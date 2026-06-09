"""Testes de roteamento, processamento e exportacao."""

import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from pptx import Presentation

from app.services.exports import InsightExportService
from app.services.markdown import MarkdownService
from app.services.powerpoint import PowerPointService
from app.services.query_results import QueryResultStore
from app.services.question_processing import (
    QuestionProcessingService,
    classify_question,
)
from app.services.sales_insights import SalesInsightStore


class FakeSalesAgent:
    """Produz um insight previsivel sem chamar a OpenAI."""

    def __init__(self, results, insights) -> None:
        """Recebe os mesmos repositorios usados pelo processamento real."""
        self._results = results
        self._insights = insights

    def run(self, question):
        """Armazena dados e insight suficientes para testar exportacao."""
        result_id = self._results.save(
            pd.DataFrame({"Categoria": ["A"], "Valor": [100]})
        )
        insight = self._insights.add(
            question=question,
            result_id=result_id,
            titulo="Vendas por categoria",
            headline="A categoria A totalizou 100.",
            analise="A categoria A representa o resultado consultado.",
        )
        return {
            "response_text": insight["headline"],
            "insight_id": insight["insight_id"],
        }


class FakeExternalAgent:
    """Representa um agente externo que retorna somente texto."""

    def run(self, question):
        """Retorna uma resposta sem criar resultado ou insight exportavel."""
        return {"response_text": f"Resposta externa para {question}"}


class ProcessingAndExportTests(unittest.TestCase):
    """Valida roteamento, ausencia de exportacao automatica e formatos."""

    def test_routes_weather_to_external_agent(self) -> None:
        """Termos de clima devem ser externos e vendas devem permanecer locais."""
        self.assertEqual(
            classify_question("Como esta o clima em Recife?"),
            "external",
        )
        self.assertEqual(
            classify_question("Total de vendas por UF"),
            "sales",
        )

    def test_processes_mixed_questions_without_creating_output(self) -> None:
        """Um lote misto deve produzir apenas um insight exportavel de vendas."""
        results = QueryResultStore()
        insights = SalesInsightStore(results)
        service = QuestionProcessingService(
            sales_agent=FakeSalesAgent(results, insights),
            external_agent=FakeExternalAgent(),
            result_store=results,
            insight_store=insights,
        )

        result = service.process(
            ["Total de vendas", "Clima em Recife"]
        )

        self.assertEqual(result["sales_insight_count"], 1)
        self.assertEqual(
            [answer["agent"] for answer in result["answers"]],
            ["sales", "external"],
        )

    def test_exports_sales_insights_to_pptx_and_markdown(self) -> None:
        """A exportacao explicita deve criar os dois formatos suportados."""
        with tempfile.TemporaryDirectory() as temp_dir:
            results = QueryResultStore()
            insights = SalesInsightStore(results)
            FakeSalesAgent(results, insights).run("Total de vendas")
            powerpoint = PowerPointService(
                Path(temp_dir) / "insights.pptx",
                results,
            )
            markdown = MarkdownService(
                Path(temp_dir) / "insights.md",
                results,
            )
            exports = InsightExportService(
                insight_store=insights,
                powerpoint=powerpoint,
                markdown=markdown,
            )

            with patch("app.services.powerpoint.datetime") as pptx_datetime, patch(
                "app.services.markdown.datetime"
            ) as markdown_datetime:
                fixed_datetime = datetime(2026, 6, 7, 2, 54, 13)
                pptx_datetime.now.return_value = fixed_datetime
                markdown_datetime.now.return_value = fixed_datetime
                pptx_result = exports.export("pptx")
                markdown_result = exports.export("markdown")

            self.assertEqual(
                Path(pptx_result["output_path"]).name,
                "insights_20260607_025413.pptx",
            )
            self.assertEqual(
                Path(markdown_result["output_path"]).name,
                "insights_20260607_025413.md",
            )
            presentation = Presentation(pptx_result["output_path"])
            self.assertEqual(len(presentation.slides), 1)
            markdown_text = Path(
                markdown_result["output_path"]
            ).read_text(encoding="utf-8")
            self.assertIn("GENERATE BY AI", markdown_text)
            self.assertIn("Gerado em: 07/06/2026 02:54:13", markdown_text)
            self.assertIn("### Analise", markdown_text)
            self.assertIn("| Categoria | Valor |", markdown_text)


if __name__ == "__main__":
    unittest.main()
