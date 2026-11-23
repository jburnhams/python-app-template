"""Where the records are. `STRATA_DB_URL` or `APP_DATABASE_URL` names a database (the shared Postgres in a deployment);
with neither, a SQLite file in the app's home folder (`~/.app/app.db`, moved with APP_HOME), so a checkout runs with
nothing to set up. The server opens it through `strata_python.db.web.add_database`; the CLI through `session()`."""

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy.orm import Session
from strata_python.db import Project, local_url

from app import settings

# Found by walking up from this file to src/app/strata-db.toml, so an installed wheel finds it too.
PROJECT = Project.load(__file__)


def default_url() -> str:
    """The SQLite fallback, read each time it is needed, so a test's or a run's APP_HOME is followed."""
    return local_url(settings.SETTINGS)


@contextmanager
def session() -> Generator[Session]:
    """A session on the migrated database, for one CLI command (the server keeps one engine for its life instead)."""
    engine = PROJECT.open(default=default_url())
    try:
        with Session(engine) as s:
            yield s
    finally:
        engine.dispose()
