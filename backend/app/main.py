"""DART Insight service API; Agent execution remains separate."""

from contextlib import asynccontextmanager
from urllib.parse import urlsplit

from authlib.integrations.starlette_client import OAuth
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import FileResponse

from backend.app.auth import router as auth_router
from backend.app.config import ROOT, Settings
from backend.app.db import Database
from backend.app.demo_data import demo_workspace
from backend.app.documents import router as documents_router
from backend.app.analysis import router as analysis_router
from backend.app.annotations import router as annotations_router
from backend.app.dart import router as dart_router
from backend.app.public_briefs import router as public_briefs_router
from backend.app.job_runner import JobManager


def create_app(settings: Settings | None = None, *, start_jobs=True, job_runner=None) -> FastAPI:
    settings = settings or Settings.from_env()
    db = Database(settings.data_dir / 'service.sqlite3')

    @asynccontextmanager
    async def lifespan(app):
        db.initialize()
        (settings.data_dir / 'files').mkdir(exist_ok=True)
        with db.connect() as conn:
            stored = {row[0] for row in conn.execute('SELECT storage_key FROM documents')}
        for trash in (settings.data_dir / 'files').glob('*.trash'):
            original = trash.with_suffix('.pdf')
            if original.name in stored and not original.exists():
                trash.replace(original)
            else:
                trash.unlink(missing_ok=True)
        if start_jobs:
            app.state.jobs.start()
        try:
            yield
        finally:
            app.state.jobs.close()

    local = urlsplit(settings.origin).hostname in ('localhost', '127.0.0.1', '::1')
    app = FastAPI(title='DART Insight API', version='0.2.0', lifespan=lifespan,
                  openapi_url='/openapi.json' if local else None)
    app.state.settings, app.state.db = settings, db
    app.state.jobs = JobManager(settings, db, runner=job_runner)
    oauth = OAuth()
    app.state.google = oauth.register(
        name='google', client_id=settings.google_id, client_secret=settings.google_secret,
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile', 'code_challenge_method': 'S256'},
    )
    app.add_middleware(SessionMiddleware, secret_key=settings.secret, session_cookie='dart_oauth',
                       max_age=600, same_site='lax', https_only=settings.cookie_secure, path='/api/auth')

    @app.middleware('http')
    async def private_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'no-referrer'
        if not local and settings.cookie_secure:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000'
        return response

    @app.get('/api/health')
    def health():
        return {'status': 'ok', 'service': 'dart-insight', 'mode': 'service'}

    @app.get('/api/demo/workspace')
    def public_demo_workspace():
        return demo_workspace()

    app.include_router(auth_router)
    app.include_router(documents_router)
    app.include_router(analysis_router)
    app.include_router(annotations_router)
    app.include_router(dart_router)
    app.include_router(public_briefs_router)
    frontend = ROOT / 'frontend' / 'dist'
    if (frontend / 'index.html').is_file():
        @app.get('/', include_in_schema=False)
        def frontend_page():
            return FileResponse(frontend / 'index.html', headers={
                'Content-Security-Policy': (
                    "default-src 'self'; script-src 'self' 'wasm-unsafe-eval'; "
                    "style-src 'self' 'unsafe-inline'; font-src 'self' blob: data:; "
                    "img-src 'self' blob: data:; worker-src 'self' blob:; "
                    "object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
                ),
                'X-Frame-Options': 'DENY',
            })

        app.mount('/assets', StaticFiles(directory=frontend / 'assets'), name='frontend-assets')
    return app


app = create_app()
