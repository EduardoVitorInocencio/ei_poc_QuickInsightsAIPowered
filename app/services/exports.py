"""Coordenacao da exportacao opcional dos insights de vendas."""

from typing import Any

from app.services.markdown import MarkdownService
from app.services.powerpoint import PowerPointService
from app.services.sales_insights import SalesInsightStore


class InsightExportService:
    """Materializa insights somente apos a escolha do usuario."""

    def __init__(
        self,
        *,
        insight_store: SalesInsightStore,
        powerpoint: PowerPointService,
        markdown: MarkdownService,
    ) -> None:
        """Configura a fonte e os dois formatos de saida.

        Args:
            insight_store: Fonte dos insights estruturados.
            powerpoint: Implementacao da apresentacao tabular.
            markdown: Implementacao do documento Markdown.
        """
        self._insight_store = insight_store
        self._powerpoint = powerpoint
        self._markdown = markdown

    def export(self, output_format: str) -> dict[str, Any]:
        """Exporta todos os insights no formato solicitado.

        Args:
            output_format: ``pptx``, ``md`` ou ``markdown``.

        Returns:
            Metadados do arquivo criado.

        Raises:
            ValueError: Se nao houver insights ou o formato for invalido.
        """
        insights = self._insight_store.list_all()
        normalized_format = output_format.strip().lower()
        if normalized_format == "pptx":
            # A apresentacao so existe depois da confirmacao na interface.
            self._powerpoint.start_report()
            for insight in insights:
                self._powerpoint.create_table_slide(
                    result_id=insight.result_id,
                    titulo=insight.titulo,
                    headline=insight.headline,
                )
            return {
                "ok": True,
                "format": "pptx",
                "output_path": str(self._powerpoint.output_path),
                "insight_count": len(insights),
            }
        if normalized_format in {"md", "markdown"}:
            return self._markdown.create_report(insights)
        raise ValueError("Formato invalido. Use pptx ou markdown.")
