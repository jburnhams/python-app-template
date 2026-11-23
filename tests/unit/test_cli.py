import importlib
import json
from pathlib import Path

import pytest

from app import cli
from app.server import app as server_app


def test_doctor_success_and_missing_module(capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch):
    assert cli.main(["doctor"]) == 0
    assert "sqlalchemy" in capsys.readouterr().out

    real_import = importlib.import_module

    def fake_import(name: str):
        if name == "uvicorn":
            raise ImportError("no uvicorn")
        return real_import(name)

    monkeypatch.setattr(importlib, "import_module", fake_import)
    assert cli.main(["doctor"]) == 1
    assert "MISSING  uvicorn" in capsys.readouterr().out


def test_hello_and_messages_commands(capsys: pytest.CaptureFixture[str], db_env: str):
    assert cli.main(["hello"]) == 0
    assert capsys.readouterr().out.strip() == "Hello, World!"
    assert cli.main(["hello", "Alice", "--greeting", "Hi", "--save", "--json"]) == 0
    rec = json.loads(capsys.readouterr().out)
    assert (rec["id"], rec["message"]) == (1, "Hi, Alice!")

    assert cli.main(["messages"]) == 0
    assert "#1    Hi, Alice!" in capsys.readouterr().out
    assert cli.main(["messages", "--json"]) == 0
    assert [m["name"] for m in json.loads(capsys.readouterr().out)] == ["Alice"]
    assert cli.main(["messages", "--clear"]) == 0
    assert "cleared 1 greeting(s)" in capsys.readouterr().out
    assert cli.main(["messages"]) == 0
    assert "no greetings kept yet" in capsys.readouterr().out
    assert cli.main(["messages", "--clear", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"cleared": 0}

    with pytest.raises(SystemExit, match="at most 120 characters"):
        cli.main(["hello", "x" * 121, "--save"])


def test_set_serve_and_openapi_commands(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    assert cli.main(["set", "style"]) == 0
    assert "style = excited  (one of: excited, calm)" in capsys.readouterr().out
    assert cli.main(["set", "greeting", "Howdy"]) == 0
    assert "greeting = Howdy" in capsys.readouterr().out
    with pytest.raises(SystemExit, match="unknown setting"):
        cli.main(["set", "bad_key", "val"])

    called: list[list[str]] = []
    monkeypatch.setattr(server_app, "main", lambda argv: called.append(argv))
    assert cli.main(["serve", "--host", "0.0.0.0", "--port", "9000"]) == 0
    assert called == [["--host", "0.0.0.0", "--port", "9000"]]

    out = tmp_path / "openapi.json"
    assert cli.main(["openapi", "-o", str(out)]) == 0
    assert '"/api/messages/page"' in out.read_text(encoding="utf8")
