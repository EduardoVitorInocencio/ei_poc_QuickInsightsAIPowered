"""Utilitarios para function calling via Chat Completions."""

import json
from typing import Any


def to_chat_tools(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Converte schemas internos para o formato de Chat Completions.

    Args:
        tools: Tools no formato simples usado anteriormente pela Responses API.

    Returns:
        Tools com os campos da funcao aninhados em ``function``.
    """
    converted = []
    for tool in tools:
        function = {
            key: value
            for key, value in tool.items()
            # Nem todos os endpoints compativeis implementam strict mode.
            if key not in {"type", "strict"}
        }
        converted.append({"type": "function", "function": function})
    return converted


def assistant_message_to_dict(message: Any) -> dict[str, Any]:
    """Converte a mensagem do SDK em um item serializavel do historico."""
    payload: dict[str, Any] = {
        "role": "assistant",
        "content": message.content,
    }
    if message.tool_calls:
        payload["tool_calls"] = [
            {
                "id": call.id,
                "type": "function",
                "function": {
                    "name": call.function.name,
                    "arguments": call.function.arguments,
                },
            }
            for call in message.tool_calls
        ]
    return payload


def tool_message(call_id: str, result: dict[str, Any]) -> dict[str, str]:
    """Monta uma mensagem ``tool`` para continuar o historico local."""
    return {
        "role": "tool",
        "tool_call_id": call_id,
        "content": json.dumps(result, ensure_ascii=False, default=str),
    }
