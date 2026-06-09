"""Servico de aplicacao para a camada HTTP."""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.api.question_loader import extract_questions_from_excel
from app.bootstrap import Application
from app.db.database import inspect_existing_data
from app.ingestion.excel_to_sqlite import load_excel_to_sqlite


@dataclass(frozen=True)
class UploadedFileData:
    """Representa um upload em memoria independente de framework web."""

    filename: str
    content: bytes

    def read(self) -> bytes:
        """Retorna o conteúdo do arquivo."""
        return self.content


class ApiError(Exception):
    """Exceção estruturada para erros HTTP."""

    def __init__(self, status_code: int, detail: str) -> None:
        """Guarda o código HTTP e a mensagem legível."""
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class ApiService:
    """Encapsula o estado de carga e a execução de perguntas."""

    def __init__(self, application: Application) -> None:
        """Guarda o container da aplicação e o estado da sessão HTTP."""
        self._application = application
        # A sessão HTTP é independente do banco, mas pode herdar um estado
        # pronto caso o arquivo já esteja completamente válido. Isso evita
        # obrigar um /data/load extra quando o SQLite já foi preparado antes
        # da primeira requisição.
        database_status = inspect_existing_data(self._application.engine)
        self._data_ready = bool(database_status.get("usable"))
        self._data_source: str | None = None
        if self._data_ready:
            self._data_source = "database"

    def status(self) -> dict[str, Any]:
        """Expõe o estado atual da fonte de dados."""
        database_status = inspect_existing_data(self._application.engine)
        return {
            "data_ready": self._data_ready,
            "data_source": self._data_source,
            "database": database_status,
        }

    def load_data(
        self,
        *,
        reuse_existing: bool,
        excel_file: UploadedFileData | None,
    ) -> dict[str, Any]:
        """Carrega ou reutiliza os dados do SQLite.

        Args:
            reuse_existing: Indica se o banco atual pode ser reutilizado.
            excel_file: Workbook enviado pelo cliente, quando houver recarga.

        Returns:
            Resposta serializável com origem e relatório de integridade.

        Raises:
            ApiError: Se o cliente pedir recarga sem enviar arquivo.
        """
        # Primeiro tentamos reaproveitar o banco atual; isso evita recarga
        # desnecessária quando o SQLite já está consistente e com o schema
        # completo esperado pelo modelo estrela.
        database_status = inspect_existing_data(self._application.engine)
        if reuse_existing and database_status["usable"]:
            self._data_ready = True
            self._data_source = "database"
            return {
                "ok": True,
                "source": "database",
                "tables": database_status["row_counts"],
                "integrity": database_status.get("integrity"),
            }

        if excel_file is None:
            raise ApiError(
                400,
                "Envie um arquivo Excel para recarregar os dados ou ative "
                "reuse_existing quando o banco atual estiver válido.",
            )

        result = self._load_excel_upload(excel_file)
        self._data_ready = True
        self._data_source = "excel"
        return {
            **result,
            "source": "excel",
        }

    def run_questions(
        self,
        questions: list[str],
        *,
        output_format: str = "none",
    ) -> dict[str, Any]:
        """Processa perguntas e exporta sob demanda."""
        self._ensure_data_ready()
        result = self._application.processing.process(questions)
        export_result = None
        normalized_format = output_format.strip().lower()
        # Exportacao e uma decisao separada do processamento; so ocorre depois
        # que existem insights de vendas e o usuario pediu um formato explicito.
        if (
            normalized_format != "none"
            and result["sales_insight_count"] > 0
        ):
            export_result = self._application.exports.export(normalized_format)
        return {
            **result,
            "export": export_result,
        }

    def run_questions_from_excel(
        self,
        questions_file: UploadedFileData,
        *,
        output_format: str = "none",
    ) -> dict[str, Any]:
        """Extrai perguntas de um workbook e executa o mesmo fluxo JSON."""
        # O loader de perguntas está separado para que o formato Excel seja só
        # uma entrada alternativa, sem duplicar a lógica do processamento.
        questions = extract_questions_from_excel(questions_file.read())
        return self.run_questions(
            questions,
            output_format=output_format,
        )

    def _ensure_data_ready(self) -> None:
        """Bloqueia perguntas antes de uma carga de dados explícita."""
        if self._data_ready:
            return

        # Se a sessao ainda nao foi marcada como pronta, rechecamos o banco
        # para nao bloquear consultas quando o arquivo ja esta valido.
        database_status = inspect_existing_data(self._application.engine)
        if database_status.get("usable"):
            self._data_ready = True
            self._data_source = "database"
            return

        raise ApiError(
            409,
            "Carregue os dados primeiro usando a rota /data/load.",
        )

    def _load_excel_upload(self, excel_file: UploadedFileData) -> dict[str, Any]:
        """Persiste um upload temporário e reaproveita o loader existente."""
        # O arquivo sobe para um caminho temporário apenas para reutilizar o
        # loader de ingestão que já trabalha com Path e transação SQLAlchemy.
        suffix = Path(excel_file.filename or "upload.xlsx").suffix or ".xlsx"
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=suffix,
            ) as temp_file:
                temp_file.write(excel_file.read())
                temp_path = Path(temp_file.name)
            return load_excel_to_sqlite(
                temp_path,
                self._application.engine,
            )
        finally:
            if temp_path and temp_path.exists():
                temp_path.unlink(missing_ok=True)

