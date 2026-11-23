# Changelog

Newest first, grouped by day. One entry per change, in the same commit or PR as the change.

## 2026-11-23

**Latest strata-python and strata-react, every dependency current, the template as the example app (branch `claude/project-thread-61o806`)**
Jonathan asked for the template to use the latest strata-python and strata-react, for every other dependency to be at its latest, and for it to adopt the working practices that make it a good starting point for new apps. That meant taking strata-python from PyPI rather than a git source, keeping the sample's greetings in a database through `strata_python.db`, typing the API end to end, and moving the web tooling onto leaflet-node's stack (Biome + oxlint). Correction: the earlier rule that the template ships no database is superseded; greetings now live in SQLite (or Postgres) and `data_dir` is gone.

- `pyproject.toml`, `uv.lock`: `strata-python[db]>=0.2.6,<0.3` from PyPI, dev group `strata-python[dev]` plus hypothesis and diff-cover; lock upgraded; `[tool.strata-db]`; pytest `--import-mode=importlib` so both suites run together.
- `.github/dependabot.yml`: grouped uv, npm and Actions updates. `.github/workflows/upgrade-strata-python.yml`: removed (Dependabot does it).
- `src/app/strata-db.toml`, `src/app/models.py`, `src/app/db.py`, `src/app/migrations/`: **new**; the greetings table, its first revision, and where the records are (`STRATA_DB_URL`/`APP_DATABASE_URL`, else `~/.app/app.db`).
- `src/app/settings.py`: `greeting` and `style` (`choices`); `data_dir` removed.
- `src/app/greet.py`: `ApiModel` contracts (`Greeting`, `Sent`, `Cleared`), database reads and writes, a cursor-paged `Page[Sent]`; times read back from Postgres answered in UTC.
- `src/app/system.py`: the app's own numbers on the shared `/api/system`.
- `src/app/server/app.py`: `base_app(commit=)`, `add_error_handlers`, `add_database`, `add_system`; typed routes. `src/app/server/landing.html`: no data folder.
- `src/app/cli.py`: `hello --save` and `messages` through `db.session()`; `openapi [--check]`.
- `web/openapi.json`, `web/src/api.generated.ts`: **new**, generated (`uv run app openapi`, `npm run api-types`).
- `web/package.json`, `web/package-lock.json`: strata-react 1.3.3 and every dependency at its latest (React Router 8, MSW 3, Vitest 5, Storybook 10.6, Playwright 1.65.1); the TypeScript 6/7 split; `lint`, `format`, `api-types`, `api-types:check`. `web/biome.json`, `web/.oxlintrc.json`: **new**.
- `web/src/api.ts`, `web/src/main.tsx`, `web/src/screens/*`, `web/src/mocks/*`: `createTypedApi`, `appBase()`, `ButtonLink`, `useAsyncAction` field errors, `ChoiceGroup`, the system page from `/api/system`; mocks answer the new shapes (new `systemUnread` state).
- `web/stories/`, `web/tests/`, `web/strata-visual.config.ts`: React Aria roles, `expectOneFilledButton`, new disk-unread story; the selected state presses Space on the row checkboxes.
- `web/tests/visual/baselines/`: all 78 rewritten (React Aria controls, lucide 1.78, Chromium 159, the new system and settings screens).
- `tests/`: the plugin's `db_session`/`db_env`/`live_app` and `strata_python.testing` (`run_cli`, `run_module`, `assert_openapi_current`, the standard database tests) replace the app's own helpers; `tests/utils/fakes.py` removed.
- `.github/workflows/unit.yml`: `strata-db check`, `strata-public-check` on the tree and wheel, unit tests on Postgres, web lint and generated-types check. `update-visual-baselines.yml`: checkout v7.
- `README.md`, `AGENTS.md`, `docs/*`, `deploy/app.service`, `tests/**/README.md`, `web/tests/README.md`: describe the database, the typed API and the new commands; `APP_DATA` and `withBase()` references removed.

## 2026-11-09

**Regenerate visual baselines on the CI runner (branch `claude/project-thread-iw7199`)**
Jonathan wants every dependency kept current, including Dependabot's playwright and lucide-react bumps. Those change the Chromium or the icons behind every screenshot, and a laptop cannot reproduce the CI Chromium, so the baselines are now written by a manual workflow.

- `.github/workflows/update-visual-baselines.yml`: **new**; manual run on a chosen branch: `test:visual:update`, then `test:visual` to prove stability, then commits `web/tests/visual/baselines` to that branch.
- `AGENTS.md`: CI section mentions it.

**Move onto the strata-python library (branch `claude/project-thread-iw7199`)**
Jonathan asked for the shared server code to live in a `strata-python` project (like strata-react) so the template stops duplicating it, and for apps to track its latest. This replaces the template's own copies; behaviour is unchanged except where noted.

- `pyproject.toml`, `uv.lock`: depend on `strata-python` as a git source tracking `main` (the lock pins the commit); pytest options `strata_env_prefix`/`strata_tuning_vars` configure the library's plugin.
- `src/app/oslib.py`, `scripts/check.py`, `tests/utils/http_server.py`, `tests/unit/test_oslib.py`, `tests/unit/test_http_server.py`: **removed**, now `strata_python.oslib`, `strata-check` and the plugin's `http_server` fixture (the library tests them, with real processes and sockets).
- `src/app/settings.py`: declares the two settings with `strata_python.settings.Settings`; same files and `APP_*` variables. Corrections: a bad `data_dir` or blank greeting now raises ValueError from `save` (the API answers 400, as it did for a relative path), `~` in `data_dir` is expanded when saved, and a bad stored or environment value falls back to the default instead of crashing.
- `src/app/server/app.py`, `src/app/cli.py`: health, settings and page routes, `serve`, `doctor` and `set` come from the library; the app keeps its own routes and `hello`/`messages`.
- `tests/conftest.py`: hermetic environment, no-network guard and `http_server` fixture removed (plugin). The `fake_*` fixtures stay as last resorts.
- `scripts/check`, `.github/workflows/unit.yml`: run `strata-check`. `.github/workflows/upgrade-strata-python.yml` **new**: weekly lock upgrade that runs the gate and opens a PR.
- `AGENTS.md`, `README.md`: describe the library, the tracking-main rule and the upgrade workflow.

**Testing policy: real code over mocks (branch `claude/project-thread-iw7199`)**
Asked to steer tests away from mocks towards real HTTP, embedded databases and installed tools, and to make skipping deliberate.

- `AGENTS.md`: **new** Testing policy section (real by default; mocks only for true externals in quick many-case unit tests; install ffmpeg and the like instead of mocking; no silent skips, a skip is a marker with a reason and a switch; machine-heavy tests are marked and run where the machine is).
- `tests/utils/http_server.py`, `tests/unit/test_http_server.py`: **new**. A real loopback HTTP server scripted per test (`http_server` fixture in `tests/conftest.py`); a request no route answers fails the test at teardown.
- `tests/utils/fakes.py`: docstring marks the doubles as a last resort. `tests/README.md`: layout notes point to the policy.
- `pyproject.toml`: ruff `TID` rules selected, `pytest.importorskip` banned with the reason.

**AGENTS.md reorganised as the basis for apps made from the template (branch `claude/project-thread-iw7199`)**
Asked to make the agent instructions suitable as the starting point for future apps, and to point database work at the shared database project.

- `AGENTS.md`: regrouped into rules for every change (run `scripts/check`, changelog and docs in the same commit, comment the why, no secrets or machine-specific details, strict types, tests, report what was run), layout, Python tooling, tests, web, CI and a closing checklist. Says which parts to keep unchanged in a derived app. Content of the earlier bullets is kept.
- `AGENTS.md`: **new** Database section. Apps use [jburnhams/database](https://github.com/jburnhams/database) (one shared database, one schema per app, models and migrations in the app repo, `dbtool check` in CI, never one database per app) and link its adoption guide rather than repeating it.

**Generic deployment notes and a systemd unit example (branch `claude/project-thread-iw7199`)**
A Docker image was dropped from the plan because apps are not deployed that way. These files are deliberately free of machine-specific details.

- `deploy/app.service`: **new**. Example systemd user unit running `uv run --locked --no-dev app serve`.
- `docs/deploying.md`: **new**. Build, install, run, reverse-proxy and how to keep a service file in step with the repo.
- `AGENTS.md`: points to them; the stale `setup_env` mention is gone (corrects the earlier line left behind by the uv change).

**Move the Python side to uv, typed strict, one gate (branch `claude/project-thread-iw7199`)**
Asked for an evaluation of this template against current best practice; the tooling gaps it found are closed here. Behaviour of the app is unchanged.

- `pyproject.toml`: now a real project (`[project]`, hatchling build, `app` console script, `[dependency-groups] dev`), with `--strict-markers --strict-config` for pytest, ruff rules `E,F,I,B,UP,SIM,RUF,C4,PT,S` at line length 120, and pyright strict.
- `uv.lock`, `.python-version`: **new**. Builds are reproducible; CI installs with `uv sync --locked`.
- `requirements.txt`, `requirements-test.txt`, `scripts/setup_env.sh`, `scripts/setup_env.ps1`: **removed**; `uv sync` replaces them. `app` and `app.cmd` stay as thin wrappers over `uv run app`.
- `scripts/check`, `scripts/check.py`: **new**. The one gate (lockfile, ruff lint and format, pyright, ty, unit tests with coverage) for git hooks, agents and CI.
- `src/app/`: fully annotated; `__version__` now reads the package metadata. `oslib.py` relaxes pyright for that one file because its Windows branches use APIs the Linux stubs lack. Formatting is `ruff format` (separate commit, no behaviour change).
- `tests/`: new `test_version.py` and a partial-settings test (coverage is 100% again); a few asserts split for ruff's PT018.
- `.github/workflows/unit.yml`, `integration.yml`: uv with cache; lint, format and types run once on Linux 3.13; weekly `uv audit`. `.github/dependabot.yml`: **new** (uv, npm, actions).
- README, AGENTS.md, test READMEs, docs: commands updated to uv and `scripts/check`.
- Not done yet: Dockerfile and systemd unit, copier conversion, release workflow (next phases).
