"""Orquestracao do SalesAgent com Chat Completions e function calling.

O agente pode inspecionar schema, consultar SQL e registrar um insight. Ele nao
recebe ferramentas externas nem ferramentas de exportacao. O historico local
torna o fluxo compativel com diferentes provedores acessados pelo SDK OpenAI.
"""

import json
import logging
from typing import Any

from app.agent.prompts import SALES_AGENT_PROMPT
from app.llm.tools import SALES_TOOLS, ToolRegistry
from app.llm.chat_tools import (
    assistant_message_to_dict,
    to_chat_tools,
    tool_message,
)

logger = logging.getLogger(__name__)


class SalesAgent:
    """Executa o ciclo de tools de vendas sem gerar arquivos."""

    def __init__(
        self,
        *,
        client: Any,
        model: str,
        tool_registry: ToolRegistry,
    ) -> None:
        """Configura cliente, modelo e conjunto local de ferramentas.

        Args:
            client: Cliente OpenAI ou fake compativel com Chat Completions.
            model: Nome do modelo usado nas respostas.
            tool_registry: Handlers permitidos exclusivamente para vendas.
        """
        self._client = client
        self._model = model
        self._tool_registry = tool_registry

    def run(self, question: str) -> dict[str, str]:
        """Processa uma pergunta e exige um insight estruturado.

        Args:
            question: Pergunta de negocio sobre o modelo de vendas.

        Returns:
            Texto final do modelo e identificador do insight registrado.

        Raises:
            ValueError: Se a pergunta estiver vazia.
            RuntimeError: Se o agente exceder o limite de iteracoes ou
                finalizar sem chamar ``submit_sales_insight`` com sucesso.
        """
        if not question.strip():
            raise ValueError("A pergunta nao pode estar vazia.")

        messages: list[dict[str, Any]] = [
            # O system prompt vem de app.agent.prompts e define o papel do
            # agente, as tools permitidas e a política de resposta.
            {"role": "system", "content": SALES_AGENT_PROMPT},
            # A pergunta do usuário entra como mensagem separada para manter
            # o histórico fiel ao fluxo real do Chat Completions.
            {"role": "user", "content": question},
        ]
        insight_id = ""
        last_result_id = ""
        last_result: dict[str, Any] | None = None
        last_result_was_fallback = False
        response_text = ""

        # O limite impede loops indefinidos de function calling.
        for _ in range(12):
            # Enquanto o insight ainda nao foi registrado, exigimos tools;
            # depois disso o modelo pode apenas redigir a resposta final.
            message = self._create_message(
                messages=messages,
                require_tools=not insight_id,
            )
            messages.append(assistant_message_to_dict(message))
            response_text = (message.content or "").strip()
            calls = message.tool_calls or []
            if not calls:
                break

            # Cada resultado volta ao historico associado ao identificador.
            for call in calls:
                result = self._execute_tool_call(call, question)
                messages.append(tool_message(call.id, result))
                if call.function.name == "run_sql_query" and result.get("ok"):
                    last_result_id = str(result.get("result_id", ""))
                    last_result = result
                    last_result_was_fallback = bool(result.get("fallback"))
                if (
                    call.function.name == "submit_sales_insight"
                    and result.get("ok") is True
                ):
                    insight_id = str(result["insight_id"])
        else:
            raise RuntimeError("O SalesAgent excedeu o limite de chamadas.")

        if not insight_id and last_result_id:
            # Alguns provedores encerram o ciclo antes de chamar
            # submit_sales_insight; o fallback preserva o contrato da aplicacao.
            title, headline, analysis = self._build_fallback_insight(
                question=question,
                last_result=last_result,
                response_text=response_text,
            )
            fallback = self._tool_registry.invoke(
                "submit_sales_insight",
                {
                    "question": question,
                    "result_id": last_result_id,
                    "titulo": title,
                    "headline": headline,
                    "analise": analysis,
                },
            )
            if fallback.get("ok") is True:
                insight_id = str(fallback["insight_id"])
                fallback_headline = str(fallback.get("headline", "")).strip()
                if fallback_headline and (
                    last_result_was_fallback or not response_text
                ):
                    response_text = fallback_headline

        if not insight_id:
            raise RuntimeError("O SalesAgent finalizou sem registrar o insight.")
        return {
            "response_text": response_text,
            "insight_id": insight_id,
        }

    def _create_message(
        self,
        *,
        messages: list[dict[str, Any]],
        require_tools: bool = False,
    ) -> Any:
        """Solicita a proxima mensagem ao provedor configurado.

        Args:
            messages: Historico completo de usuario, assistente e tools.
            require_tools: Obriga nova chamada enquanto o insight nao existir.

        Returns:
            Mensagem da primeira alternativa retornada pelo provedor.
        """
        completion = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            # `to_chat_tools` converte os schemas internos para o formato
            # esperado pelo SDK OpenAI-compatible usado por todos os provedores.
            tools=to_chat_tools(SALES_TOOLS),
            tool_choice="required" if require_tools else "auto",
        )
        if not completion.choices:
            raise RuntimeError("O provedor nao retornou alternativas.")
        return completion.choices[0].message

    def _execute_tool_call(
        self,
        call: Any,
        question: str,
    ) -> dict[str, Any]:
        """Executa uma tool solicitada pelo modelo.

        Args:
            call: Function call retornada por Chat Completions.
            question: Pergunta original anexada ao registro do insight.

        Returns:
            Resultado serializavel que sera adicionado como mensagem ``tool``.
        """
        arguments: dict[str, Any] = {}
        name = call.function.name
        try:
            arguments = json.loads(call.function.arguments or "{}")
            # A pergunta pertence ao contexto da aplicacao, nao ao LLM.
            # Inserimos aqui porque `submit_sales_insight` deve registrar a
            # pergunta original, e não uma versão reescrita pelo modelo.
            if name == "submit_sales_insight":
                arguments["question"] = question
            result = self._tool_registry.invoke(name, arguments)
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
            result = {"ok": False, "error": str(error)}
        except Exception as error:
            if name == "run_sql_query":
                # Se o SQL do modelo vier quebrado, tentamos uma consulta de
                # tendencia segura para a pergunta mais comum de receita.
                fallback_sql = self._build_fallback_sql(question)
                if fallback_sql:
                    logger.warning(
                        "SQL do modelo falhou; tentando consulta de fallback."
                    )
                    try:
                        result = self._tool_registry.invoke(
                            name,
                            {"sql": fallback_sql},
                        )
                        if result.get("ok") is True:
                            result["fallback"] = True
                            result["original_error"] = str(error)
                            return result
                    except Exception:
                        logger.exception(
                            "Falha inesperada na consulta de fallback."
                        )
                logger.warning("Falha inesperada na tool %s", name)
                result = {"ok": False, "error": str(error)}
            else:
                logger.exception("Falha inesperada na tool %s", name)
                result = {"ok": False, "error": "Falha interna na ferramenta."}
        return result

    def _build_fallback_sql(self, question: str) -> str | None:
        """Gera uma consulta segura para perguntas de tendencia de receita."""
        # O fallback só é usado quando a pergunta fala de receita ao longo do
        # tempo; isso evita gerar SQL genérico para perguntas de outra natureza.
        normalized = question.casefold()
        trend_terms = ("ao longo do tempo", "crescendo", "caindo", "tendenc")
        revenue_terms = ("receita", "venda", "vendas", "faturamento")
        if not any(term in normalized for term in trend_terms):
            return None
        if not any(term in normalized for term in revenue_terms):
            return None
        return """
            WITH revenue_by_period AS (
                SELECT
                    d.Ano AS Ano,
                    d.MesNum AS MesNum,
                    d.Mes AS Mes,
                    SUM(fact.QtdItens * fact.ValorUnitario) AS Receita
                FROM fact
                JOIN dim_data AS d ON fact.DataEmissao = d.Data
                GROUP BY d.Ano, d.MesNum, d.Mes
            ),
            first_period AS (
                SELECT Ano, MesNum, Mes, Receita
                FROM revenue_by_period
                ORDER BY Ano, MesNum
                LIMIT 1
            ),
            last_period AS (
                SELECT Ano, MesNum, Mes, Receita
                FROM revenue_by_period
                ORDER BY Ano DESC, MesNum DESC
                LIMIT 1
            )
            SELECT
                f.Ano AS PrimeiroAno,
                f.Mes AS PrimeiroMes,
                f.Receita AS ReceitaInicial,
                l.Ano AS UltimoAno,
                l.Mes AS UltimoMes,
                l.Receita AS ReceitaFinal,
                CASE
                    WHEN l.Receita > f.Receita THEN 'crescendo'
                    WHEN l.Receita < f.Receita THEN 'caindo'
                    ELSE 'estavel'
                END AS Tendencia
            FROM first_period AS f
            CROSS JOIN last_period AS l
        """.strip()

    def _build_fallback_insight(
        self,
        *,
        question: str,
        last_result: dict[str, Any] | None,
        response_text: str,
    ) -> tuple[str, str, str]:
        """Cria um insight minimo quando o modelo nao conclui o registro."""
        if last_result:
            preview_rows = last_result.get("preview_rows") or []
            if preview_rows:
                # Quando o fallback SQL devolve uma linha agregada, usamos o
                # proprio resultado para construir um headline mais util.
                row = preview_rows[0]
                tendencia = str(row.get("Tendencia", "")).strip()
                receita_inicial = row.get("ReceitaInicial")
                receita_final = row.get("ReceitaFinal")
                if tendencia:
                    titulo = "Tendencia de receita"
                    headline = (
                        f"A receita está {tendencia} no periodo analisado."
                    )
                    if (
                        receita_inicial is not None
                        and receita_final is not None
                    ):
                        headline += (
                            f" Inicialmente foi {receita_inicial} e terminou em "
                            f"{receita_final}."
                        )
                    analise = (
                        "Fallback aplicado porque o modelo nao concluiu o "
                        "registro do insight. O sistema usou o ultimo "
                        "resultado SQL disponivel para registrar a analise."
                    )
                    return titulo, headline, analise

        titulo = "Analise de vendas"
        headline = response_text or (
            "A consulta de vendas foi executada com sucesso."
        )
        analise = (
            "Fallback aplicado porque o modelo nao concluiu o registro do "
            "insight. O sistema registrou a saida com base no ultimo "
            "resultado SQL disponivel."
        )
        return titulo, headline, analise
