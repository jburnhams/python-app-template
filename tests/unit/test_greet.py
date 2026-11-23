import datetime

import pytest
from hypothesis import given
from hypothesis import strategies as st
from sqlalchemy.orm import Session

from app import greet, settings


def test_format_greeting_defaults_and_custom():
    assert greet.format_greeting().model_dump() == {"name": "World", "greeting": "Hello", "message": "Hello, World!"}
    assert greet.format_greeting("  Alice  ", "  Hi ").message == "Hi, Alice!"
    assert greet.format_greeting("", "").message == "Hello, World!"


def test_the_style_setting_ends_the_greeting():
    settings.SETTINGS.save({"style": "Calm"})  # matched without regard to case, stored as the choice is spelled
    assert settings.SETTINGS.get("style") == "calm"
    assert greet.format_greeting("Ada").message == "Hello, Ada."
    with pytest.raises(ValueError, match="one of"):
        settings.SETTINGS.save({"style": "shouty"})


def test_format_greeting_refuses_with_the_sentence_the_web_app_shows():
    with pytest.raises(greet.GreetingError, match=r"^Use at most 120 characters for the name; this is 121\.$"):
        greet.format_greeting("x" * 121)
    with pytest.raises(greet.GreetingError, match="at most 60 characters for the greeting"):
        greet.format_greeting("Alice", "g" * 61)


@given(
    name=st.text(min_size=1, max_size=40).filter(lambda s: s.strip()),
    greeting=st.text(min_size=1, max_size=20).filter(lambda s: s.strip()),
)
def test_format_greeting_property(name: str, greeting: str):
    res = greet.format_greeting(name, greeting)
    assert (res.name, res.greeting) == (name.strip(), greeting.strip())
    assert res.message == f"{greeting.strip()}, {name.strip()}!"


def test_send_keeps_greetings_newest_first_and_clear_removes_them(db_session: Session):
    assert greet.everything(db_session) == []
    a = greet.send(db_session, "Alice")
    b = greet.send(db_session, "Bob", "Welcome")
    assert (a.id, a.message, b.id, b.message) == (1, "Hello, Alice!", 2, "Welcome, Bob!")
    assert a.created.tzinfo == datetime.UTC  # aware, even read back from SQLite
    assert [m.id for m in greet.everything(db_session)] == [2, 1]
    assert greet.count(db_session) == 2
    assert greet.clear(db_session).cleared == 2
    assert greet.everything(db_session) == []
    assert greet.clear(db_session).cleared == 0


def test_times_read_back_in_any_zone_are_answered_in_utc():
    from zoneinfo import ZoneInfo

    from app.models import SentGreeting

    when = datetime.datetime(2026, 11, 9, 10, 12, tzinfo=ZoneInfo("Europe/Paris"))  # how a Postgres session may answer
    row = SentGreeting(name="Ada", greeting="Hi", message="Hi, Ada!", created=when)
    row.id = 7
    assert greet.Sent.of(row).created == datetime.datetime(2026, 11, 9, 9, 12, tzinfo=datetime.UTC)
    assert greet.Sent.of(row).created.tzinfo is datetime.UTC


def test_a_refused_greeting_keeps_nothing(db_session: Session):
    with pytest.raises(greet.GreetingError):
        greet.send(db_session, "x" * 121)
    assert greet.count(db_session) == 0


def test_ids_are_never_reused_after_a_removal(db_session: Session):
    greet.send(db_session, "Ann")
    newest = greet.send(db_session, "Ben")
    assert greet.remove(db_session, newest.id).name == "Ben"
    assert greet.send(db_session, "Cat").id == 3  # not 2: the web app may still be hiding 2 behind its Undo
    with pytest.raises(KeyError, match="There is no greeting 2"):
        greet.remove(db_session, 2)


def test_pages_follow_the_cursor_even_when_its_greeting_was_removed(db_session: Session):
    for n in "abcde":
        greet.send(db_session, n)
    first = greet.page(db_session, limit=2)
    assert [m.name for m in first.items] == ["e", "d"]
    assert first.next == "4"
    greet.remove(db_session, 4)
    second = greet.page(db_session, after=int(first.next), limit=2)
    assert [m.name for m in second.items] == ["c", "b"]
    last = greet.page(db_session, after=2, limit=2)
    assert ([m.name for m in last.items], last.next) == (["a"], None)
