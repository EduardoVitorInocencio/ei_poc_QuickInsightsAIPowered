"""Fábrica da camada HTTP baseada em FastAPI."""

from __future__ import annotations

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile

from app.api.schemas import LoadDataResponse, QuestionsRequest, QuestionsResponse
from app.api.service import ApiError, ApiService, UploadedFileData
from app.bootstrap import Application, create_application


def create_api_app(application: Application | None = None) -> FastAPI:
    """Cria a aplicação FastAPI com dependências injetáveis para testes."""
    resolved_application = application or create_application()
    api_service = ApiService(resolved_application)
    app = FastAPI(title="Quick Insights API")
    app.state.application = resolved_application
    app.state.api_service = api_service

    def get_service() -> ApiService:
        """Fornece o serviço por requisição sem acoplar as rotas."""
        return app.state.api_service

    @app.get("/health")
    def health() -> dict[str, bool]:
        """Retorna um status mínimo para monitoramento."""
        return {"ok": True}

    @app.get("/data/status")
    def data_status(
        service: ApiService = Depends(get_service),
    ) -> dict:
        """Exibe o estado atual da fonte de dados."""
        return service.status()

    @app.post("/data/load", response_model=LoadDataResponse)
    async def load_data(
        reuse_existing: bool = Form(True),
        excel_file: UploadFile | None = File(default=None),
        service: ApiService = Depends(get_service),
    ) -> dict:
        """Carrega um workbook novo ou reutiliza o banco existente."""
        try:
            # FastAPI entrega o upload como stream; convertemos para um wrapper
            # simples para manter o serviço independente do framework.
            uploaded = None
            if excel_file is not None:
                # `filename` vem do upload HTTP e é usado apenas para inferir a
                # extensao temporaria; o conteúdo segue intacto para o loader.
                uploaded = UploadedFileData(
                    filename=excel_file.filename or "upload.xlsx",
                    content=await excel_file.read(),
                )
            # `reuse_existing` é preenchido via Form porque a rota também pode
            # receber arquivo multipart, e FastAPI separa bem esses campos.
            return service.load_data(
                reuse_existing=reuse_existing,
                excel_file=uploaded,
            )
        except ApiError as error:
            raise HTTPException(
                status_code=error.status_code,
                detail=error.detail,
            ) from error

    @app.post("/questions", response_model=QuestionsResponse)
    def run_questions(
        payload: QuestionsRequest,
        service: ApiService = Depends(get_service),
    ) -> dict:
        """Processa uma lista de perguntas enviadas em JSON."""
        try:
            # A rota apenas valida o contrato HTTP; a orquestracao fica no
            # service para ser compartilhada com a CLI.
            # `payload.questions` é a lista enviada pelo cliente e
            # `payload.output_format` controla a exportacao opcional.
            return service.run_questions(
                payload.questions,
                output_format=payload.output_format,
            )
        except ApiError as error:
            raise HTTPException(
                status_code=error.status_code,
                detail=error.detail,
            ) from error

    @app.post("/questions/excel", response_model=QuestionsResponse)
    async def run_questions_from_excel(
        output_format: str = Form("none"),
        questions_file: UploadFile = File(...),
        service: ApiService = Depends(get_service),
    ) -> dict:
        """Processa perguntas carregadas em workbook."""
        try:
            # O mesmo pipeline do JSON e reaproveitado aqui depois da leitura
            # do arquivo enviado pelo cliente.
            uploaded = UploadedFileData(
                filename=questions_file.filename or "questions.xlsx",
                content=await questions_file.read(),
            )
            # `output_format` também vem de form-data para manter a rota
            # compatível com upload de arquivo e escolha de exportação.
            return service.run_questions_from_excel(
                uploaded,
                output_format=output_format,
            )
        except ApiError as error:
            raise HTTPException(
                status_code=error.status_code,
                detail=error.detail,
            ) from error

    return app


app = create_api_app()

