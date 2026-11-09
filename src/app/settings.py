"""User settings: one JSON file, `~/.app/settings.json` (the folder can be moved with the APP_HOME environment variable).

  data_dir   where application data files live. Default: `data/` in this repository (gitignored) until configured.
  greeting   default greeting word used by `greet.py` (default: 'Hello').

The environment variables APP_DATA and APP_GREETING override the file (handy for tests and one-off runs)."""

import json
import os
from collections.abc import Mapping
from typing import Any, cast

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_DATA_DIR = os.path.join(REPO, "data")
DEFAULT_GREETING = "Hello"
KNOWN = ("data_dir", "greeting")


def home() -> str:
    return os.environ.get("APP_HOME") or os.path.join(os.path.expanduser("~"), ".app")


def _path() -> str:
    return os.path.join(home(), "settings.json")


def load() -> dict[str, Any]:
    try:
        with open(_path(), encoding="utf8") as f:
            d = json.load(f)
    except (OSError, ValueError):
        d = {}
    return cast("dict[str, Any]", d) if isinstance(d, dict) else {}


def save(changes: Mapping[str, object]) -> dict[str, Any]:
    """Merge `changes` (known keys only) into the settings file; returns the saved settings. A None value removes the setting (back to its default)."""
    d = load()
    for k, v in changes.items():
        if k not in KNOWN:
            raise KeyError(f"unknown setting {k!r}")
        if v is None:
            d.pop(k, None)
        else:
            d[k] = str(v)
    os.makedirs(home(), exist_ok=True)
    tmp = _path() + ".tmp"
    with open(tmp, "w", encoding="utf8") as f:
        json.dump(d, f, indent=1)
    os.replace(tmp, _path())
    return d


def data_dir() -> str:
    """The folder that holds application data (created when asked for)."""
    p = os.environ.get("APP_DATA") or load().get("data_dir") or DEFAULT_DATA_DIR
    p = os.path.abspath(os.path.expanduser(p))
    os.makedirs(p, exist_ok=True)
    return p


def greeting() -> str:
    """The configured greeting word (e.g. 'Hello')."""
    g = (os.environ.get("APP_GREETING") or load().get("greeting") or DEFAULT_GREETING).strip()
    return g or DEFAULT_GREETING


def all_settings() -> dict[str, str]:
    return {"data_dir": data_dir(), "greeting": greeting()}
