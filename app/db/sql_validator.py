"""Politica defensiva para SQL produzido pelo SalesAgent.

A validacao reduz a superficie de risco antes que qualquer texto gerado pelo
modelo seja entregue ao driver SQLite.
"""

import re
from dataclasses import dataclass
from typing import AbstractSet

from app.domain.sales_model import ALLOWED_TABLES, FACT_TABLE, SALES_EXPRESSION

FORBIDDEN_COMMANDS = (
    "DELETE",
    "UPDATE",
    "DROP",
    "INSERT",
    "ALTER",
    "CREATE",
    "REPLACE",
    "TRUNCATE",
    "ATTACH",
    "DETACH",
    "PRAGMA",
    "VACUUM",
)


def strip_sql_literals(query: str) -> str:
    """Substitui literais para evitar falsos positivos de palavras proibidas."""
    return re.sub(r"'(?:''|[^'])*'", "''", query)


def extract_referenced_tables(query: str) -> set[str]:
    """Extrai nomes declarados depois de ``FROM`` e ``JOIN``.

    Args:
        query: SQL sem necessidade de estar validado.

    Returns:
        Conjunto de nomes em minusculas.
    """
    pattern = r'\b(?:FROM|JOIN)\s+["`\[]?([A-Za-z_][A-Za-z0-9_]*)'
    return {
        table_name.lower()
        for table_name in re.findall(pattern, query, flags=re.IGNORECASE)
    }


@dataclass(frozen=True)
class SqlValidator:
    """Politica configuravel de tabelas permitidas e fato obrigatoria."""

    allowed_tables: AbstractSet[str] = ALLOWED_TABLES
    required_fact_table: str = FACT_TABLE

    def validate(self, query: str) -> None:
        """Permite somente um SELECT no modelo estrela.

        Args:
            query: Texto SQL produzido pelo modelo.

        Raises:
            ValueError: Para SQL vazio, comentarios, multiplas instrucoes,
                operacoes proibidas, tabelas externas, ausencia da fato ou uso
                da coluna inexistente ``ValorVenda``.
        """
        # Literais sao removidos apenas para analise; o SQL original e executado.
        if not isinstance(query, str) or not query.strip():
            raise ValueError("A consulta SQL nao pode estar vazia.")

        cleaned = strip_sql_literals(query).strip()
        if "--" in cleaned or "/*" in cleaned or "*/" in cleaned:
            raise ValueError("Comentarios SQL nao sao permitidos.")

        statements = [
            statement.strip()
            for statement in cleaned.split(";")
            if statement.strip()
        ]
        if len(statements) != 1:
            raise ValueError("Apenas uma instrucao SQL e permitida por chamada.")

        statement = statements[0]
        if not re.match(r"^SELECT\b", statement, flags=re.IGNORECASE):
            raise ValueError("Apenas queries SELECT sao permitidas.")

        forbidden_pattern = rf"\b(?:{'|'.join(FORBIDDEN_COMMANDS)})\b"
        match = re.search(forbidden_pattern, statement, flags=re.IGNORECASE)
        if match:
            raise ValueError(
                f"Operacao proibida detectada: {match.group(0).upper()}"
            )

        referenced_tables = extract_referenced_tables(statement)
        if not referenced_tables:
            raise ValueError(
                f"A consulta deve referenciar a tabela {self.required_fact_table}."
            )

        unauthorized = sorted(referenced_tables - set(self.allowed_tables))
        if unauthorized:
            raise ValueError(
                "A consulta referencia tabela(s) nao permitida(s): "
                f"{', '.join(unauthorized)}"
            )

        if self.required_fact_table not in referenced_tables:
            raise ValueError(
                f"A consulta deve usar {self.required_fact_table} "
                "como tabela fato principal."
            )

        if re.search(r"\bValorVenda\b", statement, flags=re.IGNORECASE):
            raise ValueError(
                "A coluna ValorVenda nao existe. Para vendas, use "
                f"{SALES_EXPRESSION}."
            )
