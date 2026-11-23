"""The sample's business logic: format a greeting, and keep the ones that were sent.

Functions that touch records take the caller's `Session` (the server's per-request `DbSession`, the CLI's
`db.session()`, a test's `db_session`) and commit their own writes, so they read the same from all three. The answers
are `contracts.ApiModel`s, which the routes declare, so `/api/openapi.json` describes them and the web app's types are
generated from it (`web/src/api.generated.ts`) instead of being written twice."""

import datetime

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session
from strata_python.contracts import ApiModel, Page

from app import settings
from app.models import SentGreeting

MAX_NAME = 120
MAX_GREETING = 60


class GreetingError(ValueError):
    """A greeting that cannot be sent; the server answers it as a 400 with the sentence (a ValueError)."""


class Greeting(ApiModel):
    """A formatted greeting."""

    name: str
    greeting: str
    message: str


class Sent(Greeting):
    """A greeting that was sent and kept. Ids grow with time and are never reused."""

    id: int
    created: datetime.datetime

    @classmethod
    def of(cls, row: SentGreeting) -> "Sent":
        # Every time stored here is UTC. SQLite keeps no zone, so its times come back naive; Postgres's come back in
        # the session's zone (Etc/UTC on a default server). Either way the answer is in UTC.
        c = row.created
        created = c.replace(tzinfo=datetime.UTC) if c.tzinfo is None else c.astimezone(datetime.UTC)
        return cls(id=row.id, name=row.name, greeting=row.greeting, message=row.message, created=created)


class Cleared(ApiModel):
    cleared: int


def format_greeting(name: str = "World", greeting: str | None = None) -> Greeting:
    """Format a greeting for `name` with `greeting` (or the configured word), ended as the configured style says."""
    clean_name = (name or "").strip() or "World"
    clean_greeting = (greeting or "").strip() or settings.greeting()
    if len(clean_name) > MAX_NAME:
        raise GreetingError(f"Use at most {MAX_NAME} characters for the name; this is {len(clean_name)}.")
    if len(clean_greeting) > MAX_GREETING:
        raise GreetingError(f"Use at most {MAX_GREETING} characters for the greeting; this is {len(clean_greeting)}.")
    message = f"{clean_greeting}, {clean_name}{settings.ending()}"
    return Greeting(name=clean_name, greeting=clean_greeting, message=message)


def send(db: Session, name: str = "World", greeting: str | None = None) -> Sent:
    """Format a greeting and keep it; returns the kept record."""
    g = format_greeting(name, greeting)
    row = SentGreeting(name=g.name, greeting=g.greeting, message=g.message, created=datetime.datetime.now(datetime.UTC))
    db.add(row)
    db.commit()
    return Sent.of(row)


def everything(db: Session) -> list[Sent]:
    """Every kept greeting, newest first."""
    return [Sent.of(r) for r in db.scalars(select(SentGreeting).order_by(SentGreeting.id.desc()))]


def page(db: Session, after: int | None = None, limit: int = 20) -> Page[Sent]:
    """One page of the log, newest first: the greetings older than the one with id `after` (the last one the client
    holds). `next` is the cursor for the page after, None on the last one.

    A cursor, not an offset: greetings removed between pages would make an offset skip the ones that moved up to fill
    the gap. Ids grow with time, so `after` still works when that greeting has itself been removed."""
    q = select(SentGreeting).order_by(SentGreeting.id.desc()).limit(limit + 1)
    if after is not None:
        q = q.where(SentGreeting.id < after)
    rows = list(db.scalars(q))
    items = [Sent.of(r) for r in rows[:limit]]
    return Page[Sent](items=items, next=str(items[-1].id) if len(rows) > limit else None)


def count(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(SentGreeting)) or 0


def remove(db: Session, greeting_id: int) -> Sent:
    """Remove one greeting by id and return it. KeyError (a 404) when there is no such greeting."""
    row = db.get(SentGreeting, greeting_id)
    if row is None:
        raise KeyError(f"There is no greeting {greeting_id}.")
    gone = Sent.of(row)
    db.delete(row)
    db.commit()
    return gone


def clear(db: Session) -> Cleared:
    """Remove every kept greeting."""
    n = count(db)
    db.execute(delete(SentGreeting))
    db.commit()
    return Cleared(cleared=n)
