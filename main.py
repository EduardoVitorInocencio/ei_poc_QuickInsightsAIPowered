"""Ponto de entrada da interface de linha de comando."""

from app.cli.runner import run_cli


def main() -> None:
    """Inicia a CLI modular da aplicacao."""
    run_cli()


if __name__ == "__main__":
    main()
