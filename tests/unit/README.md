# Unit tests

Shared commands, layout, hermetic setup and file-ownership rules are in [`tests/README.md`](../README.md); read that first. This file is owned by unit-test work.

Fast and isolated: synthetic data, a migrated SQLite copy per test for the records; no external services, no network. `pytest tests/unit --cov` is what CI gates on (`fail_under` in `pyproject.toml`).

## Where things are tested

| Module | Tests | Coverage | Status | Notes |
| --- | --- | --- | --- | --- |
| `settings.py` | `test_settings.py` | 100% | done | greeting and style defaults, environment overrides, save/reset, the choices |
| `greet.py` | `test_greet.py` | 100% | done | formatting, length limits and their sentences, the style, hypothesis properties, keeping and clearing, ids never reused, cursor paging after a removed cursor, times answered in UTC |
| `models.py`, `migrations/` | `test_database.py` | 100% | done | strata-python's standard tests: migrations up and down, schema matches the models |
| `system.py` | `test_system.py` | 100% | done | folder sizes (files that vanish mid-walk) |
| `cli.py`, `db.py` | `test_cli.py` | 100% | done | doctor, hello (kept and not), messages, set with choices, serve delegation, openapi |
| `server/app.py` | `test_server.py` | 100% | done | the committed `openapi.json`, landing/static index with its relative `<base>`, hello, send, clear, paging, removing one, error bodies, system, settings with choices, `main` |
