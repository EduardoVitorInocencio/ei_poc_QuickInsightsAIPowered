"""Testes da orquestracao modular da interface de linha de comando."""

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.cli.runner import run_cli


def input_sequence(values: list[str]):
    """Cria uma entrada interativa deterministica."""
    iterator = iter(values)
    return lambda _: next(iterator)


class CliRunnerTests(unittest.TestCase):
    """Valida decisoes da CLI sem criar infraestrutura real."""

    def test_external_session_does_not_prepare_database(self) -> None:
        """Perguntas externas devem ignorar completamente a fonte de vendas."""
        processing = Mock()
        processing.process.return_value = {
            "answers": [
                {
                    "question_number": 1,
                    "question": "Clima em Recife",
                    "agent": "external",
                    "response_text": "Tempo estavel.",
                }
            ],
            "sales_insight_count": 0,
        }
        application = SimpleNamespace(processing=processing)
        messages = []

        with patch("app.cli.runner.prepare_data_source") as prepare_mock:
            run_cli(
                application_factory=lambda: application,
                input_fn=input_sequence(["Clima em Recife", ""]),
                output_fn=messages.append,
            )

        prepare_mock.assert_not_called()
        processing.process.assert_called_once_with(["Clima em Recife"])
        self.assertTrue(any("Tempo estavel" in text for text in messages))

    def test_sales_session_can_finish_without_export(self) -> None:
        """A recusa de exportacao deve encerrar sem gerar arquivo."""
        processing = Mock()
        processing.process.return_value = {
            "answers": [
                {
                    "question_number": 1,
                    "question": "Total de vendas",
                    "agent": "sales",
                    "response_text": "Total calculado.",
                }
            ],
            "sales_insight_count": 1,
        }
        exports = Mock()
        application = SimpleNamespace(
            processing=processing,
            exports=exports,
        )
        messages = []

        with patch(
            "app.cli.runner.prepare_data_source",
            return_value={"source": "database"},
        ) as prepare_mock:
            run_cli(
                application_factory=lambda: application,
                input_fn=input_sequence(["Total de vendas", "", "nao"]),
                output_fn=messages.append,
            )

        prepare_mock.assert_called_once()
        exports.export.assert_not_called()
        self.assertIn("Output nao gerado.", messages)


if __name__ == "__main__":
    unittest.main()
