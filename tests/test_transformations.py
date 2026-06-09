"""Testes das transformacoes de ingestao."""

import unittest

import pandas as pd

from app.ingestion.transformations import (
    normalize_columns,
    prepare_sheet,
)


class TransformationTests(unittest.TestCase):
    """Valida transformacoes puras aplicadas aos DataFrames do Excel."""

    def test_normalize_columns_removes_accents_and_spaces(self) -> None:
        """Cabecalhos devem se tornar identificadores SQL consistentes."""
        dataframe = pd.DataFrame(columns=["Razão Social", "Peso Liquido"])

        normalized = normalize_columns(dataframe)

        self.assertEqual(
            list(normalized.columns),
            ["RazaoSocial", "PesoLiquido"],
        )

    def test_prepare_fact_converts_types_and_column_names(self) -> None:
        """A fato deve normalizar cabecalhos, chaves, datas e numeros."""
        dataframe = pd.DataFrame(
            {
                "DataEmissao": ["2025-01-01"],
                "DataVencimento": ["2025-01-10"],
                "NFe": [100.0],
                "cdCliente": [1.0],
                "cdVendedor": [2.0],
                "cdProduto": [3.0],
                "QtdItens": ["2"],
                "ValorUnitario": ["10.50"],
                "Peso Liquido": ["1.25"],
            }
        )

        prepared = prepare_sheet("fact", dataframe)

        self.assertEqual(prepared.loc[0, "cdCliente"], "1")
        self.assertEqual(prepared.loc[0, "DataEmissao"], "2025-01-01")
        self.assertEqual(prepared.loc[0, "QtdItens"], 2)
        self.assertEqual(prepared.loc[0, "PesoLiquido"], 1.25)

    def test_prepare_sheet_reports_missing_columns(self) -> None:
        """Uma aba incompleta deve informar claramente a violacao de schema."""
        with self.assertRaisesRegex(ValueError, "colunas obrigatorias"):
            prepare_sheet("Cliente", pd.DataFrame({"cdCliente": [1]}))


if __name__ == "__main__":
    unittest.main()
