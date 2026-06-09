"""Helpers puros para montar a configuracao da interface Streamlit."""

from __future__ import annotations

import os
from pathlib import Path

from app.config import Settings
from app.llm.providers import ModelConfig, PROVIDER_DEFAULTS, SUPPORTED_PROVIDERS

UI_PROVIDER_OPTIONS = (
    "ollama",
    "groq",
    "openai",
    "gemini",
    "deepseek",
    "custom",
)


def _normalize_provider(provider: str) -> str:
    normalized = provider.strip().lower()
    if normalized not in SUPPORTED_PROVIDERS:
        supported = ", ".join(sorted(SUPPORTED_PROVIDERS))
        raise ValueError(
            f"Provedor LLM desconhecido: {normalized}. Use um de: {supported}."
        )
    return normalized


def _resolve_text(value: str | None, default: str | None = None) -> str | None:
    text = (value or "").strip()
    if text:
        return text
    return default


def build_ui_model_config(
    provider: str,
    *,
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
) -> ModelConfig:
    """Monta um ``ModelConfig`` a partir dos campos escolhidos no sidebar."""
    normalized_provider = _normalize_provider(provider)
    defaults = PROVIDER_DEFAULTS[normalized_provider]
    resolved_model = _resolve_text(model, defaults["model"]) or ""
    resolved_base_url = _resolve_text(base_url, defaults["base_url"])
    resolved_api_key = _resolve_text(
        api_key,
        os.getenv(defaults["api_key_env"]) or defaults.get("api_key_fallback"),
    )

    if not resolved_api_key:
        raise ValueError(
            f"Informe a chave de API para {normalized_provider}. "
            f"O campo pode usar {defaults['api_key_env']} do ambiente."
        )
    if normalized_provider == "custom" and not resolved_base_url:
        raise ValueError("O provedor custom exige uma base URL valida.")
    if not resolved_model:
        raise ValueError(f"Informe um modelo valido para {normalized_provider}.")

    return ModelConfig(
        provider=normalized_provider,
        model=resolved_model,
        api_key=resolved_api_key,
        base_url=resolved_base_url,
    )


def build_ui_settings(model_config: ModelConfig) -> Settings:
    """Reaproveita os mesmos paths de dados e exportacao da aplicacao."""
    return Settings(
        sales_model=model_config,
        external_model=model_config,
        excel_path=Path(os.getenv("EXCEL_PATH", "app/data/sales.xlsx")),
        database_url=os.getenv("DB_PATH", "sqlite:///app/data/database.db"),
        pptx_output_path=Path(
            os.getenv("PPTX_OUTPUT_PATH", "app/data/output/insight_slide.pptx")
        ),
        markdown_output_path=Path(
            os.getenv("MARKDOWN_OUTPUT_PATH", "app/data/output/insights.md")
        ),
    )

