"""Testes da politica de seguranca SQL."""

import unittest

from app.db.sql_validator import SqlValidator


class SqlValidatorTests(unittest.TestCase):
    """Cobre as principais permissoes e bloqueios da politica SQL."""

    def setUp(self) -> None:
        """Cria um validador novo e sem estado para cada teste."""
        self.validator = SqlValidator()

    def test_accepts_valid_star_schema_query(self) -> None:
        """Uma agregacao com fato e dimensao permitida deve ser aceita."""
        query = """
            SELECT c.UF,
                   SUM(fact.QtdItens * fact.ValorUnitario) AS TotalVendas
            FROM fact
            JOIN dim_cliente AS c ON fact.cdCliente = c.cdCliente
            GROUP BY c.UF
        """

        self.validator.validate(query)

    def test_blocks_non_select_statement(self) -> None:
        """Comandos de escrita devem ser bloqueados antes do banco."""
        with self.assertRaisesRegex(ValueError, "Apenas queries SELECT"):
            self.validator.validate("DELETE FROM fact")

    def test_blocks_unauthorized_table(self) -> None:
        """Tabelas internas ou externas ao modelo nao podem ser consultadas."""
        with self.assertRaisesRegex(ValueError, "nao permitida"):
            self.validator.validate(
                "SELECT * FROM fact JOIN sqlite_master ON 1 = 1"
            )

    def test_requires_fact_table(self) -> None:
        """Consultas analiticas devem partir obrigatoriamente da fato."""
        with self.assertRaisesRegex(ValueError, "tabela fato principal"):
            self.validator.validate("SELECT * FROM dim_cliente")

    def test_blocks_legacy_sales_column(self) -> None:
        """A coluna antiga ValorVenda deve gerar orientacao de calculo."""
        with self.assertRaisesRegex(ValueError, "ValorVenda nao existe"):
            self.validator.validate("SELECT ValorVenda FROM fact")

    def test_blocks_multiple_statements(self) -> None:
        """Uma segunda instrucao deve invalidar toda a entrada."""
        with self.assertRaisesRegex(ValueError, "uma instrucao"):
            self.validator.validate("SELECT * FROM fact; DROP TABLE fact")


if __name__ == "__main__":
    unittest.main()
