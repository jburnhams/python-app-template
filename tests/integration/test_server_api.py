"""The real server: the app under uvicorn on a loopback port (the plugin's `live_app`), answering real HTTP requests,
over the settings file and the SQLite fallback database in the test's home folder, which the CLI shares."""

import json
import urllib.error
import urllib.request
from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager
from typing import Any

import pytest
from fastapi import FastAPI
from strata_python.testing import CliResult

Cli = Callable[..., CliResult]  # the `cli` fixture (tests/integration/conftest.py)


@pytest.fixture
def server(live_app: Callable[[FastAPI], AbstractContextManager[str]]) -> Iterator[str]:
    from app.server.app import create_app

    with live_app(create_app()) as base:
        yield base


def call(base: str, method: str, path: str, body: object = None) -> tuple[int, Any]:
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(base + path, data=data, method=method, headers={"Content-Type": "application/json"})  # noqa: S310 - loopback
    try:
        with urllib.request.urlopen(req, timeout=10) as r:  # noqa: S310 - loopback
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def test_greetings_sent_over_http_are_kept_and_seen_by_the_cli(server: str, cli: Cli):
    status, health = call(server, "GET", "/api/health")
    assert (status, health["ok"], health["version"]) == (200, True, "0.1.0")
    for n in ("Ann", "Ben", "Cat"):
        assert call(server, "POST", "/api/messages", {"name": n})[0] == 200
    assert call(server, "DELETE", "/api/messages/2")[0] == 200
    out = cli("messages").stdout
    assert ("Hello, Ann!" in out, "Hello, Ben!" in out, "Hello, Cat!" in out) == (True, False, True)
    assert call(server, "POST", "/api/messages", {"name": "Dee"})[1]["id"] == 4
    status, page = call(server, "GET", "/api/messages/page?limit=2")
    assert (status, [m["name"] for m in page["items"]], page["next"]) == (200, ["Dee", "Cat"], "3")
    assert call(server, "GET", "/api/system")[1]["greetings"] == 3


def test_errors_answer_with_the_sentence(server: str):
    status, body = call(server, "POST", "/api/messages", {"name": "x" * 121})
    assert (status, body) == (400, {"detail": "Use at most 120 characters for the name; this is 121.", "payload": None})
    assert call(server, "DELETE", "/api/messages/99")[0] == 404
    assert call(server, "PUT", "/api/settings", {"style": "loud"})[0] == 400


def test_settings_changes_affect_later_greetings(server: str):
    assert call(server, "PUT", "/api/settings", {"greeting": "Bonjour", "style": "calm"})[0] == 200
    assert call(server, "GET", "/api/hello?name=Monde")[1]["message"] == "Bonjour, Monde."


def test_a_reload_on_any_screen_gets_the_app(server: str):
    with urllib.request.urlopen(server + "/settings?tab=appearance", timeout=10) as r:  # noqa: S310 - loopback
        assert r.status == 200
        assert '<base href="./">' in r.read().decode()
