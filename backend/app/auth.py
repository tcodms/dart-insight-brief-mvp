import hashlib
import secrets
import time
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from starlette.responses import RedirectResponse, Response

router = APIRouter(prefix='/api/auth')
COOKIE = 'dart_session'


def digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def current_session(request: Request):
    token = request.cookies.get(COOKIE, '')
    if not token:
        return None
    with request.app.state.db.connect() as conn:
        row = conn.execute('''SELECT s.*, u.email, u.name FROM sessions s
            JOIN users u ON u.id=s.user_id WHERE token_hash=? AND expires_at>?''',
            (digest(token), int(time.time()))).fetchone()
    return dict(row) if row else None


def require_session(request: Request):
    session = current_session(request)
    if not session:
        raise HTTPException(401, '로그인이 필요합니다.')
    return session


def require_mutation(request: Request, session=Depends(require_session)):
    if request.headers.get('origin') != request.app.state.settings.origin:
        raise HTTPException(403, '요청 출처를 확인할 수 없습니다.')
    if not secrets.compare_digest(request.headers.get('x-csrf-token', ''), session['csrf_token']):
        raise HTTPException(403, '세션을 새로고침해 주세요.')
    return session


def issue_session(db, settings, claims, old_token=''):
    """Called only after Authlib has validated Google's ID token."""
    now = datetime.now(timezone.utc).isoformat()
    token, csrf = secrets.token_urlsafe(48), secrets.token_urlsafe(32)
    with db.connect() as conn:
        conn.execute('DELETE FROM sessions WHERE expires_at<=?', (int(time.time()),))
        conn.execute('''INSERT INTO users(id,google_sub,email,name,created_at) VALUES(?,?,?,?,?)
            ON CONFLICT(google_sub) DO UPDATE SET email=excluded.email,name=excluded.name''',
            (str(uuid4()), claims['sub'], claims['email'], claims.get('name') or claims['email'], now))
        user_id = conn.execute('SELECT id FROM users WHERE google_sub=?', (claims['sub'],)).fetchone()[0]
        if old_token:
            conn.execute('DELETE FROM sessions WHERE token_hash=?', (digest(old_token),))
        conn.execute('INSERT INTO sessions VALUES(?,?,?,?)',
                     (digest(token), user_id, csrf, int(time.time()) + settings.session_seconds))
    return token


@router.get('/session')
def session_status(request: Request):
    session = current_session(request)
    return {'authenticated': bool(session),
            'googleConfigured': request.app.state.settings.google_configured,
            'user': {'id': session['user_id'], 'name': session['name'], 'email': session['email']} if session else None,
            'csrfToken': session['csrf_token'] if session else None}


@router.get('/login')
async def login(request: Request):
    settings = request.app.state.settings
    if not settings.google_configured:
        raise HTTPException(503, 'Google 로그인 설정이 필요합니다. 관리자에게 문의해 주세요.')
    return await request.app.state.google.authorize_redirect(request, settings.origin + '/api/auth/callback')


@router.get('/callback')
async def callback(request: Request):
    settings = request.app.state.settings
    if not settings.google_configured:
        raise HTTPException(503, 'Google 로그인 설정이 필요합니다.')
    try:
        token = await request.app.state.google.authorize_access_token(request)
        claims = token.get('userinfo')
        if not claims or not claims.get('sub') or not claims.get('email') or claims.get('email_verified') is not True:
            raise ValueError('Verified identity required')
        session_token = issue_session(request.app.state.db, settings, claims, request.cookies.get(COOKIE, ''))
    except Exception:
        request.session.clear()
        return RedirectResponse(settings.origin + '/?auth=failed', status_code=303)
    request.session.clear()
    response = RedirectResponse(settings.origin + '/?view=materials', status_code=303)
    response.set_cookie(COOKIE, session_token, max_age=settings.session_seconds, httponly=True,
                        secure=settings.cookie_secure, samesite='lax', path='/api')
    return response


@router.post('/logout', status_code=204)
def logout(request: Request, session=Depends(require_mutation)):
    with request.app.state.db.connect() as conn:
        conn.execute('DELETE FROM sessions WHERE token_hash=?', (session['token_hash'],))
    response = Response(status_code=204)
    response.delete_cookie(COOKIE, path='/api', secure=request.app.state.settings.cookie_secure, httponly=True, samesite='lax')
    return response
