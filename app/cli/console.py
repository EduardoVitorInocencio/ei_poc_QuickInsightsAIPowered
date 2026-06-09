"""Entrada, validacao e apresentacao da interface de linha de comando.

Este modulo nao conhece banco, agentes ou SDKs. Suas funcoes recebem entrada e
saida injetaveis para permanecerem reutilizaveis e simples de testar.
"""

import unicodedata
from collections.abc import Callable
from pathlib import Path
from typing import Any

InputFunction = Callable[[str], str]
OutputFunction = Callable[[str], None]


def normalize_answer(value: str) -> str:
    """Normaliza uma resposta curta para comparacoes independentes de acento.

    Args:
        value: Texto digitado pelo usuario.

    Returns:
        Texto em minusculas, sem espacos externos nem marcas de acentuacao.
    """
    decomposed = unicodedata.normalize("NFKD", value.strip().casefold())
    return "".join(
        character
        for character in decomposed
        if not unicodedata.combining(character)
    )


def ask_yes_no(
    prompt: str,
    *,
    input_fn: InputFunction = input,
    output_fn: OutputFunction = print,
) -> bool:
    """Solicita uma resposta booleana e repete entradas invalidas.

    Args:
        prompt: Texto apresentado ao usuario.
        input_fn: Funcao de entrada injetavel para testes.
        output_fn: Funcao usada para mensagens de validacao.

    Returns:
        ``True`` para sim e ``False`` para nao.
    """
    while True:
        answer = normalize_answer(input_fn(prompt))
        if answer in {"s", "sim"}:
            return True
        if answer in {"n", "nao"}:
            return False
        output_fn("Resposta invalida. Digite 's' para sim ou 'n' para nao.")


def ask_output_format(
    *,
    input_fn: InputFunction = input,
    output_fn: OutputFunction = print,
) -> str:
    """Solicita um dos formatos suportados de exportacao.

    Args:
        input_fn: Funcao de entrada injetavel.
        output_fn: Funcao de saida para erros de validacao.

    Returns:
        ``pptx`` ou ``markdown`` em formato canonico.
    """
    while True:
        answer = normalize_answer(
            input_fn("Escolha o formato do output [pptx/markdown]: ")
        )
        if answer == "pptx":
            return "pptx"
        if answer in {"md", "markdown"}:
            return "markdown"
        output_fn("Formato invalido. Digite 'pptx' ou 'markdown'.")


def ask_excel_path(
    *,
    input_fn: InputFunction = input,
    output_fn: OutputFunction = print,
) -> Path:
    """Solicita um workbook existente e com extensao suportada.

    Args:
        input_fn: Funcao usada para ler o caminho.
        output_fn: Funcao usada para explicar entradas invalidas.

    Returns:
        Caminho validado para um arquivo ``.xlsx`` ou ``.xlsm``.
    """
    while True:
        raw_path = input_fn("Informe o caminho do novo arquivo Excel: ").strip()
        path = Path(raw_path.strip("\"'")).expanduser()
        if not raw_path:
            output_fn("O caminho do arquivo nao pode estar vazio.")
            continue
        if not path.is_file():
            output_fn(f"Arquivo nao encontrado: {path}")
            continue
        if path.suffix.lower() not in {".xlsx", ".xlsm"}:
            output_fn("O arquivo deve possuir extensao .xlsx ou .xlsm.")
            continue
        return path


def collect_questions(
    *,
    input_fn: InputFunction = input,
    output_fn: OutputFunction = print,
) -> list[str]:
    """Coleta perguntas ate uma linha vazia ou o comando ``sair``.

    Args:
        input_fn: Funcao de entrada, substituivel em testes.
        output_fn: Funcao de saida para instrucoes.

    Returns:
        Lista na ordem digitada ou lista vazia quando o usuario sair.
    """
    output_fn(
        "Digite perguntas de vendas ou ferramentas externas, uma por linha. "
        "Pressione Enter em uma linha vazia para processar."
    )
    questions = []
    while True:
        question = input_fn(f"Pergunta {len(questions) + 1}: ").strip()
        if not question:
            break
        if normalize_answer(question) == "sair":
            return []
        questions.append(question)
    return questions


def display_answers(
    answers: list[dict[str, Any]],
    *,
    output_fn: OutputFunction = print,
) -> None:
    """Apresenta respostas processadas sem conhecer os agentes concretos.

    Args:
        answers: Respostas ordenadas produzidas pelo servico de processamento.
        output_fn: Destino textual da interface.
    """
    output_fn("\nRespostas:")
    for answer in answers:
        agent_label = (
            "ExternalToolsAgent"
            if answer["agent"] == "external"
            else "SalesAgent"
        )
        output_fn(
            f"\n{answer['question_number']}. [{agent_label}] "
            f"{answer['question']}\n{answer['response_text']}"
        )
