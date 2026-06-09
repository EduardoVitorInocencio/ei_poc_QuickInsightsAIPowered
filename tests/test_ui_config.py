"""Testes da configuracao da interface Streamlit."""

import os
import unittest
from unittest.mock import patch

from app.ui.config import build_ui_model_config, build_ui_settings


class StreamlitConfigTests(unittest.TestCase):
    """Valida a montagem da configuracao usada pela interface."""

    def test_ollama_uses_placeholder_key_when_sidebar_is_empty(self) -> None:
        """Ollama nao precisa de chave secreta para rodar localmente."""
        with patch.dict(os.environ, {}, clear=True):
            config = build_ui_model_config("ollama")

        self.assertEqual(config.provider, "ollama")
        self.assertEqual(config.model, "llama3.2")
        self.assertEqual(config.api_key, "ollama")
        self.assertEqual(config.base_url, "http://localhost:11434/v1/")

    def test_custom_provider_requires_base_url(self) -> None:
        """A UI deve bloquear provider custom sem endpoint valido."""
        with patch.dict(os.environ, {"CUSTOM_LLM_API_KEY": "key"}, clear=True):
            with self.assertRaisesRegex(ValueError, "base URL|base url"):
                build_ui_model_config(
                    "custom",
                    model="vendor-model",
                    api_key="vendor-key",
                    base_url="",
                )

    def test_build_ui_settings_reuses_default_paths(self) -> None:
        """A interface nao deve inventar paths diferentes da aplicacao."""
        with patch.dict(os.environ, {}, clear=True):
            config = build_ui_model_config("ollama")
            settings = build_ui_settings(config)

        self.assertEqual(settings.sales_model.provider, "ollama")
        self.assertEqual(settings.external_model.provider, "ollama")
        self.assertEqual(str(settings.excel_path), "app\\data\\sales.xlsx")
        self.assertEqual(
            str(settings.markdown_output_path),
            "app\\data\\output\\insights.md",
        )


if __name__ == "__main__":
    unittest.main()
