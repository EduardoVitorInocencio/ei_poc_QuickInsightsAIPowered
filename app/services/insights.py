"""Servicos de leitura segura do modelo estrela.

O agente nunca recebe a engine diretamente. Esta camada valida o SQL, executa
a consulta e preserva o resultado completo para uma exportacao posterior.
"""

from typing import Any

import pandas as pd
from sqlalchemy import Engine, text

from app.db.sql_validator import SqlValidator
from app.domain.sales_model import get_schema_contract
from app.services.query_results import QueryResultStore


class InsightsService:
    """Expoe schema e consultas de leitura para o SalesAgent."""

    def __init__(
        self,
        engine: Engine,
        result_store: QueryResultStore,
        validator: SqlValidator | None = None,
        preview_limit: int = 20,
    ) -> None:
        """Configura as dependencias usadas nas consultas.

        Args:
            engine: Engine conectada ao banco de vendas.
            result_store: Repositorio dos DataFrames consultados.
            validator: Politica SQL opcional; usa ``SqlValidator`` por padrao.
            preview_limit: Maximo de linhas devolvidas ao LLM como amostra.
        """
        self._engine = engine
        self._result_store = result_store
        self._validator = validator or SqlValidator()
        self._preview_limit = preview_limit

    def inspect_schema(self) -> dict[str, Any]:
        """Retorna tabelas, colunas, relacionamentos e regra de vendas."""
        return get_schema_contract()

    def run_query(self, query: str) -> pd.DataFrame:
        """Valida e executa uma consulta SELECT.

        Args:
            query: SQL produzido pelo SalesAgent.

        Returns:
            DataFrame com o resultado integral do SQLite.

        Raises:
            ValueError: Se o SQL violar a politica de seguranca.
            SQLAlchemyError: Se a execucao no banco falhar.
        """
        self._validator.validate(query)
        with self._engine.connect() as connection:
            return pd.read_sql_query(text(query), connection)

    def run_sql_tool(self, sql: str) -> dict[str, Any]:
        """Adapta uma consulta ao contrato serializavel da tool.

        Args:
            sql: Consulta SELECT a validar e executar.

        Returns:
            Status, referencia ``result_id``, colunas, contagem e amostra.
            O DataFrame completo permanece no repositorio.
        """
        dataframe = self.run_query(sql)
        result_id = self._result_store.save(dataframe)
        return {
            "ok": True,
            "result_id": result_id,
            "row_count": int(len(dataframe)),
            "columns": list(dataframe.columns),
            "preview_rows": dataframe.head(self._preview_limit).to_dict(
                orient="records"
            ),
        }
