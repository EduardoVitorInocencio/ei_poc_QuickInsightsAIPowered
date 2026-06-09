"""Testes do fluxo de Markdown na interface Streamlit."""

from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from streamlit_app import _generate_questions_markdown


class StreamlitMarkdownTests(unittest.TestCase):
    """Valida a integracao da UI com o fluxo de perguntas e exportacao."""

    def test_generate_questions_markdown_uses_api_service(self) -> None:
        """O Markdown da UI deve passar pelo serviço que executa a LLM."""
        sidebar_values = {
            "provider": "ollama",
            "model": "llama3.2",
            "api_key": "ollama",
            "base_url": "http://localhost:11434/v1/",
        }
        questions_file = SimpleNamespace(
            name="perguntas.xlsx",
            getvalue=lambda: b"excel-bytes",
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            markdown_path = Path(temp_dir) / "insights.md"
            markdown_path.write_text(
                "GENERATE BY AI\n\nGerado em: 07/06/2026 04:30:00\n",
                encoding="utf-8",
            )

            class FakeService:
                last_call = None

                def __init__(self, application) -> None:
                    self.application = application

                def run_questions_from_excel(self, uploaded, *, output_format):
                    FakeService.last_call = {
                        "uploaded_filename": uploaded.filename,
                        "uploaded_content": uploaded.content,
                        "output_format": output_format,
                    }
                    return {
                        "ok": True,
                        "question_count": 2,
                        "sales_insight_count": 1,
                        "answers": [],
                        "export": {"output_path": str(markdown_path)},
                    }

            with (
                patch("streamlit_app.build_ui_model_config") as build_config,
                patch("streamlit_app.build_ui_settings") as build_settings,
                patch("streamlit_app._build_application") as build_app,
                patch("streamlit_app.ApiService", FakeService),
            ):
                build_config.return_value = object()
                build_settings.return_value = object()
                build_app.return_value = object()

                result, output_path, markdown_text = _generate_questions_markdown(
                    sidebar_values,
                    questions_file,
                )

        self.assertTrue(result["ok"])
        self.assertEqual(result["export"]["output_path"], str(markdown_path))
        self.assertEqual(output_path, markdown_path)
        self.assertIn("GENERATE BY AI", markdown_text)
        self.assertIn("07/06/2026 04:30:00", markdown_text)
        self.assertEqual(FakeService.last_call["output_format"], "markdown")
        self.assertEqual(FakeService.last_call["uploaded_filename"], "perguntas.xlsx")


if __name__ == "__main__":
    unittest.main()
