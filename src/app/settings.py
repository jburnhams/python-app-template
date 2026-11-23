"""User settings: one JSON file, `~/.app/settings.json` (the folder moves with the APP_HOME environment variable).

APP_GREETING and APP_STYLE override the file (handy for tests and one-off runs).

  greeting   the word a greeting starts with when none is given (default: 'Hello').
  style      how a greeting ends: 'excited' ("Hello, Ada!") or 'calm' ("Hello, Ada."). One of a fixed set, so the API
             schema types it as an enum and the web app's generated type is that union.

The file handling, precedence, validation and the `GET`/`PUT /api/settings` routes are
[strata_python.settings](https://github.com/jburnhams/strata-python); this module only declares the app's settings."""

from typing import Literal

from strata_python.settings import Setting, Settings, non_empty

Style = Literal["excited", "calm"]
STYLES: tuple[Style, ...] = ("excited", "calm")
ENDINGS: dict[str, str] = {"excited": "!", "calm": "."}

SETTINGS = Settings(
    "app",
    [
        Setting("greeting", default="Hello", normalise=non_empty),
        Setting("style", default="excited", choices=list(STYLES)),
    ],
)


def greeting() -> str:
    """The configured greeting word (e.g. 'Hello')."""
    return SETTINGS.get("greeting")


def ending() -> str:
    """The punctuation the configured style ends a greeting with."""
    return ENDINGS[SETTINGS.get("style")]  # the setting only ever holds one of STYLES
