"""Transformacoes puras aplicadas antes da persistencia.

As funcoes deste modulo recebem DataFrames e devolvem novas copias. Essa
abordagem evita efeitos colaterais durante validacoes e permite testar cada
regra de conversao sem acessar Excel ou SQLite.
"""

import re
import unicodedata
from typing import Any

import pandas as pd

from app.domain.sales_model import EXPECTED_SCHEMAS

# As listas por aba tornam explicito quais regras se aplicam a cada schema.
IDENTIFIER_COLUMNS = {
    "fact": ["NFe", "cdCliente", "cdVendedor", "cdProduto"],
    "Cliente": ["cdCliente"],
    "Produto": ["cdProduto", "cdGrupo"],
    "GrupoProduto": ["cdGrupo"],
    "Vendedor": ["cdVendedor", "cdSupervisor", "cdGerente"],
    "Data": [],
}

NUMERIC_COLUMNS = {
    "fact": ["QtdItens", "ValorUnitario", "PesoLiquido"],
    "Data": ["Ano", "MesNum", "Dia"],
}

DATE_COLUMNS = {
    "fact": ["DataEmissao", "DataVencimento"],
    "Data": ["Data"],
}


def normalize_column_name(column_name: Any) -> str:
    """Converte um cabecalho do Excel em identificador SQL simples.

    Args:
        column_name: Nome original, de qualquer tipo convertivel para texto.

    Returns:
        Nome ASCII sem espacos, acentos ou caracteres especiais.
    """
    normalized = unicodedata.normalize("NFKD", str(column_name).strip())
    without_accents = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^A-Za-z0-9_]", "", without_accents)


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza todos os cabecalhos e detecta colisoes de nomes.

    Args:
        df: DataFrame original lido do workbook.

    Returns:
        Copia com os cabecalhos normalizados.

    Raises:
        ValueError: Se dois cabecalhos diferentes resultarem no mesmo nome.
    """
    normalized_df = df.copy()
    normalized_df.columns = [
        normalize_column_name(column) for column in normalized_df.columns
    ]
    duplicated = normalized_df.columns[normalized_df.columns.duplicated()].tolist()
    if duplicated:
        raise ValueError(
            "A normalizacao gerou nomes de colunas duplicados: "
            f"{sorted(set(duplicated))}"
        )
    return normalized_df


def validate_required_columns(sheet_name: str, df: pd.DataFrame) -> None:
    """Confirma que uma aba normalizada atende seu contrato de schema.

    Args:
        sheet_name: Nome da aba conforme definido em ``EXPECTED_SCHEMAS``.
        df: DataFrame cujas colunas ja foram normalizadas.

    Raises:
        KeyError: Se ``sheet_name`` nao possuir contrato conhecido.
        ValueError: Se uma ou mais colunas obrigatorias estiverem ausentes.
    """
    missing = sorted(set(EXPECTED_SCHEMAS[sheet_name]) - set(df.columns))
    if missing:
        raise ValueError(
            f"A aba '{sheet_name}' nao possui as colunas obrigatorias: "
            f"{', '.join(missing)}"
        )


def convert_identifier(series: pd.Series) -> pd.Series:
    """Padroniza chaves para texto anulavel e remove sufixos ``.0``.

    Args:
        series: Coluna de identificadores possivelmente lida como numero.

    Returns:
        Serie ``string`` com espacos removidos e vazios convertidos em nulos.
    """
    converted = series.astype("string").str.strip()
    converted = converted.str.replace(r"\.0$", "", regex=True)
    return converted.mask(converted.eq(""))


def convert_date(series: pd.Series, column_name: str) -> pd.Series:
    """Converte uma coluna de datas para texto ISO ``YYYY-MM-DD``.

    Args:
        series: Valores de data vindos do Excel.
        column_name: Nome usado na mensagem de validacao.

    Returns:
        Serie textual em formato ISO, adequado para JOINs no SQLite.

    Raises:
        ValueError: Se um valor preenchido nao puder ser convertido.
    """
    converted = pd.to_datetime(series, errors="coerce")
    invalid_count = int((series.notna() & converted.isna()).sum())
    if invalid_count:
        raise ValueError(
            f"A coluna '{column_name}' possui {invalid_count} data(s) invalida(s)."
        )
    return converted.dt.strftime("%Y-%m-%d")


def convert_numeric(series: pd.Series, column_name: str) -> pd.Series:
    """Converte valores numericos sem ocultar erros da fonte.

    Args:
        series: Coluna que deve conter numeros.
        column_name: Nome usado na mensagem de erro.

    Returns:
        Serie numerica; valores originalmente vazios permanecem nulos.

    Raises:
        ValueError: Se um valor preenchido nao for numerico.
    """
    converted = pd.to_numeric(series, errors="coerce")
    invalid_count = int((series.notna() & converted.isna()).sum())
    if invalid_count:
        raise ValueError(
            f"A coluna '{column_name}' possui "
            f"{invalid_count} valor(es) numerico(s) invalido(s)."
        )
    return converted


def transform_types(sheet_name: str, df: pd.DataFrame) -> pd.DataFrame:
    """Aplica as regras declarativas de tipo correspondentes a uma aba.

    Args:
        sheet_name: Aba de origem usada para selecionar as regras.
        df: DataFrame validado e com colunas normalizadas.

    Returns:
        Copia com identificadores, numeros e datas padronizados.
    """
    transformed = df.copy()
    for column in IDENTIFIER_COLUMNS.get(sheet_name, []):
        transformed[column] = convert_identifier(transformed[column])
    for column in NUMERIC_COLUMNS.get(sheet_name, []):
        transformed[column] = convert_numeric(transformed[column], column)
    for column in DATE_COLUMNS.get(sheet_name, []):
        transformed[column] = convert_date(transformed[column], column)
    return transformed


def prepare_sheet(sheet_name: str, df: pd.DataFrame) -> pd.DataFrame:
    """Executa o pipeline completo de preparacao de uma aba.

    A ordem e intencional: primeiro normaliza os nomes, depois valida o
    contrato, descarta colunas extras e por fim converte os tipos.

    Args:
        sheet_name: Nome da aba esperada.
        df: Dados brutos lidos do Excel.

    Returns:
        DataFrame pronto para persistencia na tabela correspondente.

    Raises:
        ValueError: Se cabecalhos, colunas ou valores forem invalidos.
    """
    prepared = normalize_columns(df)
    validate_required_columns(sheet_name, prepared)
    prepared = prepared[EXPECTED_SCHEMAS[sheet_name]].copy()
    return transform_types(sheet_name, prepared)
