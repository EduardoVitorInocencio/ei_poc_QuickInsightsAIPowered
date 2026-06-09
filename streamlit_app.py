"""Interface Streamlit desacoplada da API.

A tela compartilha os mesmos servicos do projeto, mas roda fora do servidor
FastAPI. Assim, a UI pode carregar dados, conversar com o bot e processar um
Excel de perguntas sem interferir na API existente.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import streamlit as st

from app.api.service import ApiService, UploadedFileData
from app.api.question_loader import extract_questions_from_excel
from app.bootstrap import create_application
from app.db.database import create_database_engine, inspect_existing_data
from app.ingestion.excel_to_sqlite import load_excel_to_sqlite
from app.llm.providers import PROVIDER_DEFAULTS
from app.ui.config import UI_PROVIDER_OPTIONS, build_ui_model_config, build_ui_settings


# O Streamlit oferece um cache de recursos que mantem objetos pesados entre
# interacoes. Aqui reaproveitamos a aplicacao criada para o provider atual.
@st.cache_resource(show_spinner=False)
def _build_application(settings):
    """Cria e reutiliza a aplicacao para uma configuracao de provider."""
    return create_application(settings)


def _db_url() -> str:
    """Retorna o mesmo banco SQLite usado pela aplicacao principal."""
    return os.getenv("DB_PATH", "sqlite:///app/data/database.db")


def _persist_upload_to_temp(uploaded_file) -> Path:
    """Salva o upload em disco temporariamente para reaproveitar o loader."""
    suffix = Path(uploaded_file.name or "upload.xlsx").suffix or ".xlsx"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(uploaded_file.getvalue())
        return Path(temp_file.name)


def _render_provider_sidebar() -> dict[str, str]:
    """Coleta provider, modelo e credenciais sem forcar a carga de dados."""
    st.sidebar.header("Provider LLM")

    # Escolhe o provider visivel na interface e carrega os valores padrao.
    provider = st.sidebar.selectbox("Provider", UI_PROVIDER_OPTIONS, index=0)
    provider_defaults = PROVIDER_DEFAULTS[provider]
    provider_prefix = provider.upper()

    # Permite sobrescrever modelo e credenciais diretamente pela UI.
    model = st.sidebar.text_input(
        "Modelo",
        value=(
            os.getenv(f"{provider_prefix}_MODEL")
            or os.getenv("LLM_MODEL")
            or provider_defaults["model"]
        ),
    )
    api_key_default = (
        os.getenv(provider_defaults["api_key_env"])
        or provider_defaults.get("api_key_fallback", "")
    )
    api_key = st.sidebar.text_input(
        "API key",
        value=api_key_default,
        type="password",
    )
    base_url = st.sidebar.text_input(
        "Base URL",
        value=(
            os.getenv(f"{provider_prefix}_BASE_URL")
            or os.getenv("LLM_BASE_URL")
            or provider_defaults["base_url"]
            or ""
        ),
        placeholder="Obrigatorio apenas para custom",
    )

    st.sidebar.caption(
        "A UI usa a mesma camada de dominio da CLI, mas sem passar pela API."
    )

    # Retorna a configuracao escolhida para uso em todo o app Streamlit.
    return {
        "provider": provider,
        "model": model,
        "api_key": api_key,
        "base_url": base_url,
    }


def _render_database_loader() -> None:
    """Mostra o fluxo de carga do Excel de vendas para o SQLite."""
    st.subheader("Carregar dados do Excel")
    st.write(
        "Use esta area para carregar ou reutilizar a base de vendas antes de"
        " abrir o chat ou processar um Excel de perguntas."
    )

    # Exibe o caminho do banco e o estado atual de uso.
    database_url = _db_url()
    engine = create_database_engine(database_url)
    current_status = inspect_existing_data(engine)
    st.caption(f"Banco atual: {database_url}")
    st.json(
        {
            "usable": current_status.get("usable"),
            "row_counts": current_status.get("row_counts"),
        }
    )

    # Controle para evitar recarga desnecessaria quando o banco ja esta valido.
    reuse_existing = st.checkbox(
        "Reutilizar banco existente",
        value=True,
        help="Quando marcado, a carga so ocorre se o banco atual estiver invalido.",
    )
    excel_file = st.file_uploader(
        "Arquivo Excel de vendas",
        type=["xlsx"],
        key="sales_excel_loader",
    )

    # Botao que dispara a carga do Excel para o SQLite.
    if st.button("Carregar dados", type="primary"):
        try:
            if reuse_existing and current_status.get("usable"):
                st.success("Banco atual reutilizado com sucesso.")
                st.json(current_status)
                return

            if excel_file is None:
                st.error("Envie um arquivo Excel para carregar os dados.")
                return

            temp_path = _persist_upload_to_temp(excel_file)
            try:
                result = load_excel_to_sqlite(temp_path, engine)
            finally:
                temp_path.unlink(missing_ok=True)

            st.success("Dados carregados com sucesso.")
            st.json(result)
        except Exception as error:  # noqa: BLE001
            st.error(f"Falha ao carregar dados: {error}")


def _render_questions_excel_processor(sidebar_values: dict[str, str]) -> None:
    """Extrai perguntas de um Excel e gera um Markdown com a lista."""
    st.subheader("Perguntas em Excel")
    st.write(
        "Carregue um arquivo com a lista de perguntas. A tela mostra a lista"
        " extraida e gera um Markdown executando a LLM no fluxo de vendas."
    )

    # Upload e parsing do arquivo de perguntas para a lista de strings.
    questions_file = st.file_uploader(
        "Arquivo Excel de perguntas",
        type=["xlsx"],
        key="questions_excel_loader",
    )
    if questions_file is None:
        return

    question_bytes = questions_file.getvalue()
    try:
        questions = extract_questions_from_excel(question_bytes)
    except Exception as error:  # noqa: BLE001
        st.error(f"Nenhuma pergunta foi encontrada: {error}")
        return

    st.write(f"{len(questions)} pergunta(s) encontradas:")
    st.markdown("\n".join(f"- {question}" for question in questions))

    # Botao que dispara a geracao de Markdown a partir das perguntas.
    if not st.button("Gerar Markdown", type="primary"):
        return

    try:
        result, markdown_path, markdown_text = _generate_questions_markdown(
            sidebar_values,
            questions_file,
        )
        st.success("Markdown gerado com sucesso.")
        st.json(result)
        st.caption(f"Arquivo: {markdown_path}")
        st.download_button(
            "Baixar Markdown",
            data=markdown_text,
            file_name=markdown_path.name,
            mime="text/markdown",
        )
        st.text_area("Pre-visualizacao", value=markdown_text, height=400)
    except Exception as error:  # noqa: BLE001
        st.error(f"Falha ao gerar o Markdown: {error}")


def _generate_questions_markdown(
    sidebar_values: dict[str, str],
    questions_file,
) -> tuple[dict, Path, str]:
    """Executa o fluxo real de LLM e exportacao para um Excel de perguntas."""

    # Constroi configuracao de provider com base nos valores da UI.
    model_config = build_ui_model_config(
        sidebar_values["provider"],
        model=sidebar_values["model"],
        api_key=sidebar_values["api_key"],
        base_url=sidebar_values["base_url"],
    )
    settings = build_ui_settings(model_config)
    application = _build_application(settings)
    service = ApiService(application)

    # Converte o upload em um objeto usado pelo serviço de importacao.
    uploaded = UploadedFileData(
        filename=questions_file.name,
        content=questions_file.getvalue(),
    )
    result = service.run_questions_from_excel(
        uploaded,
        output_format="markdown",
    )

    export = result.get("export") or {}
    markdown_path_value = export.get("output_path")
    if not markdown_path_value:
        raise RuntimeError(
            "O fluxo de perguntas nao retornou um arquivo Markdown."
        )

    markdown_path = Path(markdown_path_value)
    markdown_text = markdown_path.read_text(encoding="utf-8")
    return result, markdown_path, markdown_text


def _render_chat_tab(sidebar_values: dict[str, str]) -> None:
    """Mantém a experiencia de chat com o provider escolhido."""
    st.subheader("Chat")
    st.write("Converse com o bot usando o provider escolhido na lateral.")

    # Inicializa o historico de mensagens no estado da sessao.
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Reexibe o historico de conversa existente na tela.
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("Digite sua pergunta")
    if not prompt:
        return

    # Adiciona a pergunta do usuario ao historico local.
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Processa a pergunta e exibe a resposta do assistente.
    with st.chat_message("assistant"):
        with st.spinner("Processando..."):
            try:
                model_config = build_ui_model_config(
                    sidebar_values["provider"],
                    model=sidebar_values["model"],
                    api_key=sidebar_values["api_key"],
                    base_url=sidebar_values["base_url"],
                )
                settings = build_ui_settings(model_config)
                application = _build_application(settings)
                result = application.processing.process([prompt])
                answer = result["answers"][0]["response_text"]
            except Exception as error:  # noqa: BLE001
                answer = f"Erro ao processar a pergunta: {error}"
            st.markdown(answer)

    # Guarda a resposta no historico para exibicao posterior.
    st.session_state.messages.append({"role": "assistant", "content": answer})


def main() -> None:
    st.set_page_config(page_title="Quick Insights AI Powered", page_icon="chat")
    st.title("Quick Insights AI Powered")
    st.write(
        "Interface visual desacoplada da API. Aqui voce escolhe o provider,"
        " carrega a base de vendas, envia perguntas e gera Markdown a partir"
        " de um Excel de perguntas."
    )

    sidebar_values = _render_provider_sidebar()
    chat_tab, load_tab, questions_tab = st.tabs(
        [
            "Chat",
            "Carregar dados",
            "Excel de perguntas",
        ]
    )

    with chat_tab:
        _render_chat_tab(sidebar_values)
    with load_tab:
        _render_database_loader()
    with questions_tab:
        _render_questions_excel_processor(sidebar_values)


if __name__ == "__main__":
    main()
