"""Command line. From strata-python: `doctor` (versions and imports), `set` (a setting), `serve` (the web server) and
`openapi` (the schema file the web app's types are generated from). The app's own: `hello` prints or keeps a greeting,
`messages` lists or clears the kept ones."""

import argparse
import json
import sys
from collections.abc import Sequence
from typing import TYPE_CHECKING

from strata_python import cli as shared

from app import __version__, db, greet, settings

if TYPE_CHECKING:
    from fastapi import FastAPI


def run_server(host: str, port: int) -> None:
    from app.server import app as server_app  # here, so the other commands do not import FastAPI's routes

    server_app.main(["--host", host, "--port", str(port)])


def create_app() -> "FastAPI":
    from app.server.app import create_app as create  # only when `openapi` runs

    return create()


def cmd_hello(args: argparse.Namespace) -> int:
    try:
        if args.save:
            with db.session() as s:
                rec = greet.send(s, args.name, args.greeting).model_dump(mode="json")
        else:
            rec = greet.format_greeting(args.name, args.greeting).model_dump(mode="json")
    except greet.GreetingError as e:
        sys.exit(str(e))
    print(json.dumps(rec) if args.json else rec["message"])
    return 0


def cmd_messages(args: argparse.Namespace) -> int:
    with db.session() as s:
        if args.clear:
            n = greet.clear(s).cleared
            print(json.dumps({"cleared": n}) if args.json else f"cleared {n} greeting(s)")
            return 0
        items = greet.everything(s)
    if args.json:
        print(json.dumps([m.model_dump(mode="json") for m in items], indent=1))
    elif not items:
        print("  (no greetings kept yet: ./app hello World --save)")
    for m in [] if args.json else items:
        print(f"  #{m.id:<4} {m.message:30} ({m.created.isoformat()})")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="app")
    sub = p.add_subparsers(dest="cmd", required=True)
    shared.add_doctor(sub, "app", __version__, ("fastapi", "uvicorn", "pydantic", "sqlalchemy", "strata_python"))
    h = sub.add_parser("hello", help="print a greeting (and optionally keep it)")
    h.add_argument("name", nargs="?", default="World")
    h.add_argument("--greeting", help="override the default greeting word")
    h.add_argument("--save", action="store_true", help="keep the greeting in the database")
    h.add_argument("--json", action="store_true")
    h.set_defaults(fn=cmd_hello)
    m = sub.add_parser("messages", help="list or clear the kept greetings")
    m.add_argument("--clear", action="store_true")
    m.add_argument("--json", action="store_true")
    m.set_defaults(fn=cmd_messages)
    shared.add_set(sub, settings.SETTINGS)
    shared.add_serve(sub, run_server, default_port=8360)
    shared.add_openapi(sub, create_app)
    a = p.parse_args(argv)
    return a.fn(a)
