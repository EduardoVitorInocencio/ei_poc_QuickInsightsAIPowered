"""Exportacao textual dos insights de vendas.

O documento preserva pergunta, narrativa, analise e dados em um formato
portavel, legivel e adequado para versionamento.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from app.services.query_results import QueryResultStore
from app.services.sales_insights import SalesInsight


class MarkdownService:
    """Gera um unico documento Markdown para o lote de insights."""

    def __init__(
        self,
        output_path: str | Path,
        result_store: QueryResultStore,
        max_rows: int = 15,
    ) -> None:
        """Configura caminho, fonte dos dados e limite visual.

        Args:
            output_path: Arquivo Markdown que sera criado.
            result_store: Repositorio dos DataFrames referenciados.
            max_rows: Quantidade maxima de linhas por tabela.
        """
        self._base_output_path = Path(output_path)
        self._output_path = self._base_output_path
        self._result_store = result_store
        self._max_rows = max_rows

    @property
    def output_path(self) -> Path:
        """Retorna o caminho configurado sem criar o arquivo."""
        return self._output_path

    def create_report(self, insights: list[SalesInsight]) -> dict[str, Any]:
        """Cria o documento com uma secao por insight.

        Args:
            insights: Insights ordenados que devem compor o documento.

        Returns:
            Status, formato, caminho e quantidade de insights exportados.

        Raises:
            ValueError: Se a lista estiver vazia ou um ``result_id`` expirar.
        """
        if not insights:
            raise ValueError("Nao existem insights de vendas para exportar.")

        # O timestamp entra no nome e no corpo para facilitar rastreio do
        # artefato gerado em execuções repetidas.
        generated_at = datetime.now()
        output_path = self._timestamped_output_path(generated_at)
        sections = [
            "# Relatorio de Insights de Vendas",
            "",
            "GENERATE BY AI",
            "",
            f"Gerado em: {generated_at:%d/%m/%Y %H:%M:%S}",
            "",
        ]
        for index, insight in enumerate(insights, start=1):
            # Cada insight mantém o `result_id` que aponta para o DataFrame
            # salvo no QueryResultStore; daqui sai a tabela que será escrita.
            dataframe = self._result_store.get(insight.result_id).head(
                self._max_rows
            )
            sections.extend(
                [
                    f"## {index}. {insight.titulo}",
                    "",
                    f"**Pergunta:** {insight.question}",
                    "",
                    f"**Headline:** {insight.headline}",
                    "",
                    "### Analise",
                    "",
                    insight.analise,
                    "",
                    "### Dados",
                    "",
                    self._dataframe_to_markdown(dataframe),
                    "",
                ]
            )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            "\n".join(sections),
            encoding="utf-8",
        )
        return {
            "ok": True,
            "format": "markdown",
            "output_path": str(output_path),
            "insight_count": len(insights),
        }

    @staticmethod
    def _dataframe_to_markdown(dataframe: pd.DataFrame) -> str:
        """Converte um DataFrame em tabela Markdown sem dependencia extra."""
        # A formatação manual evita dependência de renderizadores externos e
        # mantém o output determinístico para testes e versionamento.
        columns = [str(column) for column in dataframe.columns]
        header = "| " + " | ".join(columns) + " |"
        separator = "| " + " | ".join("---" for _ in columns) + " |"
        rows = []
        for row in dataframe.itertuples(index=False, name=None):
            values = [
                MarkdownService._escape_value(value) for value in row
            ]
            rows.append("| " + " | ".join(values) + " |")
        return "\n".join([header, separator, *rows])

    @staticmethod
    def _escape_value(value: Any) -> str:
        """Formata um valor e escapa caracteres que quebrariam a tabela."""
        if pd.isna(value):
            return ""
        if isinstance(value, float):
            text = f"{value:,.2f}"
        else:
            text = str(value)
        # Pipes e quebras de linha quebrariam o formato de tabela Markdown.
        return text.replace("|", "\\|").replace("\n", " ")

    def _timestamped_output_path(self, generated_at: datetime) -> Path:
        """Cria um nome de arquivo com data e hora para cada exportacao."""
        suffix = self._base_output_path.suffix or ".md"
        stem = self._base_output_path.stem
        timestamp = generated_at.strftime("%Y%m%d_%H%M%S")
        # Sempre partimos do caminho base configurado, sem empilhar timestamps
        # entre exportacoes consecutivas.
        self._output_path = self._base_output_path.with_name(
            f"{stem}_{timestamp}{suffix}"
        )
        return self._output_path
