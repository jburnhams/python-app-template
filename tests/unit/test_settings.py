import os

import pytest

from app import settings


def test_defaults_and_environment_overrides(monkeypatch: pytest.MonkeyPatch):
    assert settings.greeting() == "Hello"
    assert settings.ending() == "!"
    monkeypatch.setenv("APP_GREETING", "  Hi  ")
    monkeypatch.setenv("APP_STYLE", "calm")
    assert (settings.greeting(), settings.ending()) == ("Hi", ".")


def test_save_and_reset_in_the_settings_file():
    assert settings.SETTINGS.load() == {}
    assert settings.SETTINGS.save({"greeting": "Welcome"}) == {"greeting": "Welcome"}
    assert settings.greeting() == "Welcome"
    assert os.path.isfile(os.path.join(settings.SETTINGS.home(), "settings.json"))
    assert "greeting" not in settings.SETTINGS.save({"greeting": None})
    assert settings.greeting() == "Hello"
    with pytest.raises(ValueError, match="greeting"):
        settings.SETTINGS.save({"greeting": "   "})
    assert settings.SETTINGS.allowed("style") == settings.STYLES
