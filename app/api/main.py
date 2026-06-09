"""Ponto de entrada da API HTTP."""

from __future__ import annotations

import uvicorn

from app.api.app import app


def main() -> None:
    """Inicia o servidor FastAPI com Uvicorn."""
    uvicorn.run("app.api.main:app", host="127.0.0.1", port=8000, reload=False)


if __name__ == "__main__":
    main()

