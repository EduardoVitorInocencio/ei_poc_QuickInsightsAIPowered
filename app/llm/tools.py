"""Schemas e registro de function calling.

As listas separadas de tools sao uma barreira de seguranca: cada agente recebe
somente as capacidades necessarias para sua responsabilidade.
"""

from collections.abc import Callable
from typing import Any

ToolHandler = Callable[[dict[str, Any]], dict[str, Any]]

# Tool sem argumentos usada para reduzir erros de schema antes do SQL.
INSPECT_SCHEMA_TOOL = {
    "type": "function",
    "name": "inspect_sales_schema",
    "description": "Retorna o contrato completo do modelo estrela de vendas.",
    "parameters": {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    },
    "strict": True,
}

# Unico ponto pelo qual SQL gerado pelo modelo alcanca o InsightsService.
RUN_SQL_TOOL = {
    "type": "function",
    "name": "run_sql_query",
    "description": (
        "Valida e executa uma consulta SQLite SELECT no modelo de vendas."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "sql": {
                "type": "string",
                "description": "Consulta SELECT para responder a pergunta.",
            }
        },
        "required": ["sql"],
        "additionalProperties": False,
    },
    "strict": True,
}

# Contrato estruturado que separa a analise do momento da exportacao.
SUBMIT_INSIGHT_TOOL = {
    "type": "function",
    "name": "submit_sales_insight",
    "description": (
        "Registra o insight estruturado depois de analisar um resultado SQL. "
        "Esta ferramenta nao cria arquivos."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "result_id": {
                "type": "string",
                "description": "Identificador retornado por run_sql_query.",
            },
            "titulo": {"type": "string"},
            "headline": {"type": "string"},
            "analise": {
                "type": "string",
                "description": (
                    "Breve analise executiva, fundamentada somente nos dados."
                ),
            },
        },
        "required": ["result_id", "titulo", "headline", "analise"],
        "additionalProperties": False,
    },
    "strict": True,
}

# Capacidade externa isolada do conjunto de ferramentas de vendas.
WEATHER_TOOL = {
    "type": "function",
    "name": "get_current_weather",
    "description": "Obtem as condicoes meteorologicas atuais de uma cidade.",
    "parameters": {
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "Nome da cidade, por exemplo Sao Paulo.",
            },
            "country_code": {
                "type": "string",
                "description": (
                    "Codigo ISO de duas letras, por exemplo BR. Campo opcional."
                ),
            },
        },
        "required": ["city"],
        "additionalProperties": False,
    },
    "strict": True,
}

# Cada agente recebe apenas uma destas listas; elas nao devem ser combinadas.
SALES_TOOLS = [INSPECT_SCHEMA_TOOL, RUN_SQL_TOOL, SUBMIT_INSIGHT_TOOL]
EXTERNAL_TOOLS = [WEATHER_TOOL]


class ToolRegistry:
    """Mapeia nomes autorizados para handlers locais testaveis."""

    def __init__(self, handlers: dict[str, ToolHandler]) -> None:
        """Recebe os handlers permitidos para uma instancia de agente."""
        self._handlers = handlers

    def invoke(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Executa uma ferramenta registrada.

        Args:
            name: Nome recebido na chamada do modelo.
            arguments: Argumentos JSON ja convertidos para dicionario.

        Returns:
            Resultado serializavel do handler.

        Raises:
            ValueError: Se o modelo solicitar uma ferramenta nao registrada.
        """
        handler = self._handlers.get(name)
        if handler is None:
            raise ValueError(f"Ferramenta desconhecida: {name}")
        return handler(arguments)
