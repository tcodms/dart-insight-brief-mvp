import json
from hashlib import sha256

from backend.tests.test_analysis import analysis_service, start_brief
from backend.tests.test_service import upload


RAW = '# 기여 보고서\n\n## 핵심 요약\n\n- **가장 강한 연결:** 실습 경험입니다.\n- **준비할 부분:** GMP 경험 없음.\n- **회사 맥락:** 기업 사실입니다.'


def saved_personal(service):
    app, client, headers = service
    _, job = start_brief(client, headers)
    app.state.jobs.run_one()
    brief_id = client.get('/api/jobs/' + job['id']).json()['resultId']
    cv, jd = upload(client, headers).json()['id'], upload(client, headers, 'jd').json()['id']
    job = client.post('/api/jobs', json={'jobType': 'personal', 'briefId': brief_id,
        'cvDocumentId': cv, 'jdDocumentId': jd}, headers=headers).json()
    app.state.jobs.run_one()
    result_id = client.get('/api/jobs/' + job['id']).json()['resultId']
    with app.state.db.connect() as conn:
        conn.execute('UPDATE personal_analyses SET result_json=? WHERE id=?', (json.dumps({'markdown': RAW, 'extracts': {'cv': {}, 'jd': {}}}), result_id))
    return result_id, f'/api/analyses/personal/{result_id}'


def test_existing_report_display_and_download_are_polished_without_changing_db(analysis_service):
    app, client, headers = analysis_service
    result_id, url = saved_personal(analysis_service)
    shown = client.get(url).json()['result']['markdown']
    assert '**활용할 경험:**' in shown and '**지원 방향:**' in shown
    assert client.get(url + '/download').text == shown
    with app.state.db.connect() as conn:
        saved = json.loads(conn.execute('SELECT result_json FROM personal_analyses WHERE id=?', (result_id,)).fetchone()[0])
    assert saved['markdown'] == RAW
    version = client.get(url + '/annotations').json()['contentVersion']
    response = client.post(url + '/annotations', json={'contentVersion': version, 'start': 0, 'end': 2, 'quote': '기여', 'note': '새 메모'}, headers=headers)
    assert response.status_code == 201
    assert client.get(url).json()['result']['markdown'] == shown
    notes = client.get(url + '/annotations').json()
    assert notes['contentVersion'] == version and len(notes['annotations']) == 1


def test_original_wording_is_kept_when_old_annotations_depend_on_it(analysis_service):
    app, client, _ = analysis_service
    result_id, url = saved_personal(analysis_service)
    version = sha256(RAW.encode('utf-8')).hexdigest()
    with app.state.db.connect() as conn:
        owner = conn.execute('SELECT user_id FROM personal_analyses WHERE id=?', (result_id,)).fetchone()[0]
        conn.execute('''INSERT INTO report_annotations(id,user_id,personal_analysis_id,content_version,start_offset,end_offset,quote,note,created_at)
            VALUES(?,?,?,?,?,?,?,?,?)''', ('legacy-note', owner, result_id, version, 0, 2, '기여', '기존 메모', '2026-11-06T00:00:00+00:00'))
    assert client.get(url).json()['result']['markdown'] == RAW
    listing = client.get(url + '/annotations').json()
    assert listing['contentVersion'] == version
    assert listing['annotations'][0]['note'] == '기존 메모'
