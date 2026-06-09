"""Contrato central do modelo estrela de vendas.

Constantes de schema ficam neste modulo para que ingestao, banco, validacao e
prompt compartilhem a mesma fonte de verdade.
"""

# Nome e expressao de negocio usados pelo validador e pelo agente.
FACT_TABLE = "fact"
SALES_EXPRESSION = "SUM(fact.QtdItens * fact.ValorUnitario)"

# Mapeia o nome da aba de origem para a tabela persistida.
TABLES = {
    "fact": "fact",
    "Cliente": "dim_cliente",
    "Produto": "dim_produto",
    "GrupoProduto": "dim_grupo_produto",
    "Vendedor": "dim_vendedor",
    "Data": "dim_data",
}

# Colunas apos normalizacao dos cabecalhos do Excel.
EXPECTED_SCHEMAS = {
    "fact": [
        "DataEmissao",
        "DataVencimento",
        "NFe",
        "cdCliente",
        "cdVendedor",
        "cdProduto",
        "QtdItens",
        "ValorUnitario",
        "PesoLiquido",
    ],
    "Cliente": [
        "cdCliente",
        "RazaoSocial",
        "Status",
        "Categoria",
        "Cidade",
        "UF",
    ],
    "Produto": ["cdProduto", "Descricao", "cdGrupo"],
    "GrupoProduto": ["cdGrupo", "Grupo", "Linha"],
    "Vendedor": [
        "cdVendedor",
        "Vendedor",
        "cdSupervisor",
        "Supervisor",
        "cdGerente",
        "Gerente",
        "Equipe",
    ],
    "Data": ["Data", "Ano", "Mes", "MesNum", "Dia"],
}

# Conjunto imutavel usado pela politica SQL.
ALLOWED_TABLES = frozenset(TABLES.values())

# Relacionamentos informados ao agente e validados apos a carga.
RELATIONSHIPS = [
    {"from": "fact.cdCliente", "to": "dim_cliente.cdCliente"},
    {"from": "fact.cdVendedor", "to": "dim_vendedor.cdVendedor"},
    {"from": "fact.cdProduto", "to": "dim_produto.cdProduto"},
    {"from": "fact.DataEmissao", "to": "dim_data.Data"},
    {"from": "fact.DataVencimento", "to": "dim_data.Data"},
    {
        "from": "dim_produto.cdGrupo",
        "to": "dim_grupo_produto.cdGrupo",
    },
]

# Indices fisicos que aceleram os JOINs mais comuns.
INDEXES = {
    "idx_fact_cdcliente": ("fact", "cdCliente"),
    "idx_fact_cdvendedor": ("fact", "cdVendedor"),
    "idx_fact_cdproduto": ("fact", "cdProduto"),
    "idx_fact_dataemissao": ("fact", "DataEmissao"),
    "idx_fact_datavencimento": ("fact", "DataVencimento"),
    "idx_dim_cliente_cdcliente": ("dim_cliente", "cdCliente"),
    "idx_dim_produto_cdproduto": ("dim_produto", "cdProduto"),
    "idx_dim_produto_cdgrupo": ("dim_produto", "cdGrupo"),
    "idx_dim_grupo_produto_cdgrupo": ("dim_grupo_produto", "cdGrupo"),
    "idx_dim_vendedor_cdvendedor": ("dim_vendedor", "cdVendedor"),
    "idx_dim_data_data": ("dim_data", "Data"),
}

# Chaves que devem ser unicas dentro das dimensoes.
DIMENSION_KEYS = {
    "dim_cliente": "cdCliente",
    "dim_produto": "cdProduto",
    "dim_grupo_produto": "cdGrupo",
    "dim_vendedor": "cdVendedor",
    "dim_data": "Data",
}


def get_schema_contract() -> dict:
    """Monta o schema serializavel usado por ``inspect_sales_schema``.

    Returns:
        Dicionario com fato, tabelas, colunas, relacionamentos, expressao de
        vendas e lista de tabelas autorizadas.
    """
    tables = {
        TABLES[sheet_name]: {
            "source_sheet": sheet_name,
            "columns": columns,
        }
        for sheet_name, columns in EXPECTED_SCHEMAS.items()
    }
    return {
        "fact_table": FACT_TABLE,
        "tables": tables,
        "relationships": RELATIONSHIPS,
        "sales_expression": SALES_EXPRESSION,
        "allowed_tables": sorted(ALLOWED_TABLES),
    }
