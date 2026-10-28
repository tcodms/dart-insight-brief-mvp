import io
import sqlite3
import time
from dataclasses import replace
from urllib.parse import parse_qs, urlsplit

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfWriter

from backend.app.auth import COOKIE, digest, issue_session
from backend.app.config import Settings
from backend.app.main import create_app


@pytest.fixture
def service(tmp_path):
    app = create_app(Settings(data_dir=tmp_path, max_upload_bytes=4096))
    with TestClient(app, base_url='http://testserver') as client:
        yield app, client


def sign_in(app, client, sub='alice'):
    token = issue_session(app.state.db, app.state.settings,
                          {'sub': sub, 'email': f'{sub}@example.test', 'name': sub})
    client.cookies.set(COOKIE, token, path='/api')
    session = client.get('/api/auth/session').json()
    return {'Origin': app.state.settings.origin, 'X-CSRF-Token': session['csrfToken']}, token


def pdf(encrypted=False):
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    if encrypted:
        writer.encrypt('password')
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


def upload(client, headers, kind='cv', payload=None, name='CV.pdf'):
    return client.post('/api/documents', data={'kind': kind},
                       files={'file': (name, pdf() if payload is None else payload, 'application/pdf')}, headers=headers)


def test_auth_required_and_csrf_enforced(service):
    app, client = service
    assert client.get('/api/documents').status_code == 401
    assert upload(client, {}).status_code == 401
    assert client.get('/api/auth/login').status_code == 503
    headers, _ = sign_in(app, client)
    assert upload(client, {}).status_code == 403
    assert upload(client, {**headers, 'Origin': 'https://evil.example'}).status_code == 403
    assert list((app.state.settings.data_dir / 'files').iterdir()) == []


def test_persistence_versions_and_private_download(service):
    app, client = service
    headers, token = sign_in(app, client)
    first = upload(client, headers).json()
    assert first['version'] == 'v1' and first['pages'] == 1
    assert 'storage_key' not in first and 'user_id' not in first
    assert client.get(f"/api/documents/{first['id']}/file").content == pdf()
    with TestClient(create_app(app.state.settings)) as restarted:
        restarted.cookies.set(COOKIE, token, path='/api')
        assert restarted.get('/api/documents').json()['documents'][0]['id'] == first['id']
    assert client.delete(f"/api/documents/{first['id']}", headers=headers).status_code == 204
    second = upload(client, headers).json()
    assert second['version'] == 'v2'


def test_other_user_cannot_list_download_delete_or_inspect(service):
    app, client = service
    alice_headers, _ = sign_in(app, client)
    doc = upload(client, alice_headers).json()
    bob_headers, _ = sign_in(app, client, 'bob')
    assert client.get('/api/documents').json() == {'documents': []}
    for suffix in ('file', 'impact'):
        assert client.get(f"/api/documents/{doc['id']}/{suffix}").status_code == 404
    assert client.delete(f"/api/documents/{doc['id']}", headers=bob_headers).status_code == 404
    assert (app.state.settings.data_dir / 'files' / (doc['id'] + '.pdf')).exists()


@pytest.mark.parametrize('payload,name,status', [
    (b'not pdf', 'fake.pdf', 422), (b'%PDF- invalid', 'broken.pdf', 422),
    (pdf(True), 'encrypted.pdf', 422), (b'x' * 4097, 'large.pdf', 413),
    (pdf(), 'image.png', 422),
])
def test_rejected_files_leave_no_records_or_files(service, payload, name, status):
    app, client = service
    headers, _ = sign_in(app, client)
    assert upload(client, headers, payload=payload, name=name).status_code == status
    assert client.get('/api/documents').json() == {'documents': []}
    assert list((app.state.settings.data_dir / 'files').iterdir()) == []


def test_logout_revokes_session_and_expired_session_fails(service):
    app, client = service
    headers, token = sign_in(app, client)
    assert client.post('/api/auth/logout', headers=headers).status_code == 204
    client.cookies.set(COOKIE, token, path='/api')
    assert client.get('/api/documents').status_code == 401
    _, token = sign_in(app, client)
    with app.state.db.connect() as conn:
        conn.execute('UPDATE sessions SET expires_at=? WHERE token_hash=?', (int(time.time()) - 1, digest(token)))
    assert client.get('/api/auth/session').json()['authenticated'] is False


def test_cv_delete_cascades_personal_results_but_preserves_brief(service):
    app, client = service
    headers, _ = sign_in(app, client)
    report = upload(client, headers, 'report').json()['id']
    cv = upload(client, headers).json()['id']
    user = client.get('/api/auth/session').json()['user']['id']
    with app.state.db.connect() as conn:
        conn.execute("INSERT INTO company_briefs(id,user_id,report_document_id,company_name,result_json,created_at) VALUES('brief',?,?, 'A','{}','now')", (user, report))
        conn.execute("INSERT INTO personal_analyses(id,user_id,brief_id,cv_document_id,target_role,result_json,created_at) VALUES('personal',?,'brief',?,'dev','{}','now')", (user, cv))
        conn.execute("INSERT INTO evidence(id,user_id,document_id,personal_analysis_id,page,quote,section) VALUES('e',?,?,'personal',1,'quote','section')", (user, cv))
    impact = client.get(f'/api/documents/{cv}/impact').json()
    assert impact == {'briefs': 0, 'personalAnalyses': 1, 'preservesBriefs': True}
    assert client.delete(f'/api/documents/{cv}', headers=headers).status_code == 204
    with app.state.db.connect() as conn:
        assert conn.execute('SELECT COUNT(*) FROM company_briefs').fetchone()[0] == 1
        assert conn.execute('SELECT COUNT(*) FROM personal_analyses').fetchone()[0] == 0
        assert conn.execute('SELECT COUNT(*) FROM evidence').fetchone()[0] == 0
    assert not (app.state.settings.data_dir / 'files' / (cv + '.pdf')).exists()


def test_database_rejects_cross_owner_analysis_links(service):
    app, client = service
    headers, _ = sign_in(app, client)
    report = upload(client, headers, 'report').json()['id']
    sign_in(app, client, 'bob')
    bob = client.get('/api/auth/session').json()['user']['id']
    with pytest.raises(sqlite3.IntegrityError), app.state.db.connect() as conn:
        conn.execute("INSERT INTO company_briefs(id,user_id,report_document_id,company_name,result_json,created_at) VALUES('bad',?,?,'A','{}','now')", (bob, report))


def test_oauth_callback_failure_never_creates_a_session(service):
    app, client = service
    app.state.settings = replace(app.state.settings, google_id='fake', google_secret='fake')
    response = client.get('/api/auth/callback?code=untrusted', follow_redirects=False)
    assert response.status_code == 303
    assert response.headers['location'].endswith('/?auth=failed')
    assert COOKIE not in response.cookies
    with app.state.db.connect() as conn:
        assert conn.execute('SELECT COUNT(*) FROM users').fetchone()[0] == 0


def test_oauth_redirect_has_state_nonce_pkce_and_rejects_wrong_state(service, monkeypatch):
    app, client = service
    app.state.settings = replace(app.state.settings, google_id='fake', google_secret='fake')

    async def metadata():
        return {'authorization_endpoint': 'https://accounts.google.com/o/oauth2/v2/auth',
                'token_endpoint': 'https://oauth2.googleapis.com/token', 'issuer': 'https://accounts.google.com'}

    monkeypatch.setattr(app.state.google, 'load_server_metadata', metadata)
    response = client.get('/api/auth/login', follow_redirects=False)
    query = parse_qs(urlsplit(response.headers['location']).query)
    assert query['state'] and query['nonce'] and query['code_challenge']
    assert query['code_challenge_method'] == ['S256']
    assert query['redirect_uri'] == [app.state.settings.origin + '/api/auth/callback']
    rejected = client.get('/api/auth/callback?code=fake&state=wrong', follow_redirects=False)
    assert rejected.headers['location'].endswith('/?auth=failed')
    assert client.get('/api/auth/session').json()['authenticated'] is False


def test_verified_callback_issues_httponly_session_and_unverified_email_fails(service, monkeypatch):
    app, client = service
    app.state.settings = replace(app.state.settings, google_id='fake', google_secret='fake')
    verified = False

    async def validated_token(request):
        # Simulate Authlib's validated return value; this is not a live Google test.
        return {'id_token': 'validated-in-test', 'userinfo': {'sub': 'google-user', 'email': 'user@example.test', 'email_verified': verified}}

    monkeypatch.setattr(app.state.google, 'authorize_access_token', validated_token)
    assert client.get('/api/auth/callback', follow_redirects=False).headers['location'].endswith('/?auth=failed')
    verified = True
    response = client.get('/api/auth/callback', follow_redirects=False)
    assert 'HttpOnly' in response.headers['set-cookie'] and 'SameSite=lax' in response.headers['set-cookie']
    assert client.get('/api/auth/session').json()['authenticated'] is True


def test_chunked_body_limit_is_enforced_before_multipart_parsing(service):
    _, client = service
    def chunks():
        yield b'x' * (1024 * 1024)
        yield b'x' * 8192
    assert client.post('/api/documents', content=chunks(), headers={'Content-Type': 'multipart/form-data; boundary=test'}).status_code == 413


def test_startup_recovers_interrupted_delete_or_cleans_committed_delete(service):
    app, client = service
    headers, _ = sign_in(app, client)
    doc = upload(client, headers).json()['id']
    path = app.state.settings.data_dir / 'files' / (doc + '.pdf')
    trash = path.with_suffix('.trash')
    # Crash before commit: SQLite still owns the document, so restore its original.
    path.replace(trash)
    with TestClient(create_app(app.state.settings)):
        assert path.exists() and not trash.exists()
    # Crash after commit: the hidden trash file should be removed on restart.
    path.replace(trash)
    with app.state.db.connect() as conn:
        conn.execute('DELETE FROM documents WHERE id=?', (doc,))
    with TestClient(create_app(app.state.settings)):
        assert not path.exists() and not trash.exists()
