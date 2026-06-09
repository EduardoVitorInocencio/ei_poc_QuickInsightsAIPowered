"""Orquestracao do agente dedicado a ferramentas externas.

Este agente nao conhece banco, insights exportaveis ou geradores de arquivo.
Seu unico produto e uma resposta textual fundamentada na tool executada.
"""

import json
import logging
from typing import Any

from app.agent.prompts import EXTERNAL_TOOLS_AGENT_PROMPT
from app.llm.tools import EXTERNAL_TOOLS, ToolRegistry
from app.llm.chat_tools import (
    assistant_message_to_dict,
    to_chat_tools,
    tool_message,
)

logger = logging.getLogger(__name__)


class ExternalToolsAgent:
    """Executa tools externas e retorna somente texto."""

    def __init__(
        self,
        *,
        client: Any,
        model: str,
        tool_registry: ToolRegistry,
    ) -> None:
        """Configura as dependencias isoladas do agente externo.

        Args:
            client: Cliente OpenAI ou fake compativel com Chat Completions.
            model: Nome do modelo.
            tool_registry: Registro contendo somente ferramentas externas.
        """
        self._client = client
        self._model = model
        self._tool_registry = tool_registry

    def run(self, question: str) -> dict[str, str]:
        """Executa pelo menos uma tool externa e sintetiza a resposta.

        Args:
            question: Pergunta que requer uma fonte externa.

        Returns:
            Dicionario contendo apenas ``response_text``.

        Raises:
            ValueError: Se a pergunta estiver vazia.
            RuntimeError: Se nenhuma tool concluir ou o limite for excedido.
        """
        if not question.strip():
            raise ValueError("A pergunta nao pode estar vazia.")

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": EXTERNAL_TOOLS_AGENT_PROMPT},
            {"role": "user", "content": question},
        ]
        tool_succeeded = False
        response_text = ""

        # Menos iteracoes sao suficientes porque nao ha cadeia SQL/exportacao.
        for _ in range(8):
            message = self._create_message(
                messages=messages,
                require_tools=not tool_succeeded,
            )
            messages.append(assistant_message_to_dict(message))
            response_text = (message.content or "").strip()
            calls = message.tool_calls or []
            if not calls:
                break

            for call in calls:
                result = self._execute_tool_call(call)
                messages.append(tool_message(call.id, result))
                tool_succeeded = tool_succeeded or result.get("ok") is True
        else:
            raise RuntimeError(
                "O ExternalToolsAgent excedeu o limite de chamadas."
            )

        if not tool_succeeded:
            raise RuntimeError(
                "O ExternalToolsAgent finalizou sem executar uma ferramenta."
            )
        return {"response_text": response_text}

    def _create_message(
        self,
        *,
        messages: list[dict[str, Any]],
        require_tools: bool = False,
    ) -> Any:
        """Solicita uma mensagem expondo somente ``EXTERNAL_TOOLS``."""
        completion = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            tools=to_chat_tools(EXTERNAL_TOOLS),
            tool_choice="required" if require_tools else "auto",
        )
        if not completion.choices:
            raise RuntimeError("O provedor nao retornou alternativas.")
        return completion.choices[0].message

    def _execute_tool_call(self, call: Any) -> dict[str, Any]:
        """Executa uma tool externa e retorna seu resultado serializavel."""
        name = call.function.name
        try:
            arguments = json.loads(call.function.arguments or "{}")
            result = self._tool_registry.invoke(name, arguments)
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
            result = {"ok": False, "error": str(error)}
        except Exception:
            logger.exception("Falha inesperada na tool externa %s", name)
            result = {"ok": False, "error": "Falha interna na ferramenta."}
        return result
