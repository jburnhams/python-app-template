"""The app's records: SQLAlchemy models, migrated by Alembic (`src/app/migrations/`, declared in `src/app/strata-db.toml`).

One table, the greetings that were sent. Each model change comes with a reviewed revision: `uv run strata-db revision -m
"..."` writes it from the difference between these models and the migrations (a rename reads as drop + add, so read it),
and `uv run strata-db check` (CI) fails when they disagree. Models stay portable (generic types) so the same code runs on
the local SQLite fallback and on the shared Postgres; see strata-python's README, "Database"."""

import datetime

from sqlalchemy import DateTime, Integer, MetaData, String
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, mapped_column
from strata_python.db import NAMING_CONVENTION


class Base(MappedAsDataclass, DeclarativeBase):
    # Written out rather than `make_base()`: ty refuses a function's result as a base class. The shared naming convention
    # gives every constraint the same name on every app and engine, so migrations never drift on a name.
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class SentGreeting(Base):
    """A greeting that went out. Ids grow with time and are never reused (the web app hides a removed row by its id
    until the removal is committed, and pages the log with `after=<id>`), hence AUTOINCREMENT on SQLite, which would
    otherwise hand the largest id out again after the newest row is removed; Postgres identities never go back."""

    __tablename__ = "greetings"
    __table_args__ = {"sqlite_autoincrement": True}  # noqa: RUF012 - SQLAlchemy reads it from the class

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    name: Mapped[str] = mapped_column(String(120))
    greeting: Mapped[str] = mapped_column(String(60))
    message: Mapped[str] = mapped_column(String(200))
    created: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
