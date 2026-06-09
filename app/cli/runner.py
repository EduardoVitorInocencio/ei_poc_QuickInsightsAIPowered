"""Orquestrador do caso de uso executado pela CLI."""

import json
import logging
from collections.abc import Callable

from app.bootstrap import Application, create_application
from app.cli.console import (
    InputFunction,
    OutputFunction,
    ask_output_format,
    ask_yes_no,
    collect_questions,
    display_answers,
)
from app.cli.data_source import prepare_data_source
from app.services.question_processing import classify_question

ApplicationFactory = Callable[[], Application]


def configure_logging() -> None:
    """Configura o formato padrao de logs da aplicacao."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def run_cli(
    *,
    application_factory: ApplicationFactory = create_application,
    input_fn: InputFunction = input,
    output_fn: OutputFunction = print,
) -> None:
    """Executa uma sessao completa sem concentrar regras no entrypoint.

    Args:
        application_factory: Fabrica injetavel do container da aplicacao.
        input_fn: Fonte das entradas interativas.
        output_fn: Destino das mensagens apresentadas.
    """
    configure_logging()
    application = application_factory()
    questions = collect_questions(input_fn=input_fn, output_fn=output_fn)
    if not questions:
        output_fn("Nenhuma pergunta informada.")
        return

    if any(classify_question(question) == "sales" for question in questions):
        data_result = prepare_data_source(
            application,
            input_fn=input_fn,
            output_fn=output_fn,
        )
        if data_result["source"] == "database":
            output_fn("Usando os dados existentes no banco.")
        else:
            output_fn("Nova carga concluida:")
            output_fn(
                json.dumps(data_result, ensure_ascii=False, indent=2)
            )

    result = application.processing.process(questions)
    display_answers(result["answers"], output_fn=output_fn)
    if result["sales_insight_count"] == 0:
        return

    if not ask_yes_no(
        "\nDeseja gerar um output com os insights de vendas? [s/n]: ",
        input_fn=input_fn,
        output_fn=output_fn,
    ):
        output_fn("Output nao gerado.")
        return

    output_format = ask_output_format(
        input_fn=input_fn,
        output_fn=output_fn,
    )
    export_result = application.exports.export(output_format)
    output_fn(
        f"Output {export_result['format']} gerado em: "
        f"{export_result['output_path']}"
    )
