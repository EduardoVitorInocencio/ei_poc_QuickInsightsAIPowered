"""Infraestrutura do SQLite.

Este modulo concentra a criacao da engine, a persistencia das tabelas e as
validacoes estruturais do modelo estrela. Manter essas operacoes aqui evita que
agentes, interfaces e servicos conhecam detalhes de SQL administrativo.
"""

from collections.abc import Mapping
from typing import Any

import pandas as pd
from sqlalchemy import Engine, create_engine, inspect, text

from app.domain.sales_model import (
    DIMENSION_KEYS,
    EXPECTED_SCHEMAS,
    INDEXES,
    TABLES,
)


def create_database_engine(database_url: str) -> Engine:
    """Cria a engine SQLAlchemy compartilhada pela aplicacao.

    Args:
        database_url: URL SQLAlchemy, normalmente no formato
            ``sqlite:///caminho/database.db``.

    Returns:
        Engine configurada sem log verboso de SQL.
    """
    return create_engine(database_url, echo=False)


def inspect_existing_data(engine: Engine) -> dict[str, Any]:
    """Determina se um banco existente pode ser reutilizado com seguranca.

    A verificacao e feita em camadas: tabelas, colunas, quantidade de registros
    e integridade relacional. Isso impede que a interface ofereca ao usuario um
    banco parcialmente carregado ou incompatível com o agente.

    Args:
        engine: Engine conectada ao banco que sera inspecionado.

    Returns:
        Dicionario com ``usable``, justificativa em ``reason``, contagens por
        tabela e, quando valido, o relatorio de integridade.
    """
    # A inspecao de metadados nao executa consultas produzidas pelo agente.
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    expected_tables = set(TABLES.values())
    missing_tables = sorted(expected_tables - existing_tables)

    if missing_tables:
        return {
            "usable": False,
            "reason": (
                "Tabelas obrigatorias ausentes: " + ", ".join(missing_tables)
            ),
            "row_counts": {},
        }

    # Uma tabela existente ainda pode ser antiga ou ter schema incompleto.
    schema_errors = {}
    for sheet_name, table_name in TABLES.items():
        existing_columns = {
            column["name"] for column in inspector.get_columns(table_name)
        }
        missing_columns = sorted(
            set(EXPECTED_SCHEMAS[sheet_name]) - existing_columns
        )
        if missing_columns:
            schema_errors[table_name] = missing_columns

    if schema_errors:
        return {
            "usable": False,
            "reason": f"Schema incompleto: {schema_errors}",
            "row_counts": {},
        }

    # Contagens e integridade usam a mesma conexao de leitura.
    with engine.connect() as connection:
        row_counts = {
            table_name: int(
                connection.execute(
                    text(f'SELECT COUNT(*) FROM "{table_name}"')
                ).scalar_one()
            )
            for table_name in sorted(expected_tables)
        }
        try:
            integrity = validate_relationship_integrity(connection)
        except ValueError as error:
            return {
                "usable": False,
                "reason": str(error),
                "row_counts": row_counts,
            }

    empty_tables = [
        table_name for table_name, count in row_counts.items() if count == 0
    ]
    if empty_tables:
        return {
            "usable": False,
            "reason": "Tabelas sem dados: " + ", ".join(empty_tables),
            "row_counts": row_counts,
        }

    return {
        "usable": True,
        "reason": "Modelo estrela completo e com dados.",
        "row_counts": row_counts,
        "integrity": integrity,
    }


def replace_tables(
    connection: Any,
    frames_by_table: Mapping[str, pd.DataFrame],
) -> None:
    """Substitui as tabelas SQLite pelos DataFrames preparados.

    A transacao e controlada pelo chamador para que carga, indices e validacao
    sejam confirmados ou revertidos como uma unica unidade.

    Args:
        connection: Conexao transacional SQLAlchemy.
        frames_by_table: Mapeamento entre nome da tabela e DataFrame pronto.
    """
    for table_name, dataframe in frames_by_table.items():
        dataframe.to_sql(
            table_name,
            connection,
            if_exists="replace",
            index=False,
        )


def create_relationship_indexes(connection: Any) -> None:
    """Cria indices usados pelos JOINs mais frequentes.

    Args:
        connection: Conexao SQLAlchemy com permissao para criar os indices.
    """
    for index_name, (table_name, column_name) in INDEXES.items():
        connection.execute(
            text(
                f'CREATE INDEX IF NOT EXISTS "{index_name}" '
                f'ON "{table_name}" ("{column_name}")'
            )
        )


def find_duplicate_dimension_keys(connection: Any) -> dict[str, int]:
    """Conta grupos de chaves duplicadas em cada dimensao.

    Args:
        connection: Conexao com as tabelas do modelo ja carregadas.

    Returns:
        Mapeamento de tabela para quantidade de chaves que aparecem mais de
        uma vez. O valor representa grupos duplicados, nao linhas totais.
    """
    duplicates = {}
    for table_name, key_column in DIMENSION_KEYS.items():
        query = text(
            f'SELECT COUNT(*) FROM ('
            f'SELECT "{key_column}" FROM "{table_name}" '
            f'WHERE "{key_column}" IS NOT NULL '
            f'GROUP BY "{key_column}" HAVING COUNT(*) > 1'
            f")"
        )
        duplicates[table_name] = int(connection.execute(query).scalar_one())
    return duplicates


def find_orphan_relationships(connection: Any) -> dict[str, int]:
    """Conta chaves sem correspondencia em cada relacionamento esperado.

    Args:
        connection: Conexao com fato e dimensoes disponiveis.

    Returns:
        Mapeamento descritivo do relacionamento para quantidade de registros
        orfaos encontrados.
    """
    # LEFT JOIN preserva a origem e permite localizar a dimensao ausente.
    checks = {
        "fact.cdCliente -> dim_cliente.cdCliente": """
            SELECT COUNT(*) FROM fact AS f
            LEFT JOIN dim_cliente AS d ON f.cdCliente = d.cdCliente
            WHERE f.cdCliente IS NOT NULL AND d.cdCliente IS NULL
        """,
        "fact.cdVendedor -> dim_vendedor.cdVendedor": """
            SELECT COUNT(*) FROM fact AS f
            LEFT JOIN dim_vendedor AS d ON f.cdVendedor = d.cdVendedor
            WHERE f.cdVendedor IS NOT NULL AND d.cdVendedor IS NULL
        """,
        "fact.cdProduto -> dim_produto.cdProduto": """
            SELECT COUNT(*) FROM fact AS f
            LEFT JOIN dim_produto AS d ON f.cdProduto = d.cdProduto
            WHERE f.cdProduto IS NOT NULL AND d.cdProduto IS NULL
        """,
        "fact.DataEmissao -> dim_data.Data": """
            SELECT COUNT(*) FROM fact AS f
            LEFT JOIN dim_data AS d ON f.DataEmissao = d.Data
            WHERE f.DataEmissao IS NOT NULL AND d.Data IS NULL
        """,
        "fact.DataVencimento -> dim_data.Data": """
            SELECT COUNT(*) FROM fact AS f
            LEFT JOIN dim_data AS d ON f.DataVencimento = d.Data
            WHERE f.DataVencimento IS NOT NULL AND d.Data IS NULL
        """,
        "dim_produto.cdGrupo -> dim_grupo_produto.cdGrupo": """
            SELECT COUNT(*) FROM dim_produto AS p
            LEFT JOIN dim_grupo_produto AS d ON p.cdGrupo = d.cdGrupo
            WHERE p.cdGrupo IS NOT NULL AND d.cdGrupo IS NULL
        """,
    }
    return {
        relationship: int(connection.execute(text(query)).scalar_one())
        for relationship, query in checks.items()
    }


def validate_relationship_integrity(
    connection: Any,
) -> dict[str, dict[str, int]]:
    """Valida as regras de integridade que o SQLite nao declara como FKs.

    Args:
        connection: Conexao com o modelo estrela completamente carregado.

    Returns:
        Contagens de duplicidades e registros orfaos, todas iguais a zero.

    Raises:
        ValueError: Se uma dimensao tiver chave duplicada ou um relacionamento
            possuir registros sem correspondencia.
    """
    duplicate_keys = find_duplicate_dimension_keys(connection)
    orphan_records = find_orphan_relationships(connection)

    errors = []
    invalid_duplicates = {
        table: count for table, count in duplicate_keys.items() if count
    }
    invalid_orphans = {
        relationship: count
        for relationship, count in orphan_records.items()
        if count
    }
    if invalid_duplicates:
        errors.append(f"chaves duplicadas: {invalid_duplicates}")
    if invalid_orphans:
        errors.append(f"relacionamentos orfaos: {invalid_orphans}")
    if errors:
        raise ValueError(
            "Falha na integridade do modelo estrela; " + "; ".join(errors)
        )

    return {
        "duplicate_dimension_keys": duplicate_keys,
        "orphan_relationships": orphan_records,
    }
