"""Orquestracao da carga do workbook para o SQLite.

Este modulo coordena leitura, preparacao e persistencia. Transformacoes de
dados permanecem isoladas em ``transformations.py`` e operacoes estruturais de
banco em ``database.py``.
"""

from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import Engine

from app.db.database import (
    create_relationship_indexes,
    replace_tables,
    validate_relationship_integrity,
)
from app.domain.sales_model import TABLES
from app.ingestion.transformations import prepare_sheet


def validate_required_sheets(sheet_names: list[str]) -> None:
    """Valida a presenca de todas as abas declaradas no modelo.

    Args:
        sheet_names: Nomes encontrados no workbook.

    Raises:
        ValueError: Se qualquer aba obrigatoria estiver ausente.
    """
    missing = sorted(set(TABLES) - set(sheet_names))
    if missing:
        raise ValueError(
            "Abas obrigatorias ausentes no Excel: " f"{', '.join(missing)}"
        )


def read_and_prepare_workbook(file_path: str | Path) -> dict[str, pd.DataFrame]:
    """Le e prepara o workbook inteiro sem alterar o banco.

    Args:
        file_path: Caminho de um arquivo Excel suportado pelo Pandas.

    Returns:
        Mapeamento entre nome da aba e DataFrame validado.

    Raises:
        OSError: Se o arquivo nao puder ser aberto.
        ValueError: Se abas, colunas ou valores forem invalidos.
    """
    # O context manager fecha o arquivo mesmo quando uma aba falha.
    with pd.ExcelFile(file_path) as excel_file:
        validate_required_sheets(excel_file.sheet_names)
        return {
            sheet_name: prepare_sheet(
                sheet_name,
                pd.read_excel(excel_file, sheet_name=sheet_name, dtype=object),
            )
            for sheet_name in TABLES
        }


def load_excel_to_sqlite(
    file_path: str | Path,
    engine: Engine,
) -> dict[str, Any]:
    """Substitui o modelo estrela por um workbook validado.

    Args:
        file_path: Caminho do workbook de origem.
        engine: Engine do banco que recebera as tabelas.

    Returns:
        Status, contagem de linhas por tabela e relatorio de integridade.

    Raises:
        OSError: Se o workbook nao puder ser lido.
        ValueError: Se a fonte ou os relacionamentos forem invalidos.
        SQLAlchemyError: Se a persistencia falhar.
    """
    prepared_sheets = read_and_prepare_workbook(file_path)
    frames_by_table = {
        TABLES[sheet_name]: dataframe
        for sheet_name, dataframe in prepared_sheets.items()
    }

    # engine.begin confirma tudo junto ou reverte a carga inteira em falhas.
    with engine.begin() as connection:
        replace_tables(connection, frames_by_table)
        create_relationship_indexes(connection)
        integrity = validate_relationship_integrity(connection)

    return {
        "ok": True,
        "tables": {
            table_name: int(len(dataframe))
            for table_name, dataframe in frames_by_table.items()
        },
        "integrity": integrity,
    }
