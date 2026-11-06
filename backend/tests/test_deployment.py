from fastapi.testclient import TestClient

from backend.app.config import Settings
from backend.app.main import create_app


def test_frontend_build_is_served_without_shadowing_api_or_source_files(tmp_path, monkeypatch):
    build = tmp_path / 'frontend' / 'dist'
    build.mkdir(parents=True)
    (build / 'assets').mkdir()
    (build / 'index.html').write_text('<html><body>React app</body></html>', encoding='utf-8')
    (build / 'assets' / 'app.js').write_text('console.log("app")', encoding='utf-8')
    (tmp_path / '.env').write_text('SECRET=test', encoding='utf-8')
    monkeypatch.setattr('backend.app.main.ROOT', tmp_path)
    app = create_app(Settings(data_dir=tmp_path / 'data'), start_jobs=False)
    with TestClient(app) as client:
        assert 'React app' in client.get('/?view=workspace').text
        assert client.get('/assets/app.js').status_code == 200
        assert client.get('/api/health').json()['status'] == 'ok'
        assert client.get('/api/unknown').status_code == 404
        assert client.get('/.env').status_code == 404
        assert client.get('/docs').status_code == 200

    settings = Settings(data_dir=tmp_path / 'data', origin='https://service.example', cookie_secure=True)
    with TestClient(create_app(settings, start_jobs=False)) as client:
        page = client.get('/')
        assert "frame-ancestors 'none'" in page.headers['content-security-policy']
        assert page.headers['x-frame-options'] == 'DENY'
        assert page.headers['strict-transport-security'] == 'max-age=31536000'
        for path in ('/docs', '/redoc', '/openapi.json'):
            assert client.get(path).status_code == 404


def test_railway_volume_is_used_unless_data_directory_is_explicit(tmp_path, monkeypatch):
    monkeypatch.setattr('backend.app.config.load_dotenv', lambda *args, **kwargs: None)
    monkeypatch.setenv('GOOGLE_CLIENT_ID', '')
    monkeypatch.setenv('GOOGLE_CLIENT_SECRET', '')
    monkeypatch.setenv('SERVICE_ORIGIN', 'http://127.0.0.1:5173')
    monkeypatch.setenv('SERVICE_COOKIE_SECURE', 'false')
    monkeypatch.delenv('SERVICE_DATA_DIR', raising=False)
    monkeypatch.setenv('RAILWAY_VOLUME_MOUNT_PATH', str(tmp_path / 'volume'))
    assert Settings.from_env().data_dir == tmp_path / 'volume'
    monkeypatch.setenv('SERVICE_DATA_DIR', str(tmp_path / 'explicit'))
    assert Settings.from_env().data_dir == tmp_path / 'explicit'
