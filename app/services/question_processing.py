"""Roteamento de perguntas entre agentes especializados.

O roteamento deterministico preserva o principio do menor privilegio: o
SalesAgent nao recebe internet e o ExternalToolsAgent nao recebe banco.
"""

from typing import Any

from app.agent.external_tools_agent import ExternalToolsAgent
from app.agent.sales_agent import SalesAgent
from app.services.query_results import QueryResultStore
from app.services.sales_insights import SalesInsightStore

WEATHER_TERMS = (
    "clima",
    "tempo em",
    "temperatura",
    "meteorolog",
    "previsao do tempo",
    "previsão do tempo",
    "chuva em",
)


def classify_question(question: str) -> str:
    """Escolhe o agente a partir de termos meteorologicos.

    Args:
        question: Pergunta original do usuario.

    Returns:
        ``external`` para meteorologia ou ``sales`` para dados do SQLite.
    """
    normalized = question.casefold()
    if any(term in normalized for term in WEATHER_TERMS):
        return "external"
    return "sales"


class QuestionProcessingService:
    """Executa perguntas sem criar arquivos automaticamente."""

    def __init__(
        self,
        *,
        sales_agent: SalesAgent,
        external_agent: ExternalToolsAgent,
        result_store: QueryResultStore,
        insight_store: SalesInsightStore,
    ) -> None:
        """Recebe agentes e repositorios compartilhados.

        Args:
            sales_agent: Agente restrito ao modelo de vendas.
            external_agent: Agente restrito a ferramentas externas.
            result_store: Resultados SQL preservados para eventual exportacao.
            insight_store: Insights de vendas produzidos no lote.
        """
        self._sales_agent = sales_agent
        self._external_agent = external_agent
        self._result_store = result_store
        self._insight_store = insight_store

    def process(self, questions: list[str]) -> dict[str, Any]:
        """Roteia um lote e agrega respostas na ordem de entrada.

        Args:
            questions: Perguntas de vendas e/ou ferramentas externas.

        Returns:
            Respostas com identificacao do agente e quantidade de insights de
            vendas que podem ser exportados.

        Raises:
            ValueError: Se nenhuma pergunta valida for informada.
        """
        normalized = [
            question.strip() for question in questions if question.strip()
        ]
        if not normalized:
            raise ValueError("Informe pelo menos uma pergunta.")

        # Um novo lote nao pode reutilizar referencias ou insights anteriores.
        self._result_store.clear()
        self._insight_store.clear()
        answers = []
        for position, question in enumerate(normalized, start=1):
            # A classificacao determina tambem quais ferramentas ficam visiveis.
            agent_name = classify_question(question)
            if agent_name == "external":
                result = self._external_agent.run(question)
            else:
                result = self._sales_agent.run(question)
            answers.append(
                {
                    "question_number": position,
                    "question": question,
                    "agent": agent_name,
                    "response_text": result["response_text"],
                }
            )

        return {
            "ok": True,
            "question_count": len(normalized),
            "sales_insight_count": len(self._insight_store.list_all()),
            "answers": answers,
        }
