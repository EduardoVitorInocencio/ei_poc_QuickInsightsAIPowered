"""Teste de integracao da carga com o workbook real do projeto."""

import tempfile
import unittest
from pathlib import Path

from sqlalchemy import inspect

from app.db.database import create_database_engine, inspect_existing_data
from app.domain.sales_model import ALLOWED_TABLES
from app.ingestion.excel_to_sqlite import load_excel_to_sqlite


class IngestionIntegrationTests(unittest.TestCase):
    """Exercita Excel, transformacoes e SQLite em conjunto."""

    def test_loads_complete_star_schema(self) -> None:
        """O workbook real deve gerar todas as tabelas com integridade valida."""
        source = Path("app/data/sales.xlsx")
        if not source.exists():
            self.skipTest("Workbook de integracao nao encontrado.")

        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "database.db"
            engine = create_database_engine(f"sqlite:///{database_path}")
            try:
                result = load_excel_to_sqlite(source, engine)
                inspector = inspect(engine)

                self.assertTrue(result["ok"])
                self.assertEqual(
                    set(inspector.get_table_names()),
                    set(ALLOWED_TABLES),
                )
                self.assertTrue(all(result["tables"].values()))
                self.assertTrue(
                    all(
                        count == 0
                        for count in result["integrity"][
                            "orphan_relationships"
                        ].values()
                    )
                )
                database_status = inspect_existing_data(engine)
                self.assertTrue(database_status["usable"])
                self.assertEqual(
                    set(database_status["row_counts"]),
                    set(ALLOWED_TABLES),
                )
            finally:
                engine.dispose()


if __name__ == "__main__":
    unittest.main()
