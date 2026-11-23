"""Integration-suite fixtures: the CLI in this process and as a real `python -m app` process (strata_python.testing's
runners), over the real settings file and the SQLite fallback database in the test's own home folder."""

from collections.abc import Callable
from pathlib import Path

import pytest
from strata_python.testing import CliResult, run_cli, run_module

SRC = str(Path(__file__).parents[2] / "src")

Cli = Callable[..., CliResult]


@pytest.fixture
def cli() -> Cli:
    """`cli("hello", "World", "--json")` -> CliResult(stdout, stderr, code); AssertionError on a non-zero exit unless `check=False`."""
    from app import cli as app_cli

    return lambda *args, check=True: run_cli(app_cli.main, *args, check=check)


@pytest.fixture
def cli_subprocess(isolated_env: Path) -> Cli:
    """The same through a real process: the entry-point smoke test and anything that must not share this process's state."""
    return lambda *args, check=True: run_module("app", *args, src=SRC, check=check)
