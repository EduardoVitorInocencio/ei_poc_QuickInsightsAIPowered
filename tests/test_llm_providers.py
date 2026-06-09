"""Testes da configuracao multi-provedor sem chamadas HTTP."""

import os
import unittest
from unittest.mock import patch

from app.llm.tools import WEATHER_TOOL
from app.llm.chat_tools import to_chat_tools
from app.llm.providers import ModelConfig


class ModelConfigTests(unittest.TestCase):
    """Valida defaults, overrides e requisitos de cada provedor."""

    def test_uses_ollama_as_default_provider_when_env_is_empty(self) -> None:
        """Sem variaveis de provedor, a configuracao padrao deve ser Ollama."""
        with patch.dict(os.environ, {}, clear=True):
            config = ModelConfig.from_env("SALES")

        self.assertEqual(config.provider, "ollama")
        self.assertEqual(config.model, "llama3.2")
        self.assertEqual(config.api_key, "ollama")
        self.assertEqual(config.base_url, "http://localhost:11434/v1/")

    def test_openai_accepts_legacy_model_variable(self) -> None:
        """Mantem compatibilidade com o arquivo ``.env`` anterior."""
        environment = {
            "LLM_PROVIDER": "openai",
            "OPENAI_API_KEY": "openai-key",
            "OPENAI_MODEL": "gpt-custom",
        }
        with patch.dict(os.environ, environment, clear=True):
            config = ModelConfig.from_env("SALES")

        self.assertEqual(config.provider, "openai")
        self.assertEqual(config.model, "gpt-custom")
        self.assertIsNone(config.base_url)

    def test_agent_specific_values_override_global_values(self) -> None:
        """Permite que cada agente use provedor e modelo independentes."""
        environment = {
            "LLM_PROVIDER": "openai",
            "LLM_MODEL": "global-model",
            "LLM_API_KEY": "global-key",
            "SALES_LLM_PROVIDER": "gemini",
            "SALES_LLM_MODEL": "gemini-special",
            "SALES_LLM_API_KEY": "sales-key",
        }
        with patch.dict(os.environ, environment, clear=True):
            config = ModelConfig.from_env("SALES")

        self.assertEqual(config.provider, "gemini")
        self.assertEqual(config.model, "gemini-special")
        self.assertEqual(config.api_key, "sales-key")
        self.assertIn("generativelanguage.googleapis.com", config.base_url)

    def test_ollama_uses_local_endpoint_and_placeholder_key(self) -> None:
        """Ollama local nao exige uma credencial secreta."""
        with patch.dict(
            os.environ,
            {"EXTERNAL_LLM_PROVIDER": "ollama"},
            clear=True,
        ):
            config = ModelConfig.from_env("EXTERNAL")

        self.assertEqual(config.api_key, "ollama")
        self.assertEqual(config.model, "llama3.2")
        self.assertEqual(config.base_url, "http://localhost:11434/v1/")

    def test_deepseek_uses_provider_key(self) -> None:
        """Resolve a chave padrao e o endpoint oficial do DeepSeek."""
        environment = {
            "LLM_PROVIDER": "deepseek",
            "DEEPSEEK_API_KEY": "deepseek-key",
        }
        with patch.dict(os.environ, environment, clear=True):
            config = ModelConfig.from_env("SALES")

        self.assertEqual(config.api_key, "deepseek-key")
        self.assertEqual(config.base_url, "https://api.deepseek.com")

    def test_custom_provider_requires_base_url(self) -> None:
        """Evita criar um provedor custom sem endpoint definido."""
        environment = {
            "LLM_PROVIDER": "custom",
            "LLM_MODEL": "vendor-model",
            "LLM_API_KEY": "vendor-key",
        }
        with patch.dict(os.environ, environment, clear=True):
            with self.assertRaisesRegex(ValueError, "base URL|BASE_URL"):
                ModelConfig.from_env("SALES")

    def test_custom_provider_accepts_openai_compatible_endpoint(self) -> None:
        """Habilita novos provedores sem alterar os agentes."""
        environment = {
            "LLM_PROVIDER": "custom",
            "LLM_MODEL": "vendor-model",
            "LLM_API_KEY": "vendor-key",
            "LLM_BASE_URL": "https://vendor.example/v1",
        }
        with patch.dict(os.environ, environment, clear=True):
            config = ModelConfig.from_env("SALES")

        self.assertEqual(config.provider, "custom")
        self.assertEqual(config.model, "vendor-model")
        self.assertEqual(config.base_url, "https://vendor.example/v1")

    def test_chat_tool_conversion_omits_strict_mode(self) -> None:
        """Gera o formato comum aceito pelos endpoints compativeis."""
        converted = to_chat_tools([WEATHER_TOOL])

        function = converted[0]["function"]
        self.assertEqual(function["name"], "get_current_weather")
        self.assertNotIn("strict", function)
        self.assertEqual(
            function["parameters"]["required"],
            ["city"],
        )


if __name__ == "__main__":
    unittest.main()
