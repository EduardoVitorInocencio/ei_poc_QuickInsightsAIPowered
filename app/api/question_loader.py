"""Leitura de perguntas a partir de arquivos Excel."""

from __future__ import annotations

from io import BytesIO
from typing import Any

import pandas as pd

from app.ingestion.transformations import normalize_column_name

QUESTION_COLUMN_ALIASES = {
    "question",
    "questions",
    "pergunta",
    "perguntas",
    "questao",
    "questoes",
}


def extract_questions_from_excel(content: bytes) -> list[str]:
    """Extrai perguntas de todas as abas de um workbook.

    A estrategia e conservadora: se houver uma coluna com nome conhecido,
    ela e usada; caso contrario, a primeira coluna nao vazia de cada aba e
    considerada. Isso permite planilhas simples e tambem planilhas mais
    estruturadas sem acoplamento a um layout unico.

    Args:
        content: Conteudo binario do arquivo Excel.

    Returns:
        Lista ordenada de perguntas nao vazias.

    Raises:
        ValueError: Se o arquivo nao contiver perguntas legiveis.
    """
    questions: list[str] = []
    with pd.ExcelFile(BytesIO(content)) as excel_file:
        for sheet_name in excel_file.sheet_names:
            dataframe = pd.read_excel(
                excel_file,
                sheet_name=sheet_name,
                dtype=object,
            )
            if dataframe.empty:
                continue
            questions.extend(_extract_sheet_questions(dataframe))
    questions = [question for question in questions if question]
    if not questions:
        raise ValueError("Nenhuma pergunta foi encontrada no arquivo Excel.")
    return questions


def _extract_sheet_questions(dataframe: pd.DataFrame) -> list[str]:
    """Extrai perguntas de uma aba individual.

    Args:
        dataframe: Aba lida do Excel.

    Returns:
        Lista de textos encontrados na aba.
    """
    if dataframe.empty:
        return []

    columns = list(dataframe.columns)
    preferred_column = None
    for column in columns:
        normalized = normalize_column_name(column).casefold()
        if normalized in QUESTION_COLUMN_ALIASES:
            preferred_column = column
            break

    source_column = preferred_column or columns[0]
    series = dataframe[source_column].dropna().astype(str).map(str.strip)
    return [value for value in series if value]

