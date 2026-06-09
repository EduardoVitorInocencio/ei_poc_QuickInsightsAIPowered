"""Catalogo e configuracao de provedores OpenAI-compatible.

Todos os provedores sao acessados pelo pacote ``openai``. A diferenca fica
restrita a ``base_url``, chave e nome do modelo, evitando acoplamento dos
agentes a SDKs especificos.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from openai import OpenAI

SUPPORTED_PROVIDERS = frozenset({"openai", "groq", "gemini", "deepseek", "custom", "ollama"})

PROVIDER_DEFAULTS = {
    "openai": {
        "base_url": None,
        "api_key_env": "OPENAI_API_KEY",
        "model": "gpt-5.4-nano",
    },
    "ollama": {
        "base_url": "http://localhost:11434/v1/",
        "api_key_env": "OLLAMA_API_KEY",
        "api_key_fallback": "ollama",
        "model": "llama3.2",
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "api_key_env": "GEMINI_API_KEY",
        "model": "gemini-3.5-flash",
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com",
        "api_key_env": "DEEPSEEK_API_KEY",
        "model": "deepseek-v4-flash",
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "api_key_env": "GROQ_API_KEY",
        "model": "qwen/qwen3-32b",
    },
    "custom": {
        "base_url": None,
        "api_key_env": "CUSTOM_LLM_API_KEY",
        "model": "",
    },
}


@dataclass(frozen=True)
class ModelConfig:
    """Configuracao completa de um modelo usado por um agente."""

    provider: str
    model: str
    api_key: str
    base_url: str | None

    @classmethod
    def from_env(
        cls,
        prefix: str,
        *,
        default_provider: str = "ollama",
    ) -> "ModelConfig":
        """Carrega um modelo com suporte a override por ambiente.

        Variaveis especificas como ``SALES_LLM_PROVIDER`` prevalecem sobre
        ``LLM_PROVIDER``. O mesmo vale para modelo, chave e base URL.
        """
        normalized_prefix = prefix.strip().upper()
        provider = (
            os.getenv(f"{normalized_prefix}_LLM_PROVIDER")
            or os.getenv("LLM_PROVIDER")
            or default_provider
        ).strip().lower()
        if provider not in SUPPORTED_PROVIDERS:
            supported = ", ".join(sorted(SUPPORTED_PROVIDERS))
            raise ValueError(
                f"Provedor LLM desconhecido: {provider}. "
                f"Use um de: {supported}."
            )

        defaults = PROVIDER_DEFAULTS[provider]
        model = (
            os.getenv(f"{normalized_prefix}_LLM_MODEL")
            or os.getenv("LLM_MODEL")
            or (
                os.getenv("OPENAI_MODEL")
                if provider == "openai"
                else None
            )
            or defaults["model"]
        ).strip()
        base_url = (
            os.getenv(f"{normalized_prefix}_LLM_BASE_URL")
            or os.getenv("LLM_BASE_URL")
            or defaults["base_url"]
        )
        api_key = (
            os.getenv(f"{normalized_prefix}_LLM_API_KEY")
            or os.getenv("LLM_API_KEY")
            or os.getenv(defaults["api_key_env"])
            or defaults.get("api_key_fallback")
        )
        if not api_key:
            raise ValueError(
                f"Chave ausente para {provider}. Configure "
                f"{normalized_prefix}_LLM_API_KEY, LLM_API_KEY ou "
                f"{defaults['api_key_env']}."
            )
        if not model:
            raise ValueError(
                f"Modelo ausente para {provider}. Configure "
                f"{normalized_prefix}_LLM_MODEL ou LLM_MODEL."
            )
        if provider == "custom" and not base_url:
            raise ValueError(
                "O provedor custom exige uma variavel LLM_BASE_URL "
                "global ou especifica do agente."
            )

        return cls(
            provider=provider,
            model=model,
            api_key=api_key,
            base_url=base_url,
        )


def create_openai_client(config: ModelConfig) -> OpenAI:
    """Cria um cliente OpenAI apontando para o provedor configurado."""
    kwargs = {"api_key": config.api_key}
    if config.base_url:
        kwargs["base_url"] = config.base_url
    return OpenAI(**kwargs)
