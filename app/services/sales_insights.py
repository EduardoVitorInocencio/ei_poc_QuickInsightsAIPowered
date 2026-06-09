"""Contratos e armazenamento dos insights de vendas.

O insight liga a pergunta e a narrativa ao resultado SQL original. Assim, a
analise ocorre antes e independentemente da decisao de exportar.
"""

from dataclasses import asdict, dataclass
from uuid import uuid4

from app.services.query_results import QueryResultStore


@dataclass(frozen=True)
class SalesInsight:
    """Registro imutavel de uma analise pronta para exportacao."""

    insight_id: str
    question: str
    result_id: str
    titulo: str
    headline: str
    analise: str


class SalesInsightStore:
    """Valida e mantem insights na ordem em que foram produzidos."""

    def __init__(self, result_store: QueryResultStore) -> None:
        """Inicializa o repositorio.

        Args:
            result_store: Fonte usada para validar cada ``result_id``.
        """
        self._result_store = result_store
        self._insights: list[SalesInsight] = []

    def add(
        self,
        *,
        question: str,
        result_id: str,
        titulo: str,
        headline: str,
        analise: str,
    ) -> dict:
        """Registra um insight vinculado a dados existentes.

        Args:
            question: Pergunta original do usuario.
            result_id: Referencia ao DataFrame consultado.
            titulo: Titulo curto para o artefato.
            headline: Principal conclusao sustentada pelos dados.
            analise: Explicacao executiva breve do resultado.

        Returns:
            Dicionario serializavel com status e campos do insight.

        Raises:
            ValueError: Se o resultado nao existir ou algum texto for vazio.
        """
        self._result_store.get(result_id)
        for field_name, value in {
            "titulo": titulo,
            "headline": headline,
            "analise": analise,
        }.items():
            if not value.strip():
                raise ValueError(f"O campo {field_name} nao pode estar vazio.")

        insight = SalesInsight(
            insight_id=uuid4().hex,
            question=question,
            result_id=result_id,
            titulo=titulo.strip(),
            headline=headline.strip(),
            analise=analise.strip(),
        )
        self._insights.append(insight)
        return {"ok": True, **asdict(insight)}

    def list_all(self) -> list[SalesInsight]:
        """Retorna uma nova lista com os insights do lote atual."""
        return list(self._insights)

    def clear(self) -> None:
        """Remove insights anteriores antes de processar outro lote."""
        self._insights.clear()
