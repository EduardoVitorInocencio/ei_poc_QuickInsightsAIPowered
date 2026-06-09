"""Raiz de composicao da aplicacao.

Somente este modulo instancia infraestrutura concreta e conecta handlers aos
agentes. Essa centralizacao facilita testes e inclusao de novas interfaces.
"""

from dataclasses import dataclass

from sqlalchemy import Engine

from app.agent.external_tools_agent import ExternalToolsAgent
from app.agent.sales_agent import SalesAgent
from app.llm.tools import ToolRegistry
from app.config import Settings
from app.db.database import create_database_engine
from app.llm.providers import create_openai_client
from app.services.exports import InsightExportService
from app.services.insights import InsightsService
from app.services.markdown import MarkdownService
from app.services.powerpoint import PowerPointService
from app.services.query_results import QueryResultStore
from app.services.question_processing import QuestionProcessingService
from app.services.sales_insights import SalesInsightStore
from app.services.weather import WeatherService


@dataclass(frozen=True)
class Application:
    """Container imutavel das capacidades usadas pela CLI ou futuras APIs."""

    settings: Settings
    engine: Engine
    insights: InsightsService
    weather: WeatherService
    sales_agent: SalesAgent
    external_agent: ExternalToolsAgent
    processing: QuestionProcessingService
    exports: InsightExportService


def create_application(settings: Settings | None = None) -> Application:
    """Monta o grafo completo de dependencias.

    Args:
        settings: Configuracao explicita; quando ausente, le o ambiente.

    Returns:
        Container com engine, agentes, processamento e exportacao.

    Raises:
        ValueError: Se a configuracao de algum provedor estiver incompleta.
    """
    resolved_settings = settings or Settings.from_env()
    engine = create_database_engine(resolved_settings.database_url)
    result_store = QueryResultStore()
    insight_store = SalesInsightStore(result_store)

    insights = InsightsService(engine, result_store)
    weather = WeatherService()
    # powerpoint = PowerPointService(
    #     resolved_settings.pptx_output_path,
    #     result_store,
    # )
    markdown = MarkdownService(
        resolved_settings.markdown_output_path,
        result_store,
    )

    # Registros separados impedem acesso cruzado entre os agentes.
    sales_registry = ToolRegistry(
        {
            "inspect_sales_schema": lambda _: insights.inspect_schema(),
            "run_sql_query": lambda args: insights.run_sql_tool(args["sql"]),
            "submit_sales_insight": lambda args: insight_store.add(
                question=args["question"],
                result_id=args["result_id"],
                titulo=args["titulo"],
                headline=args["headline"],
                analise=args["analise"],
            ),
        }
    )
    external_registry = ToolRegistry(
        {
            "get_current_weather": lambda args: weather.get_current_weather(
                args["city"],
                args.get("country_code"),
            ),
        }
    )
    # Cada agente pode usar provedor, endpoint, credencial e modelo distintos.
    sales_client = create_openai_client(resolved_settings.sales_model)
    external_client = create_openai_client(resolved_settings.external_model)
    sales_agent = SalesAgent(
        client=sales_client,
        model=resolved_settings.sales_model.model,
        tool_registry=sales_registry,
    )
    external_agent = ExternalToolsAgent(
        client=external_client,
        model=resolved_settings.external_model.model,
        tool_registry=external_registry,
    )
    processing = QuestionProcessingService(
        sales_agent=sales_agent,
        external_agent=external_agent,
        result_store=result_store,
        insight_store=insight_store,
    )
    exports = InsightExportService(
        insight_store=insight_store,
        powerpoint=powerpoint,
        markdown=markdown,
    )
    return Application(
        settings=resolved_settings,
        engine=engine,
        insights=insights,
        weather=weather,
        sales_agent=sales_agent,
        external_agent=external_agent,
        processing=processing,
        exports=exports,
    )
