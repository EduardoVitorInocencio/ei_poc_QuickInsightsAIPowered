"""Testes dos agentes especializados sem acesso a rede."""

import json
import unittest
from types import SimpleNamespace

from app.agent.external_tools_agent import ExternalToolsAgent
from app.agent.sales_agent import SalesAgent
from app.llm.tools import ToolRegistry


def tool_completion(call_id, name, arguments):
    """Monta uma completion simulada contendo uma unica function call."""
    call = SimpleNamespace(
        id=call_id,
        function=SimpleNamespace(
            name=name,
            arguments=json.dumps(arguments),
        ),
    )
    message = SimpleNamespace(content=None, tool_calls=[call])
    return SimpleNamespace(
        choices=[SimpleNamespace(message=message)],
    )


def text_completion(text):
    """Monta uma completion final sem novas chamadas de ferramenta."""
    message = SimpleNamespace(content=text, tool_calls=None)
    return SimpleNamespace(
        choices=[SimpleNamespace(message=message)],
    )


class FakeSalesCompletions:
    """Simula a sequencia SQL, registro de insight e resposta final."""

    def __init__(self) -> None:
        """Inicializa o historico de chamadas recebidas."""
        self.calls = []

    def create(self, **kwargs):
        """Retorna a proxima etapa deterministica do SalesAgent."""
        self.calls.append(kwargs)
        if len(self.calls) == 1:
            return tool_completion(
                "call-1",
                "run_sql_query",
                {"sql": "SELECT 'Total' AS Indicador, 10 AS Valor FROM fact"},
            )
        if len(self.calls) == 2:
            return tool_completion(
                "call-2",
                "submit_sales_insight",
                {
                    "result_id": "result-1",
                    "titulo": "Total de vendas",
                    "headline": "As vendas totalizaram 10.",
                    "analise": "O valor consolidado do periodo foi 10.",
                },
            )
        return text_completion("As vendas totalizaram 10.")


class FakeSalesCompletionsWithoutSubmit:
    """Simula um provedor que executa SQL mas nao fecha o insight."""

    def __init__(self) -> None:
        """Inicializa o historico de chamadas recebidas."""
        self.calls = []

    def create(self, **kwargs):
        """Retorna SQL na primeira chamada e texto na segunda."""
        self.calls.append(kwargs)
        if len(self.calls) == 1:
            return tool_completion(
                "call-1",
                "run_sql_query",
                {"sql": "SELECT 'Total' AS Indicador, 10 AS Valor FROM fact"},
            )
        return text_completion("As vendas totalizaram 10.")


class FakeSalesCompletionsWithBadSql:
    """Simula SQL invalido na primeira tentativa e texto final depois."""

    def __init__(self) -> None:
        """Inicializa o historico de chamadas recebidas."""
        self.calls = []

    def create(self, **kwargs):
        """Retorna SQL quebrado na primeira chamada e texto na segunda."""
        self.calls.append(kwargs)
        if len(self.calls) == 1:
            return tool_completion(
                "call-1",
                "run_sql_query",
                {
                    "sql": (
                        "SELECT SUM(fact.QtdItens * fact.ValorUnitario) "
                        "AS Vendas OVER (dim_data), dim_data, "
                        "dim_grupo_produto FROM fact GROUP BY "
                        "dim_grupo_produto AND dim_data"
                    )
                },
            )
        return text_completion("A receita está em análise.")


class FakeExternalCompletions:
    """Simula uma consulta meteorologica seguida da resposta textual."""

    def __init__(self) -> None:
        """Inicializa o historico de chamadas recebidas."""
        self.calls = []

    def create(self, **kwargs):
        """Retorna uma tool externa na primeira chamada e texto na segunda."""
        self.calls.append(kwargs)
        if len(self.calls) == 1:
            return tool_completion(
                "weather-1",
                "get_current_weather",
                {"city": "Sao Paulo", "country_code": "BR"},
            )
        return text_completion("Sao Paulo registra 21 graus.")


def fake_client(completions):
    """Cria a hierarquia ``client.chat.completions`` usada pelos agentes."""
    return SimpleNamespace(
        chat=SimpleNamespace(completions=completions),
    )


class AgentTests(unittest.TestCase):
    """Protege isolamento de ferramentas e contratos dos agentes."""

    def test_sales_agent_registers_insight_without_output_tool(self) -> None:
        """Confirma que vendas registram insight sem exportar ou acessar clima."""
        completions = FakeSalesCompletions()
        registry = ToolRegistry(
            {
                "run_sql_query": lambda _: {
                    "ok": True,
                    "result_id": "result-1",
                    "columns": ["Indicador", "Valor"],
                },
                "submit_sales_insight": lambda args: {
                    "ok": True,
                    "insight_id": "insight-1",
                    "question": args["question"],
                },
            }
        )
        agent = SalesAgent(
            client=fake_client(completions),
            model="test-model",
            tool_registry=registry,
        )

        result = agent.run("Qual o total de vendas?")

        self.assertEqual(result["insight_id"], "insight-1")
        self.assertEqual(len(completions.calls), 3)
        tool_names = {
            tool["function"]["name"]
            for tool in completions.calls[0]["tools"]
        }
        self.assertNotIn("create_powerpoint_slide", tool_names)
        self.assertNotIn("get_current_weather", tool_names)
        self.assertEqual(completions.calls[0]["model"], "test-model")
        self.assertEqual(completions.calls[0]["tool_choice"], "required")
        self.assertEqual(completions.calls[-1]["tool_choice"], "auto")

    def test_sales_agent_falls_back_when_model_omits_submit_insight(self) -> None:
        """O agente deve finalizar mesmo se o provedor nao chamar submit."""
        completions = FakeSalesCompletionsWithoutSubmit()
        registry = ToolRegistry(
            {
                "run_sql_query": lambda _: {
                    "ok": True,
                    "result_id": "result-1",
                    "columns": ["Indicador", "Valor"],
                },
                "submit_sales_insight": lambda args: {
                    "ok": True,
                    "insight_id": "insight-1",
                    "question": args["question"],
                },
            }
        )
        agent = SalesAgent(
            client=fake_client(completions),
            model="test-model",
            tool_registry=registry,
        )

        result = agent.run("Qual o total de vendas?")

        self.assertEqual(result["insight_id"], "insight-1")
        self.assertEqual(result["response_text"], "As vendas totalizaram 10.")
        self.assertEqual(len(completions.calls), 2)

    def test_sales_agent_recovers_from_invalid_sql(self) -> None:
        """O agente deve tentar uma consulta de fallback ao falhar no SQL."""
        completions = FakeSalesCompletionsWithBadSql()
        sql_calls = []

        def run_sql(args):
            sql_calls.append(args["sql"])
            if "WITH revenue_by_period" in args["sql"]:
                return {
                    "ok": True,
                    "result_id": "result-1",
                    "columns": [
                        "PrimeiroAno",
                        "PrimeiroMes",
                        "ReceitaInicial",
                        "UltimoAno",
                        "UltimoMes",
                        "ReceitaFinal",
                        "Tendencia",
                    ],
                    "preview_rows": [
                        {
                            "PrimeiroAno": 2024,
                            "PrimeiroMes": "Janeiro",
                            "ReceitaInicial": 100.0,
                            "UltimoAno": 2024,
                            "UltimoMes": "Dezembro",
                            "ReceitaFinal": 180.0,
                            "Tendencia": "crescendo",
                        }
                    ],
                }
            raise RuntimeError("SQL invalido")

        registry = ToolRegistry(
            {
                "run_sql_query": run_sql,
                "submit_sales_insight": lambda args: {
                    "ok": True,
                    "insight_id": "insight-1",
                    "question": args["question"],
                    "titulo": args["titulo"],
                    "headline": args["headline"],
                    "analise": args["analise"],
                },
            }
        )
        agent = SalesAgent(
            client=fake_client(completions),
            model="test-model",
            tool_registry=registry,
        )

        result = agent.run("A receita está crescendo ou caindo ao longo do tempo?")

        self.assertEqual(result["insight_id"], "insight-1")
        self.assertIn("crescendo", result["response_text"])
        self.assertEqual(len(sql_calls), 2)
        self.assertIn("WITH revenue_by_period", sql_calls[-1])

    def test_external_agent_only_uses_external_tools(self) -> None:
        """Confirma que o agente externo enxerga somente meteorologia."""
        completions = FakeExternalCompletions()
        agent = ExternalToolsAgent(
            client=fake_client(completions),
            model="test-model",
            tool_registry=ToolRegistry(
                {
                    "get_current_weather": lambda _: {
                        "ok": True,
                        "current": {"TemperaturaC": 21},
                    }
                }
            ),
        )

        result = agent.run("Como esta o clima em Sao Paulo?")

        self.assertIn("21", result["response_text"])
        tool_names = {
            tool["function"]["name"]
            for tool in completions.calls[0]["tools"]
        }
        self.assertEqual(tool_names, {"get_current_weather"})


if __name__ == "__main__":
    unittest.main()
