"""Configuracao imutavel baseada em variaveis de ambiente."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from app.llm.providers import ModelConfig


@dataclass(frozen=True)
class Settings:
    """Valores necessarios para compor infraestrutura e agentes."""

    sales_model: ModelConfig
    external_model: ModelConfig
    excel_path: Path
    database_url: str
    pptx_output_path: Path
    markdown_output_path: Path

    @classmethod
    def from_env(cls) -> "Settings":
        """Carrega o arquivo ``.env`` e aplica valores padrao.

        Returns:
            Instancia imutavel pronta para o ``bootstrap``.
        """
        load_dotenv()
        return cls(
            sales_model=ModelConfig.from_env("SALES"),
            external_model=ModelConfig.from_env("EXTERNAL"),
            excel_path=Path(
                os.getenv("EXCEL_PATH", "app/data/sales.xlsx")
            ),
            database_url=os.getenv(
                "DB_PATH",
                "sqlite:///app/data/database.db",
            ),
            pptx_output_path=Path(
                os.getenv(
                    "PPTX_OUTPUT_PATH",
                    "app/data/output/insight_slide.pptx",
                )
            ),
            markdown_output_path=Path(
                os.getenv(
                    "MARKDOWN_OUTPUT_PATH",
                    "app/data/output/insights.md",
                )
            ),
        )
