"""Testes da API HTTP."""

import io
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
from fastapi.testclient import TestClient

from app.api.app import create_api_app
from app.db.database import create_database_engine
from app.domain.sales_model import TABLES


def create_workbook(path: Path, sheets: dict[str, pd.DataFrame]) -> Path:
    """Cria um workbook temporário para os testes de upload."""
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sheet_name, dataframe in sheets.items():
            dataframe.to_excel(writer, sheet_name=sheet_name, index=False)
    return path


def required_sheet_frames() -> dict[str, pd.DataFrame]:
    """Monta um workbook mínimo e válido para o modelo estrela."""
    return {
        "fact": pd.DataFrame(
            [
                {
                    "DataEmissao": "2024-01-01",
                    "DataVencimento": "2024-01-31",
                    "NFe": "1",
                    "cdCliente": "1",
                    "cdVendedor": "1",
                    "cdProduto": "1",
                    "QtdItens": 1,
                    "ValorUnitario": 100,
                    "Peso Liquido": 2.5,
                }
            ]
        ),
        "Cliente": pd.DataFrame(
            [
                {
                    "cdCliente": "1",
                    "Razão Social": "Cliente A",
                    "Status": "Ativo",
                    "Categoria": "A",
                    "Cidade": "São Paulo",
                    "UF": "SP",
                }
            ]
        ),
        "Produto": pd.DataFrame(
            [{"cdProduto": "1", "Descrição": "Produto A", "cdGrupo": "10"}]
        ),
        "GrupoProduto": pd.DataFrame(
            [{"cdGrupo": "10", "Grupo": "Grupo A", "Linha": "Linha A"}]
        ),
        "Vendedor": pd.DataFrame(
            [
                {
                    "cdVendedor": "1",
                    "Vendedor": "Vendedor A",
                    "cdSupervisor": "2",
                    "Supervisor": "Supervisor A",
                    "cdGerente": "3",
                    "Gerente": "Gerente A",
                    "Equipe": "Equipe A",
                }
            ]
        ),
        "Data": pd.DataFrame(
            [
                {
                    "Data": "2024-01-01",
                    "Ano": 2024,
                    "Mes": "Janeiro",
                    "MesNum": 1,
                    "Dia": 1,
                },
                {
                    "Data": "2024-01-31",
                    "Ano": 2024,
                    "Mes": "Janeiro",
                    "MesNum": 1,
                    "Dia": 31,
                },
            ]
        ),
    }


def seed_database(engine, sheets: dict[str, pd.DataFrame]) -> None:
    """Cria o modelo estrela diretamente no banco para testes de bootstrap."""
    with engine.begin() as connection:
        for sheet_name, dataframe in sheets.items():
            dataframe.to_sql(
                TABLES[sheet_name],
                connection,
                if_exists="replace",
                index=False,
            )


class ApiTests(unittest.TestCase):
    """Valida os contratos HTTP sem chamar LLMs reais."""

    def setUp(self) -> None:
        """Cria app e cliente isolados por teste."""
        self.temp_dir = tempfile.TemporaryDirectory()
        database_path = Path(self.temp_dir.name) / "database.db"
        engine = create_database_engine(f"sqlite:///{database_path}")
        self.processing = SimpleNamespace(
            process=lambda questions: {
                "ok": True,
                "question_count": len(questions),
                "sales_insight_count": 1,
                "answers": [
                    {
                        "question_number": index,
                        "question": question,
                        "agent": "sales",
                        "response_text": "Total calculado.",
                    }
                    for index, question in enumerate(questions, start=1)
                ],
            }
        )
        self.exports = SimpleNamespace(
            export=lambda output_format: {
                "ok": True,
                "format": output_format,
                "output_path": "app/data/output/insights.md",
            }
        )
        application = SimpleNamespace(
            engine=engine,
            processing=self.processing,
            exports=self.exports,
        )
        self.client = TestClient(create_api_app(application))
        self.engine = engine

    def tearDown(self) -> None:
        """Limpa os artefatos temporários."""
        self.engine.dispose()
        self.temp_dir.cleanup()

    def test_docs_route_returns_swagger_ui(self) -> None:
        """A documentação do FastAPI deve estar disponível em /docs."""
        response = self.client.get("/docs")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Swagger UI", response.text)

    def test_openapi_route_returns_schema(self) -> None:
        """O schema OpenAPI deve estar disponível para Swagger e Postman."""
        response = self.client.get("/openapi.json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["info"]["title"], "Quick Insights API")

    def test_loads_data_from_uploaded_workbook(self) -> None:
        """A primeira rota deve aceitar um Excel com o modelo estrela."""
        workbook_path = create_workbook(
            Path(self.temp_dir.name) / "sales.xlsx",
            required_sheet_frames(),
        )

        with workbook_path.open("rb") as file_obj:
            response = self.client.post(
                "/data/load",
                data={"reuse_existing": "false"},
                files={
                    "excel_file": (
                        workbook_path.name,
                        file_obj,
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["source"], "excel")

    def test_runs_questions_from_json_and_exports_markdown(self) -> None:
        """A rota de perguntas deve acionar exportação sob demanda."""
        workbook_path = create_workbook(
            Path(self.temp_dir.name) / "sales.xlsx",
            required_sheet_frames(),
        )
        with workbook_path.open("rb") as file_obj:
            self.client.post(
                "/data/load",
                data={"reuse_existing": "false"},
                files={
                    "excel_file": (
                        workbook_path.name,
                        file_obj,
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                },
            )

        response = self.client.post(
            "/questions",
            json={
                "questions": ["Total de vendas"],
                "output_format": "markdown",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["sales_insight_count"], 1)
        self.assertEqual(response.json()["export"]["format"], "markdown")

    def test_runs_questions_without_manual_load_when_database_is_valid(self) -> None:
        """Um banco já pronto deve permitir perguntas sem chamar /data/load."""
        seed_database(
            self.engine,
            {
                "fact": pd.DataFrame(
                    [
                        {
                            "DataEmissao": "2024-01-01",
                            "DataVencimento": "2024-01-31",
                            "NFe": "1",
                            "cdCliente": "1",
                            "cdVendedor": "1",
                            "cdProduto": "1",
                            "QtdItens": 1,
                            "ValorUnitario": 100,
                            "PesoLiquido": 2.5,
                        }
                    ]
                ),
                "Cliente": pd.DataFrame(
                    [
                        {
                            "cdCliente": "1",
                            "RazaoSocial": "Cliente A",
                            "Status": "Ativo",
                            "Categoria": "A",
                            "Cidade": "Sao Paulo",
                            "UF": "SP",
                        }
                    ]
                ),
                "Produto": pd.DataFrame(
                    [{"cdProduto": "1", "Descricao": "Produto A", "cdGrupo": "10"}]
                ),
                "GrupoProduto": pd.DataFrame(
                    [{"cdGrupo": "10", "Grupo": "Grupo A", "Linha": "Linha A"}]
                ),
                "Vendedor": pd.DataFrame(
                    [
                        {
                            "cdVendedor": "1",
                            "Vendedor": "Vendedor A",
                            "cdSupervisor": "2",
                            "Supervisor": "Supervisor A",
                            "cdGerente": "3",
                            "Gerente": "Gerente A",
                            "Equipe": "Equipe A",
                        }
                    ]
                ),
                "Data": pd.DataFrame(
                    [
                        {
                            "Data": "2024-01-01",
                            "Ano": 2024,
                            "Mes": "Janeiro",
                            "MesNum": 1,
                            "Dia": 1,
                        },
                        {
                            "Data": "2024-01-31",
                            "Ano": 2024,
                            "Mes": "Janeiro",
                            "MesNum": 1,
                            "Dia": 31,
                        },
                    ]
                ),
            },
        )

        response = self.client.post(
            "/questions",
            json={
                "questions": ["A receita está crescendo ou caindo ao longo do tempo?"],
                "output_format": "markdown",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["question_count"], 1)
        self.assertEqual(response.json()["export"]["format"], "markdown")

    def test_runs_questions_from_excel_file(self) -> None:
        """A rota de upload deve extrair perguntas de uma planilha."""
        workbook_path = create_workbook(
            Path(self.temp_dir.name) / "sales.xlsx",
            required_sheet_frames(),
        )
        with workbook_path.open("rb") as file_obj:
            self.client.post(
                "/data/load",
                data={"reuse_existing": "false"},
                files={
                    "excel_file": (
                        workbook_path.name,
                        file_obj,
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                },
            )

        questions_path = create_workbook(
            Path(self.temp_dir.name) / "questions.xlsx",
            {
                "Perguntas": pd.DataFrame(
                    {
                        "Pergunta": [
                            "Total de vendas",
                            "Clima em Sao Paulo",
                        ]
                    }
                )
            },
        )

        with questions_path.open("rb") as file_obj:
            response = self.client.post(
                "/questions/excel",
                data={"output_format": "none"},
                files={
                    "questions_file": (
                        questions_path.name,
                        file_obj,
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["question_count"], 2)
        self.assertEqual(
            [answer["question"] for answer in response.json()["answers"]],
            ["Total de vendas", "Clima em Sao Paulo"],
        )


if __name__ == "__main__":
    unittest.main()
