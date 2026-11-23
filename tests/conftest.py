"""Fixtures both suites share. Most come from the strata-python pytest plugin, configured in pyproject.toml: a fresh
home and settings folder for every test (`isolated_env`), no outbound network, `http_server` and `live_app` for real
HTTP, the `fake_*` last-resort doubles, the `integration` marker under tests/integration, and, because the app
declares its database (`[tool.strata-db]`), `db_session`, `db_engine`, `db_url` and `db_env` on a freshly migrated
SQLite copy (or a throwaway Postgres with `--pg`)."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(db_env: str) -> Iterator[TestClient]:
    """The HTTP API on a fresh migrated test database. Used as a context manager so the server's lifespan runs, as
    under uvicorn: the engine is disposed when the test ends (a SQLite file left open cannot be removed on Windows)."""
    from app.server.app import create_app

    with TestClient(create_app()) as c:
        yield c
