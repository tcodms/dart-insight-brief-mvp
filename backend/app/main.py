"""DART Insight service API; Agent execution remains separate."""

from contextlib import asynccontextmanager

from authlib.integrations.starlette_client import OAuth
from fastapi import FastAPI, Request
from starlette.middleware.sessions import SessionMiddleware

from backend.app.auth import router as auth_router
from backend.app.config import Settings
from backend.app.db import Database
from backend.app.demo_data import demo_workspace
from backend.app.documents import router as documents_router
from backend.app.limits import UploadBodyLimit


def create_app(settings: Settings | None = None) -> FastAPI:
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
        yield

    app = FastAPI(title='DART Insight API', version='0.2.0', lifespan=lifespan)
    app.state.settings, app.state.db = settings, db
    oauth = OAuth()
    app.state.google = oauth.register(
        name='google', client_id=settings.google_id, client_secret=settings.google_secret,
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile', 'code_challenge_method': 'S256'},
    )
    app.add_middleware(SessionMiddleware, secret_key=settings.secret, session_cookie='dart_oauth',
                       max_age=600, same_site='lax', https_only=settings.cookie_secure, path='/api/auth')
    app.add_middleware(UploadBodyLimit, max_bytes=settings.max_upload_bytes + 1024 * 1024)

    @app.middleware('http')
    async def private_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'no-referrer'
        return response

    @app.get('/api/health')
    def health():
        return {'status': 'ok', 'service': 'dart-insight', 'mode': 'service'}

    @app.get('/api/demo/workspace')
    def public_demo_workspace():
        return demo_workspace()

    app.include_router(auth_router)
    app.include_router(documents_router)
    return app


app = create_app()
