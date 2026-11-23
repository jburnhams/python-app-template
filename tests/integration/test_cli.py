import json
from collections.abc import Callable
from pathlib import Path

from strata_python.testing import CliResult

from app import settings

Cli = Callable[..., CliResult]  # the `cli` fixture (tests/integration/conftest.py)


def test_doctor_reports_the_environment(cli: Cli):
    r = cli("doctor", check=False)
    assert "app 0.1.0" in r.stdout
    assert "sqlalchemy" in r.stdout
    assert r.code == 0


def test_kept_greetings_live_in_the_fallback_database_in_the_app_home(cli: Cli):
    assert cli("hello", "World").stdout.strip() == "Hello, World!"
    rec = json.loads(cli("hello", "Grace", "--greeting", "Welcome", "--save", "--json").stdout)
    assert (rec["id"], rec["message"]) == (1, "Welcome, Grace!")
    # no database configured: SQLite in the app's home, migrated on first use
    assert (Path(settings.SETTINGS.home()) / "app.db").is_file()
    assert [m["name"] for m in json.loads(cli("messages", "--json").stdout)] == ["Grace"]
    assert "cleared 1 greeting(s)" in cli("messages", "--clear").stdout
    assert json.loads(cli("messages", "--json").stdout) == []


def test_settings_are_viewed_and_updated_from_the_command_line(cli: Cli):
    assert "style = calm" in cli("set", "style", "CALM").stdout
    assert cli("hello", "Ada").stdout.strip() == "Hello, Ada."
    assert cli("set", "style", "loud", check=False).stderr == "style: must be one of excited, calm\n"
    assert "style = excited" in cli("set", "style", "default").stdout
    assert cli("set", "nope", "x", check=False).code != 0


def test_the_committed_schema_check_passes(cli: Cli):
    # What CI runs on the Python side, so a stale web/openapi.json fails without Node.
    assert cli("openapi", "--check").code == 0


def test_the_command_line_runs_as_a_real_process(cli_subprocess: Cli):
    assert "app 0.1.0" in cli_subprocess("doctor").stdout
    assert cli_subprocess("hello", "Subprocess", "--save").stdout.strip() == "Hello, Subprocess!"
    assert "Hello, Subprocess!" in cli_subprocess("messages").stdout
