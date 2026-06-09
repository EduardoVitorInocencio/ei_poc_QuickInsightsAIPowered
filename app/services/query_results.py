"""Repositorio em memoria para resultados de consultas.

O LLM recebe somente uma amostra serializavel. Exportadores recuperam o
DataFrame completo por ``result_id``, evitando que o modelo reconstrua dados.
"""

from uuid import uuid4

import pandas as pd


class QueryResultStore:
    """Mantem copias defensivas dos DataFrames durante uma execucao."""

    def __init__(self) -> None:
        """Inicializa um repositorio vazio."""
        self._results: dict[str, pd.DataFrame] = {}

    def save(self, dataframe: pd.DataFrame) -> str:
        """Armazena um resultado e cria uma referencia opaca.

        Args:
            dataframe: Resultado integral de uma consulta validada.

        Returns:
            Identificador unico usado por insights e exportadores.
        """
        result_id = uuid4().hex
        self._results[result_id] = dataframe.copy()
        return result_id

    def get(self, result_id: str) -> pd.DataFrame:
        """Recupera um resultado sem expor a instancia interna.

        Args:
            result_id: Identificador retornado por :meth:`save`.

        Returns:
            Copia do DataFrame associado.

        Raises:
            ValueError: Se o identificador nao existir no lote atual.
        """
        dataframe = self._results.get(result_id)
        if dataframe is None:
            raise ValueError(f"Resultado SQL desconhecido: {result_id}")
        return dataframe.copy()

    def clear(self) -> None:
        """Remove resultados anteriores antes de iniciar um novo lote."""
        self._results.clear()
