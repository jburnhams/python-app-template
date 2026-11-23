# Integration tests

Shared commands, layout, hermetic setup and file-ownership rules are in [`tests/README.md`](../README.md); read that first. This file is owned by integration-test work.

These run the program's boundaries end to end: the command line (in-process and as a subprocess) and the real server on a loopback port, over the real settings file and the SQLite fallback database in the test's home.

## Fixtures (`conftest.py`)

| Fixture | What it gives you |
| --- | --- |
| `cli` | `cli('hello', 'World', '--json')` -> `CliResult(stdout, stderr, code, out)`, **in process** (fast; `strata_python.testing.run_cli`). Raises with the output on a non-zero exit unless `check=False`. |
| `cli_subprocess` | The same through a real `python -m app` process (`run_module`): entry-point smoke test, and anything that must not share this process's state. |
| `server` (in `test_server_api.py`) | The app under uvicorn on a free loopback port (the plugin's `live_app`); its base URL. |

## Coverage

Not gated. `pytest tests/integration -n auto --cov --cov-fail-under=0 --cov-report=term-missing`.

| Area | Tests |
| --- | --- |
| `cli.py` | `test_cli.py`: doctor, the SQLite fallback in the app home, settings with choices, `openapi --check`, real subprocess |
| `server/app.py` | `test_server_api.py`: health, greetings kept over HTTP and seen by the CLI, paging, error bodies, settings, a reload on any screen |
