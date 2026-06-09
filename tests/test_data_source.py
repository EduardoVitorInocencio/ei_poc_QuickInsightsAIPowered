"""Testes da selecao interativa da fonte de dados."""

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pandas as pd
from sqlalchemy import create_engine

from app.db.database import inspect_existing_data
from app.domain.sales_model import EXPECTED_SCHEMAS, TABLES
from app.cli.console import (
    ask_excel_path,
    ask_output_format,
    ask_yes_no,
)
from app.cli.data_source import prepare_data_source


def input_sequence(values: list[str]):
    """Cria uma funcao de entrada que devolve valores em sequencia."""
    iterator = iter(values)
    return lambda _: next(iterator)


class DatabaseStatusTests(unittest.TestCase):
    """Valida a decisao de reutilizar ou rejeitar um banco existente."""

    def test_empty_database_is_not_usable(self) -> None:
        """Um banco sem tabelas nao pode ser oferecido ao usuario."""
        engine = create_engine("sqlite:///:memory:")

        status = inspect_existing_data(engine)

        self.assertFalse(status["usable"])
        self.assertIn("Tabelas obrigatorias ausentes", status["reason"])

    def test_complete_database_with_rows_is_usable(self) -> None:
        """Um modelo completo e preenchido deve ser reutilizavel."""
        engine = create_engine("sqlite:///:memory:")
        for sheet_name, table_name in TABLES.items():
            row = {
                column: "1" for column in EXPECTED_SCHEMAS[sheet_name]
            }
            pd.DataFrame([row]).to_sql(table_name, engine, index=False)

        status = inspect_existing_data(engine)

        self.assertTrue(status["usable"])
        self.assertTrue(all(status["row_counts"].values()))


class DataSourceFlowTests(unittest.TestCase):
    """Valida repeticoes e escolhas do fluxo interativo de entrada."""

    def test_ask_yes_no_repeats_invalid_answer(self) -> None:
        """Uma resposta desconhecida deve ser rejeitada antes de aceitar sim."""
        messages = []

        result = ask_yes_no(
            "Usar? ",
            input_fn=input_sequence(["talvez", "sim"]),
            output_fn=messages.append,
        )

        self.assertTrue(result)
        self.assertEqual(len(messages), 1)

    def test_ask_output_format_accepts_markdown(self) -> None:
        """Um formato invalido deve repetir ate receber markdown."""
        messages = []

        result = ask_output_format(
            input_fn=input_sequence(["pdf", "markdown"]),
            output_fn=messages.append,
        )

        self.assertEqual(result, "markdown")
        self.assertEqual(len(messages), 1)

    def test_ask_excel_path_repeats_missing_path(self) -> None:
        """Um caminho inexistente deve ser rejeitado antes do arquivo valido."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workbook = Path(temp_dir) / "dados.xlsx"
            workbook.touch()
            messages = []

            result = ask_excel_path(
                input_fn=input_sequence(["inexistente.xlsx", str(workbook)]),
                output_fn=messages.append,
            )

            self.assertEqual(result, workbook)
            self.assertIn("Arquivo nao encontrado", messages[0])

    def test_prepare_data_source_reuses_existing_database(self) -> None:
        """A resposta sim deve evitar uma nova ingestao."""
        engine = create_engine("sqlite:///:memory:")
        for sheet_name, table_name in TABLES.items():
            row = {
                column: "1" for column in EXPECTED_SCHEMAS[sheet_name]
            }
            pd.DataFrame([row]).to_sql(table_name, engine, index=False)
        application = SimpleNamespace(engine=engine)

        result = prepare_data_source(
            application,
            input_fn=input_sequence(["s"]),
            output_fn=lambda _: None,
        )

        self.assertEqual(result["source"], "database")

    def test_prepare_data_source_loads_selected_excel(self) -> None:
        """A ausencia de banco deve encaminhar o workbook escolhido a carga."""
        engine = create_engine("sqlite:///:memory:")
        application = SimpleNamespace(engine=engine)
        with tempfile.TemporaryDirectory() as temp_dir:
            workbook = Path(temp_dir) / "dados.xlsx"
            workbook.touch()
            load_result = {"ok": True, "tables": {"fact": 1}}

            with patch(
                "app.cli.data_source.load_excel_to_sqlite",
                return_value=load_result,
            ) as load_mock:
                result = prepare_data_source(
                    application,
                    input_fn=input_sequence([str(workbook)]),
                    output_fn=lambda _: None,
                )

        self.assertEqual(result["source"], "excel")
        load_mock.assert_called_once_with(workbook, engine)


if __name__ == "__main__":
    unittest.main()
