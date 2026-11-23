# Repository Guidelines

This file is for people and coding agents (`CLAUDE.md` imports it). It is the basis for the same file in every app made from [python-app-template](https://github.com/jburnhams/python-app-template): when you start an app from the template, keep the sections, replace the descriptions of the sample code with your app's, and keep what is true for every app unchanged so the template can be updated into it later.

## What this is

A Python backend (FastAPI + CLI) and a React frontend built on [strata-react](https://github.com/jburnhams/strata-react) (TypeScript + Vite + Tailwind CSS v4), extracted from `strata-360` and `strata-stills`. Hermetic unit and integration test suites, Storybook, screenshot tests, coverage ratchets and multi-OS GitHub Actions CI. The sample app (greetings kept in a database, a paged log, settings, a status page) exists to show the patterns; replace it, keep the shape.

## Rules for every change

1. **Run `scripts/check` before every commit** (`--fast` skips the tests, `--fix` applies ruff). CI runs the same steps. Never skip, disable or quarantine a test or a check to get green.
2. **Keep the docs and the changelog in the same commit as the change**: add an entry to `CHANGELOG.md` (newest day first; a bold one-line title, what was asked, then bullets naming each file touched and what changed; say **new** for new files, and call out corrections to earlier claims), and update the README, this file and `docs/` where they stop being true.
3. **Write the why**: dense code with comments that say why, not what. Facts, commands, paths and decisions; link instead of repeating what another doc or upstream page already says.
4. **No secrets, no machine-specific details** in this repo. Say where a secret lives (an environment variable name, a password manager), never its value. Hostnames, addresses, user names, local paths and the owner's infrastructure belong in the owner's private docs, not here: examples use placeholders (`/home/ada/...`, `<port>`).
5. **Types are not optional**: everything in `src/` is fully annotated and passes `pyright` (strict) and `ty`; a new file is strict from its first commit. Style is `ruff format` at line length 120, not by hand.
6. **Tests come with the change**: unit tests for logic, integration tests for the CLI and HTTP API, web tests and stories for screens. Coverage floors only ratchet up.
7. **Say what you ran**: in the PR or the final message, list the commands you ran and their results, and name what you could not run.

## Layout and conventions

- Shared server code is the [strata-python](https://github.com/jburnhams/strata-python) library (read its README, "Move an app onto it", for every module): `Settings`, `web.base_app`/`add_error_handlers`/`add_system`/`add_web`/`serve`, `contracts` (`ApiModel`, `Page`, `SystemInfo`), the `doctor`/`set`/`serve`/`openapi` CLI commands, `db` (models base, migrations, `add_database`/`DbSession`), `files`, `http`, `media`, `tasks`, `oslib`, the pytest plugin, `strata-check` and `strata-public-check`. Do not copy those modules into the app; if the library lacks something every app needs, change it there. This repo declares its settings (`settings.py`), its records (`models.py`, `migrations/`, `strata-db.toml`, `db.py`), its business logic (`greet.py`), its routes (`server/app.py`) and its commands (`cli.py`), and nothing else.
- The API is typed end to end: routes return `contracts.ApiModel` subclasses (or a shared contract such as `Page[...]`), `./app openapi` writes `web/openapi.json`, and `cd web && npm run api-types` writes `web/src/api.generated.ts` from it. Commit both after any route or model change; a unit test (`assert_openapi_current`) and CI (`npm run api-types:check`) fail a stale one. Errors are raised, not caught in routes: a `ValueError` answers 400 and a `KeyError` 404 with the sentence as `detail` (`add_error_handlers`), and the web app shows that sentence.
- Python application code lives in `src/app/` (the package name is changed per app, see the README); the React web app lives in `web/src/` and builds into `src/app/server/static/`, which `app serve` serves at every non-API path.
- The web app follows strata-react's rules (its `CLAUDE.md`, "Building an app on Strata"): only Strata components and theme roles (no raw palette colours, arbitrary values or `dark:` overrides), every remote read `useLoad`/`useInfiniteLoad` → `DataView`/`InfiniteList` with skeleton and empty state, one filled button per view at a time (the `BulkBar` action takes it while rows are chosen), reversible removals through `useUndoable`, URL state for sort/tab, numbers and dates through `format`. Each screen in `web/src/screens/` opens with its one question. Something Strata lacks is raised as an issue on strata-react, not hand-built here.
- Cross-platform (Linux, macOS, Windows): OS differences (file locks, process liveness and termination, priority, how to start the CLI) live in `strata_python.oslib`; do not import `fcntl` or call `os.kill(pid, 0)` elsewhere (on Windows that terminates the process).
- Reverse-proxy support: the server gives every page a relative `<base href>` back to its root (`web.add_web`), the web build uses relative asset paths (`base: './'` in `vite.config.ts`), and strata-react's `appBase()` reads the page's base for React Router's `basename` (`main.tsx`). Every request goes through `api` (`web/src/api.ts`, `createTypedApi`), which puts the base first; an `<img src>` or a download link uses `api.url(path)`; in-app links are router paths (`ButtonLink`, `TextLink`).
- Docs live in `docs/`: `overview.md` (design brief), `implementation-plan.md` (milestones and next steps), `progress.md` (log of findings and decisions), `deploying.md` (running it as a service; keep it generic), `prompts/` (unattended agent prompts for backend unit, integration and web tests).

## Python tooling (uv)

- `uv sync` builds `.venv` from the committed `uv.lock`; `uv run <cmd>` runs inside it; `uv add <pkg>` / `uv add --group dev <pkg>` change dependencies (commit `pyproject.toml` and `uv.lock` together). Version, dependencies, the `app` entry point and every tool's configuration are in `pyproject.toml`; the version lives only there (`app.__version__` reads it back). `./app` and `app.cmd` are thin wrappers for `uv run app`.
- `scripts/check` is `uv run --locked strata-check` (from strata-python): `uv lock --check`, `ruff check`, `ruff format --check`, `pyright` and `ty`, then the unit tests with coverage. Options such as the checked paths are in `[tool.strata-check]` in `pyproject.toml`.
- strata-python comes from PyPI as `strata-python[db]>=0.2.6,<0.3` (while 0.x a minor release may break, so the cap is the next minor) and brings FastAPI, uvicorn, pydantic and SQLAlchemy; the dev group is `strata-python[dev]` (ruff, pyright, ty and the pytest plugins at the versions `strata-check` expects) plus hypothesis and diff-cover. Do not list what it brings. Dependabot raises one grouped uv PR a week: read strata-python's CHANGELOG (each breaking line ends with the migration) before merging. To try an unreleased commit, add `[tool.uv.sources] strata-python = { git = "...", rev = "<sha>" }` for the moment.
- `uv run pytest tests/unit --cov` runs the unit suite with coverage (random order via pytest-randomly; `-n auto` runs in parallel; `diff-cover` checks the lines a change touches). `uv run pytest tests/integration -n auto` runs the integration suite.
- `uv run app doctor` checks the environment; `uv run app hello [name] [--save]` prints (and keeps) a greeting; `uv run app serve` runs the web server on port 8360; `uv run app openapi [--check]` writes (or checks) `web/openapi.json`.
- Python coverage is calculated from the unit suite only (`fail_under` in `pyproject.toml`).
- Style: pytest style tests (`def test_...` with `assert`; use `monkeypatch`/`tmp_path` instead of patching globals by hand).

## Testing policy

Prefer real code over mocks. A test that runs the real thing finds the bugs that matter; a mock only proves the code agrees with the test.

- **Real by default**: real HTTP requests (against a real local server: the `http_server` fixture from the strata-python plugin, or its `live_app` fixture to run the app itself on a loopback port), real embedded databases (SQLite, or the Postgres service container, via the database project's `db_session` fixtures; see Database), real files in `tmp_path`, real subprocesses. In the web app that means MSW answering real `fetch` calls, never a stubbed `fetch` or a mocked module.
- **Mocks and fakes are the exception**: use one only for a true external (a paid or remote service, hardware, the clock) and only in quick unit tests that cover many cases where speed is the point. Never mock your own modules or the database. Even then, keep one test of the same path against the real thing.
- **Install what the tests need**: CI runners can have software installed. If code calls `ffmpeg`, install it (locally and in the workflow) and run it; do not mock it or skip when it is missing. Add the install to the workflow and say so in the README.
- **No silent skips, no swallowed errors**: a test must not pass or skip because something was missing or an exception was caught. `pytest.importorskip` is banned (ruff). A test is skipped only deliberately: a marker or `skipif` with a **reason** and an explicit switch, for example a 12 GB model that is too large for CI is `@pytest.mark.skipif(not os.environ.get("RUN_LARGE_MODEL"), reason="needs the 12 GB model; set RUN_LARGE_MODEL=1")` and runs on the machine that has it. Skips show in the summary (`-ra`); any new skip is mentioned in the PR.
- **Where tests need a lot of machine** (GPU, large models), mark them (`slow`, `gpu`), run them where that machine exists, and keep the marker documented in `tests/README.md`.

## Python tests

- Tests live under `tests/`, grouped by type:
  - `tests/unit/`: fast, isolated tests of logic, the database through `db_session` (a migrated SQLite copy per test, Postgres with `--pg`) and the HTTP API through the `client` fixture. No external processes or network.
  - `tests/integration/`: end-to-end tests that run the CLI (in-process and as a subprocess, `strata_python.testing.run_cli`/`run_module`) and the real server on a loopback port (`live_app`), over the real settings file and the SQLite fallback database.
  - `tests/utils/`: the app's own helpers, when it has any (on `pythonpath`). The strata-python pytest plugin (configured by `strata_env_prefix` and `strata_tuning_vars` in `pyproject.toml`) makes every suite hermetic (isolated home, no network) and provides `http_server`, `live_app`, the `fake_*` last-resort doubles and the `db_*` fixtures; `tests/conftest.py` holds the `client` fixture.
- Read `tests/README.md` before writing any Python test: fixtures, conventions, file-ownership rules and the per-module coverage ledger.

## Web

- Web tests live in `web/tests/{unit,integration,utils}` (vitest; unit runs in node, integration in jsdom through `renderRoutes` from `strata-react/testing`). Backend calls are answered by msw from `web/src/mocks/handlers.ts` (every endpoint the app calls needs a handler there; the same handlers serve Storybook and the visual suite); read `web/tests/README.md` before writing any. Stories live in `web/stories/`; visual baselines in `web/tests/visual/baselines/`.
- Commands, from `web/`: `npm install`, `npm run dev` (proxies `/api` to `app serve` on 8360), `npm run build` (writes into `src/app/server/static/`), `npm run lint` (Biome, then oxlint with type information: the leaflet-node stack; `npm run format` applies Biome's formatting), `npm run typecheck` (TypeScript 7's `tsc`; the package named `typescript` is the TypeScript 6 API, which openapi-typescript and Storybook need), `npm run api-types` / `api-types:check`, `npm run test:unit` (node), `npm run test:integration` (jsdom + msw), `npm run test:coverage:gate` (unit + integration together, what CI gates on: floors in `web/coverage-floor.json`, read by `web/vitest.gate.config.ts`), `npm run test:coverage` (unit only, informational), `npm run test:coverage:all` (unit + integration, no gate), `npm run storybook`, `npm run build-storybook`, `npm run test:visual` (builds the app and Storybook, then `strata-visual` compares every story and route state, light and dark, with the baselines), `npm run test:visual:update` (look at the diffs in `tests/visual/output/` first, say in the PR which baselines changed and why). Node 26 (`.nvmrc`). The web floors only ratchet up.

## Database

The sample keeps its greetings in a database through `strata_python.db` (read strata-python's README, "Database", and do not restate it here). The rules that matter to an agent:

- The declaration is `src/app/strata-db.toml` (pointed to from `[tool.strata-db] file = ...` in `pyproject.toml`), with the Alembic revisions in `src/app/migrations/` beside it, so both ship in the wheel and `Project.load(__file__)` finds them from an installed app.
- Where the data is: `STRATA_DB_URL` or `APP_DATABASE_URL` (the shared Postgres in a deployment: one database, one schema per app, never a database per app, since Postgres cannot join across databases), else a SQLite file in the app's home (`~/.app/app.db`). The server opens it on the first request that needs it (`add_database`), routes take a `DbSession`, and the CLI uses `db.session()`. Never put a URL with credentials in the repo.
- Models (`src/app/models.py`) are typed records on a base class written out (`class Base(MappedAsDataclass, DeclarativeBase)` with the shared `NAMING_CONVENTION`), portable (generic types, a `server_default` on a new NOT NULL column) unless the app really needs Postgres; then `engine = "postgres"` in the declaration.
- Every model change comes with a reviewed revision (`uv run strata-db revision -m "..."`; autogenerate reads a rename as drop + add). CI runs `strata-db check` and the unit tests on Postgres too (`pytest --pg`). Tests use the plugin's `db_session`/`db_env` fixtures and `strata_python.db.testing`'s standard tests, never a mocked connection or `create_all()`.
- For data that is personal (photos, people, children) keep it out of git and behind a login.
- If strata-python lacks something an app needs, raise it there instead of working around it here.

## CI

`.github/workflows/unit.yml` (`strata-check --fast`, `strata-db check` and `strata-public-check` on the tree and the wheel once, then unit tests with coverage on Linux Python 3.11-3.13, macOS and Windows, and once on Postgres; web lint, typecheck, generated-types check, coverage gate, build, Storybook build; visual regression) and `integration.yml` (integration tests on Linux, macOS and Windows, web component tests, a weekly dependency audit, weekly and on demand). `update-visual-baselines.yml` (manual) rewrites the visual baselines on the CI runner for a branch, which is how a Dependabot browser or icon bump gets new baselines. `.github/dependabot.yml` keeps uv, npm and Actions dependencies current, one grouped PR per ecosystem. CI installs with `uv sync --locked`, so a stale lockfile fails the build.

## Before you say it is done

`scripts/check` passes, the integration suite passes, the web checks you touched pass (`lint`, `typecheck`, `api-types:check`, `test:coverage:gate`, `test:visual` for any UI change), the changelog has its entry, and the docs match the code. Report the commands and their results.
