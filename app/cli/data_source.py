"""Fluxo interativo de selecao e preparacao da fonte de vendas."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from app.cli.console import (
    InputFunction,
    OutputFunction,
    ask_excel_path,
    ask_yes_no,
)
from app.db.database import inspect_existing_data
from app.ingestion.excel_to_sqlite import load_excel_to_sqlite

if TYPE_CHECKING:
    from app.bootstrap import Application


def prepare_data_source(
    application: Application,
    *,
    input_fn: InputFunction = input,
    output_fn: OutputFunction = print,
) -> dict[str, Any]:
    """Reutiliza um banco valido ou carrega um workbook informado.

    Args:
        application: Container que fornece a engine configurada.
        input_fn: Entrada interativa injetavel.
        output_fn: Saida interativa injetavel.

    Returns:
        Metadados da fonte escolhida e das tabelas disponiveis.
    """
    database_status = inspect_existing_data(application.engine)
    if database_status["usable"]:
        output_fn("Foram encontrados dados validos no banco:")
        output_fn(
            json.dumps(
                database_status["row_counts"],
                ensure_ascii=False,
                indent=2,
            )
        )
        if ask_yes_no(
            "Deseja usar os dados existentes? [s/n]: ",
            input_fn=input_fn,
            output_fn=output_fn,
        ):
            return {
                "ok": True,
                "source": "database",
                "tables": database_status["row_counts"],
            }
    else:
        output_fn(
            "Nao foram encontrados dados validos no banco. "
            f"Motivo: {database_status['reason']}"
        )

    # Uma carga invalida nao encerra a sessao; o usuario pode corrigir o path.
    while True:
        excel_path = ask_excel_path(input_fn=input_fn, output_fn=output_fn)
        try:
            result = load_excel_to_sqlite(excel_path, application.engine)
            return {
                **result,
                "source": "excel",
                "excel_path": str(excel_path),
            }
        except (OSError, ValueError) as error:
            output_fn(f"Falha ao carregar o arquivo: {error}")
            output_fn("Informe outro arquivo Excel.")
