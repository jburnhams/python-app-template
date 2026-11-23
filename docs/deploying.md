# Deploying

The app is one process: `uv run app serve` (FastAPI plus the built React app). Run it however you run long-lived services; [deploy/app.service](../deploy/app.service) is a systemd user-unit example.

1. Build the web app once per checkout: `cd web && npm ci && npm run build` (writes into `src/app/server/static/`).
2. `uv sync --locked --no-dev` installs the runtime dependencies only.
3. Choose where the records go. With nothing set they go to a SQLite file in the app's home, `~/.app/app.db` (move it with `APP_HOME`), outside the checkout, so a fresh checkout keeps them. For the shared Postgres, give the service `APP_DATABASE_URL` (or `STRATA_DB_URL`) and `STRATA_DB_LIVE=1` from an environment file only the service user can read; strata-python's README ("Database") has the rest. The schema is migrated when the server first needs it.
4. Start `uv run --locked --no-dev app serve --host 127.0.0.1 --port <port>`. In a service, give uv's full path: systemd does not search `~/.local/bin`.
5. Put a reverse proxy in front if you want TLS or a shared hostname. The app works under a path prefix (`/<prefix>/`) with no configuration: see "Reverse-proxy support" in [AGENTS.md](../AGENTS.md). Forward the prefix-stripped path to the app.
6. Check `GET /api/health`: it returns `{"ok": true, "version": ..., "commit": ...}` (`commit` is the checkout's, or null for an installed wheel).

## Keep the service and the repo in step

A service file that names a launch command can go stale when the repo is restructured, and the failure only shows as a restart loop. So:

- Start the app only through the `app` console script (`uv run app serve`), never through a path to a source file.
- Change the unit in the same change as any rename of the package, the command or the port.
- After a restart, a port that answers is not proof the right app is running: compare `/api/health`'s `commit` with the checkout's (`git rev-parse HEAD`).
- Records live outside the checkout (step 3), so redeploying never touches them; a new revision in `src/app/migrations/` is applied on the first request after the restart.
