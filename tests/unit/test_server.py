from pathlib import Path

import pytest
import uvicorn
from fastapi.testclient import TestClient
from strata_python.testing import assert_openapi_current

from app import __version__
from app.server import app as server_app
from app.server.app import create_app

OPENAPI = Path(__file__).parents[2] / "web" / "openapi.json"


def test_the_committed_schema_is_what_the_server_answers():
    # The web app's types are generated from this file (web/src/api.generated.ts); a route change without
    # `./app openapi` (then `npm run api-types` in web/) fails here, before the types drift from the server.
    assert_openapi_current(create_app, OPENAPI)


def test_landing_page_and_built_static_index(tmp_path, monkeypatch: pytest.MonkeyPatch, db_env: str):
    monkeypatch.setattr(server_app, "STATIC", str(tmp_path / "no_static"))
    with TestClient(create_app()) as c:
        assert "Say hello" in c.get("/").text
        assert c.get("/api/health").json()["ok"] is True

    static = tmp_path / "static"
    (static / "assets").mkdir(parents=True)
    (static / "index.html").write_text("<h1>built react app</h1>", encoding="utf8")
    (static / "assets" / "main.js").write_text("console.log(1)", encoding="utf8")
    monkeypatch.setattr(server_app, "STATIC", str(static))
    with TestClient(create_app()) as c:
        assert c.get("/").text == '<base href="./"><h1>built react app</h1>'
        assert "console.log(1)" in c.get("/assets/main.js").text
        assert '<base href="../">' in c.get("/log/2026").text  # one level down: one step back up
        assert c.get("/api/nope").json() == {"detail": "no such endpoint"}


def test_hello_send_and_clear(client: TestClient):
    assert client.get("/api/hello").json() == {"name": "World", "greeting": "Hello", "message": "Hello, World!"}
    assert client.get("/api/hello", params={"name": "Ada", "greeting": "Hi"}).json()["message"] == "Hi, Ada!"
    refused = client.get("/api/hello", params={"name": "x" * 121})
    assert refused.status_code == 400
    assert refused.json() == {"detail": "Use at most 120 characters for the name; this is 121.", "payload": None}

    assert client.get("/api/messages").json() == []
    m = client.post("/api/messages", json={"name": "Ada", "greeting": "Hi"}).json()
    assert (m["id"], m["message"]) == (1, "Hi, Ada!")
    assert m["created"].endswith("Z") or m["created"].endswith("+00:00")
    assert client.post("/api/messages", json={"name": "x" * 121}).status_code == 400
    assert client.delete("/api/messages").json() == {"cleared": 1}
    assert client.get("/api/messages").json() == []


def test_paging_removing_and_the_system_page(client: TestClient):
    for n in ("a", "b", "c"):
        client.post("/api/messages", json={"name": n})
    page = client.get("/api/messages/page", params={"limit": 2}).json()
    assert [m["name"] for m in page["items"]] == ["c", "b"]
    assert page["next"] == "2"
    rest = client.get("/api/messages/page", params={"after": page["next"], "limit": 2}).json()
    assert ([m["name"] for m in rest["items"]], rest["next"]) == (["a"], None)
    assert client.get("/api/messages/page", params={"limit": 0}).status_code == 422
    assert client.delete("/api/messages/2").json()["name"] == "b"
    gone = client.delete("/api/messages/2")
    assert (gone.status_code, gone.json()["detail"]) == (404, "There is no greeting 2.")

    client.put("/api/settings", json={"greeting": "Hi"})
    s = client.get("/api/system").json()
    assert s["version"] == __version__
    assert s["greetings"] == 2
    (home,) = s["folders"]
    assert s["home_bytes"] == (Path(home["path"]) / "settings.json").stat().st_size  # the test database is elsewhere
    assert home["name"] == "home"
    assert home["total_bytes"] >= home["free_bytes"] > 0


def test_settings_roundtrip_with_choices_and_server_main(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    assert client.get("/api/settings").json() == {"greeting": "Hello", "style": "excited"}
    assert client.put("/api/settings", json={"style": "loud"}).status_code == 400
    assert client.put("/api/settings", json={"greeting": "Hey", "style": "calm"}).json() == {
        "greeting": "Hey",
        "style": "calm",
    }
    assert client.get("/api/hello", params={"name": "Ada"}).json()["message"] == "Hey, Ada."
    assert client.put("/api/settings", json={}).json() == {"greeting": "Hey", "style": "calm"}

    runs: list[tuple[str, int, str]] = []
    monkeypatch.setattr(uvicorn, "run", lambda app, host, port, log_level: runs.append((host, port, log_level)))
    server_app.main(["--host", "127.0.0.1", "--port", "8360"])
    assert runs == [("127.0.0.1", 8360, "warning")]
