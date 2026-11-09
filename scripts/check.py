"""The one gate: lint, format, types, lockfile and unit tests with coverage. Run it before every commit; the git hooks and CI call the same steps.

    scripts/check            # everything
    scripts/check --fast     # skip the tests (for a commit hook)
    scripts/check --fix      # apply ruff fixes and formatting first

Two type checkers gate: pyright (strict) and ty. ty is the one we are moving to; when it is stable and as strict as pyright's strict mode, delete the pyright step and its config."""

import subprocess
import sys

STEPS: list[tuple[str, list[str]]] = [
    ("lockfile is current", ["uv", "lock", "--check"]),
    ("ruff lint", ["ruff", "check", "src", "tests", "scripts"]),
    ("ruff format", ["ruff", "format", "--check", "src", "tests", "scripts"]),
    ("pyright (strict)", ["pyright"]),
    ("ty", ["ty", "check", "src"]),
]
TESTS = ("unit tests + coverage", ["pytest", "tests/unit", "--cov", "-q"])


def run(label: str, cmd: list[str]) -> bool:
    print(f"\n==> {label}: {' '.join(cmd)}", flush=True)
    return subprocess.run(cmd).returncode == 0  # noqa: S603  (fixed commands from this file)


def main(argv: list[str]) -> int:
    if "--fix" in argv:
        run("ruff fix", ["ruff", "check", "--fix", "src", "tests", "scripts"])
        run("ruff format", ["ruff", "format", "src", "tests", "scripts"])
    steps = list(STEPS) if "--fast" in argv else [*STEPS, TESTS]
    failed = [label for label, cmd in steps if not run(label, cmd)]
    print("\n" + ("FAILED: " + ", ".join(failed) if failed else "all checks passed"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
