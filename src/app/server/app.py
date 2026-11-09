"""The application server: `./app serve` starts the FastAPI backend and serves the built React app.

    ./app serve [--host 127.0.0.1] [--port 8360]

API (JSON): GET /api/health; GET /api/system; GET /api/settings; PUT /api/settings {data_dir?, greeting?}; GET /api/hello?name=&greeting=;
GET /api/messages; GET /api/messages/page?after=&limit=; POST /api/messages {name, greeting?}; DELETE /api/messages; DELETE /api/messages/{id}.
Every other path serves the web app (`src/app/server/static/index.html` when built with `cd web && npm run build`, else the plain stand-in `landing.html`),
so a reload or a shared link to /settings?tab=appearance opens that screen: the app routes in the browser (React Router)."""
import os

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app import __version__, greet, settings, system

STATIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
LANDING = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'landing.html')


class SettingsIn(BaseModel):
    data_dir: str | None = None
    greeting: str | None = None


class MessageIn(BaseModel):
    name: str = 'World'
    greeting: str | None = None


def create_app():
    app = FastAPI(title='python-app-template', docs_url='/api/docs', openapi_url='/api/openapi.json')

    def guard(fn, *a, **kw):
        try: return fn(*a, **kw)
        except greet.GreetingError as e: raise HTTPException(400, str(e))

    @app.get('/api/health')
    def get_health(): return dict(ok=True, version=__version__)

    @app.get('/api/system')
    def get_system(): return system.status()

    @app.get('/api/settings')
    def get_settings(): return settings.all_settings()

    @app.put('/api/settings')
    def put_settings(s: SettingsIn):
        if s.data_dir is not None and not os.path.isabs(os.path.expanduser(s.data_dir)): raise HTTPException(400, 'the data folder must be an absolute path')
        changes = {}
        if s.data_dir is not None: changes['data_dir'] = s.data_dir
        if s.greeting is not None: changes['greeting'] = s.greeting
        if changes: settings.save(changes)
        return settings.all_settings()

    @app.get('/api/hello')
    def get_hello(name: str = 'World', greeting: str | None = None):
        return guard(greet.format_greeting, name, greeting)

    @app.get('/api/messages')
    def get_messages(): return greet.list_messages()

    @app.get('/api/messages/page')
    def get_messages_page(after: int | None = None, limit: int = Query(20, ge=1, le=200)): return greet.page_messages(after, limit)

    @app.post('/api/messages')
    def post_message(b: MessageIn): return guard(greet.add_message, b.name, b.greeting)

    @app.delete('/api/messages')
    def delete_messages(): return greet.clear_messages()

    @app.delete('/api/messages/{message_id}')
    def delete_message(message_id: int):
        removed = greet.remove_message(message_id)
        if removed is None: raise HTTPException(404, f'there is no greeting {message_id}')
        return removed

    if os.path.isdir(os.path.join(STATIC, 'assets')): app.mount('/assets', StaticFiles(directory=os.path.join(STATIC, 'assets')), name='assets')

    @app.get('/{path:path}', response_class=HTMLResponse, include_in_schema=False)
    def page(path: str):
        if path.startswith('api/'): raise HTTPException(404, 'no such endpoint')
        top = os.path.join(STATIC, path)
        if path and '/' not in path and os.path.isfile(top): return FileResponse(top)     # favicon.svg and the like, built from web/public
        built = os.path.join(STATIC, 'index.html')          # the React app when it has been built (cd web && npm run build), else the plain stand-in page
        with open(built if os.path.exists(built) else LANDING, encoding='utf8') as f: html = f.read()
        return with_base(html, path)

    return app


def with_base(html: str, path: str) -> str:
    """Give the page a relative <base> that points back at where the app is served, so one build works at the server's root and behind a reverse proxy at /<prefix>/.

    The server only sees the path under its own root (`settings`, `a/b`), never the proxy's prefix, but that is enough: the depth says how many `../` lead back up.
    The web app reads its base from `document.baseURI` (web/src/api.ts BASE), for its API calls and as React Router's basename, and its assets are relative (vite.config.ts base './')."""
    depth = path.count('/')
    tag = f'<base href="{"../" * depth or "./"}">'
    return html.replace('<head>', '<head>' + tag, 1) if '<head>' in html else tag + html


def main(argv=None):
    import argparse, uvicorn
    a = argparse.ArgumentParser(); a.add_argument('--host', default='127.0.0.1'); a.add_argument('--port', type=int, default=8360); a = a.parse_args(argv)
    print(f'data folder: {settings.data_dir()}\nhttp://{a.host}:{a.port}/'); uvicorn.run(create_app(), host=a.host, port=a.port, log_level='warning')
