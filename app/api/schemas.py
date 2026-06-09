"""Modelos de dados da API HTTP."""

from typing import Literal

from pydantic import BaseModel, Field

OutputFormat = Literal["none", "pptx", "markdown"]


class LoadDataResponse(BaseModel):
    """Resposta da rota de carga de dados."""

    ok: bool = True
    source: str = ""
    tables: dict[str, int] = Field(default_factory=dict)
    integrity: dict | None = None
    reason: str | None = None


class QuestionsRequest(BaseModel):
    """Entrada para perguntas manuais."""

    questions: list[str]
    output_format: OutputFormat = "none"


class QuestionsResponse(BaseModel):
    """Resposta padronizada do processamento de perguntas."""

    ok: bool = True
    question_count: int = 0
    sales_insight_count: int = 0
    answers: list[dict] = Field(default_factory=list)
    export: dict | None = None
