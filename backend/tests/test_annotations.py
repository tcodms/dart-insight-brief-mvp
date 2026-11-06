from fastapi.testclient import TestClient

from backend.app.db import Database
from backend.app.main import create_app
from backend.tests.test_analysis import analysis_service, start_brief
from backend.tests.test_service import sign_in, upload


def saved_brief(service):
    app, client, headers = service
    _, job = start_brief(client, headers)
    assert app.state.jobs.run_one()
    result_id = client.get('/api/jobs/' + job['id']).json()['resultId']
    return f'/api/analyses/brief/{result_id}/annotations'


def test_annotations_persist_edit_and_leave_generated_report_unchanged(analysis_service):
    app, client, headers = analysis_service
    url = saved_brief(analysis_service)
    original = client.get(url.removesuffix('/annotations')).json()
    listing = client.get(url).json()
    assert listing['annotations'] == []
    body = {'contentVersion': listing['contentVersion'], 'start': 0, 'end': 5, 'quote': '기업 활동', 'note': ' 면접에서 연결하기 '}
    assert client.post(url, json=body).status_code == 403
    response = client.post(url, json=body, headers=headers)
    assert response.status_code == 201
    annotation = response.json()
    assert annotation['note'] == '면접에서 연결하기'
    assert client.post(url, json=body, headers=headers).status_code == 409
    assert client.patch(url + '/' + annotation['id'], json={'note': '수정한 생각'}, headers=headers).json()['note'] == '수정한 생각'
    assert client.get(url.removesuffix('/annotations')).json() == original
    with TestClient(create_app(app.state.settings), cookies=client.cookies) as restarted:
        assert restarted.get(url).json()['annotations'][0]['note'] == '수정한 생각'
    assert client.delete(url + '/' + annotation['id'], headers=headers).status_code == 204
    assert client.get(url).json()['annotations'] == []


def test_annotations_are_private_and_validate_version_range_and_size(analysis_service):
    app, client, headers = analysis_service
    url = saved_brief(analysis_service)
    body = {'contentVersion': client.get(url).json()['contentVersion'], 'start': 3, 'end': 6, 'quote': '안녕!', 'note': ''}
    assert client.post(url, json={**body, 'contentVersion': '0' * 64}, headers=headers).status_code == 409
    for bad in ({'start': -1}, {'end': 3}, {'quote': '다른길이'}, {'note': 'x' * 5001}):
        assert client.post(url, json={**body, **bad}, headers=headers).status_code == 422
    annotation = client.post(url, json=body, headers=headers).json()
    bob_headers, _ = sign_in(app, client, 'bob')
    assert client.get(url).status_code == 404
    assert client.post(url, json=body, headers=bob_headers).status_code == 404
    assert client.patch(url + '/' + annotation['id'], json={'note': '다른 사용자'}, headers=bob_headers).status_code == 404
    assert client.delete(url + '/' + annotation['id'], headers=bob_headers).status_code == 404
    client.cookies.clear()
    assert client.get(url).status_code == 401


def test_personal_annotations_and_brief_annotations_cascade_on_report_deletion(analysis_service):
    app, client, headers = analysis_service
    url = saved_brief(analysis_service)
    brief_id = url.split('/')[-2]
    cv, jd = upload(client, headers).json()['id'], upload(client, headers, 'jd').json()['id']
    client.post('/api/jobs', json={'jobType': 'personal', 'briefId': brief_id, 'cvDocumentId': cv, 'jdDocumentId': jd}, headers=headers)
    assert app.state.jobs.run_one()
    personal_id = client.get('/api/analyses').json()['personal'][0]['id']
    personal_url = f'/api/analyses/personal/{personal_id}/annotations'
    for endpoint in (url, personal_url):
        body = {'contentVersion': client.get(endpoint).json()['contentVersion'], 'start': 0, 'end': 4, 'quote': '문장😀', 'note': '메모'}
        assert client.post(endpoint, json=body, headers=headers).status_code == 201
    assert client.delete(url.removesuffix('/annotations'), headers=headers).status_code == 204
    with app.state.db.connect() as conn:
        assert conn.execute('SELECT COUNT(*) FROM report_annotations').fetchone()[0] == 0


def test_existing_database_migrates_without_losing_users(tmp_path):
    db = Database(tmp_path / 'old.sqlite3')
    with db.connect() as conn:
        from pathlib import Path
        conn.executescript(Path('backend/app/schema.sql').read_text(encoding='utf-8'))
        conn.execute("INSERT INTO users VALUES('u','sub','a@example.test','기존 사용자','today')")
    db.initialize()
    db.initialize()
    with db.connect() as conn:
        assert conn.execute('PRAGMA user_version').fetchone()[0] == 4
        assert conn.execute('SELECT name FROM users').fetchone()[0] == '기존 사용자'
        assert conn.execute('SELECT COUNT(*) FROM report_annotations').fetchone()[0] == 0
