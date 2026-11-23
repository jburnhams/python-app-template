# Design brief

## 1. Goal

Provide a clean, minimal starting point for full-stack local-first Python + React applications with the exact build, test, coverage-gate and multi-OS CI setup proven in `strata-360` and `strata-stills`.

## 2. Architecture

- **Python CLI and HTTP server (`src/app/`)**:
  Everything shared (settings files, the web server's common routes and error answers, the CLI's common commands, the database plumbing, the test fixtures and the gate) is [strata-python](https://github.com/jburnhams/strata-python); this package is the app's own declarations and logic.
  - `cli.py`: command-line interface (`doctor`, `hello`, `messages`, `set`, `serve`, `openapi`), invoked as `uv run app` (the `app` console script from `pyproject.toml`; `./app` and `app.cmd` wrap it).
  - `server/app.py`: FastAPI application: strata-python's health, settings, system and docs routes and error answers, the app's typed `/api/*` routes, and the built React single-page app at every other path (falling back to `server/landing.html` when `web/` has not been built yet).
  - `settings.py`: the app's settings declared on strata-python's `Settings` (`~/.app/settings.json`, `APP_HOME` override, a choice typed as an enum in the API).
  - `models.py`, `migrations/`, `strata-db.toml`, `db.py`: the records (one SQLAlchemy table), their Alembic revisions and where the database is (a configured URL, else SQLite in the app home).
  - `greet.py`: the "Hello, world!" business logic: formatting, and sending, listing, paging (a cursor, ids never reused) and removing kept greetings, answered as `ApiModel`s.
  - `system.py`: the app's own numbers on the shared System page (greetings kept, size of its home).
- **React frontend (`web/`)**, built on [strata-react](https://github.com/jburnhams/strata-react) (components, UX patterns, the token contract and the testing and screenshot tooling):
  - React 19, TypeScript, Vite 8, Tailwind CSS v4 with Strata's token contract (Tailwind's stock colours, sizes and radii do not compile), a palette generated from the subject (`web/src/styles/`), bundled faces.
  - React Router with real paths (`web/src/routes.tsx`, one tree shared by the app, the tests and the stories); URL state for sort and tabs. The server answers every page path with the app and a relative `<base>`, so one build works at `/` or behind a reverse proxy at `/<subpath>/` (`web.add_web` on the server, strata-react's `appBase()` and `createTypedApi` in the browser).
  - Types from the server: `./app openapi` writes `web/openapi.json`, strata-react's `strata-api-types` writes `web/src/api.generated.ts`, and `createTypedApi<paths>()` checks every path, parameter, body and answer against it.
  - Server data through TanStack Query (`useLoad`, `useInfiniteLoad` with `apiPage`), shown through `DataView`/`InfiniteList` so loading, empty and error states cannot be left out; writes through `useAsyncAction` with `validate` for field messages.
  - Biome and oxlint (with type information) lint the web code, as in the libraries.
  - MSW handlers for every endpoint (`web/src/mocks/`) serve the jsdom tests, Storybook and the visual suite.
  - `npm run build` outputs directly to `src/app/server/static/`.

## 3. Principles

- **Hermetic tests by default**: every test run gets an isolated home and data directory outside `tmp_path`, stripped environment overrides, and a socket guard that blocks outbound network calls.
- **Two-tier test suites**: fast unit tests (`tests/unit/`, `web/tests/unit/`) and end-to-end integration tests (`tests/integration/`, `web/tests/integration/`), with clear file ownership so parallel agent branches never conflict.
- **Ratcheting coverage floors**: Python unit coverage (`fail_under` in `pyproject.toml`) and web combined coverage (`web/coverage-floor.json`) only ratchet up.
