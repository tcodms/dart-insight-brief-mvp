import json

import pytest
from fastapi.testclient import TestClient

from backend.app.config import Settings
from backend.app.job_runner import BRIEF_KEYS, PERSONAL_KEYS, JobFailure
from backend.app.main import create_app
from backend.tests.test_service import sign_in, upload


@pytest.fixture
def analysis_service(tmp_path, monkeypatch):
    monkeypatch.setattr('backend.app.analysis.agent_settings', lambda: dict.fromkeys(BRIEF_KEYS + PERSONAL_KEYS, 'test-config'))

    def runner(request, directory, stopped):
        assert directory.is_relative_to(tmp_path / 'jobs')
        if request['job_type'] == 'brief':
            assert request['report_path'].endswith('report.pdf')
            return {'brief': {'company_name': '테스트 기업'}, 'markdown': '# 기업 브리프\n실제 결과 자리',
                    'facts': {'company_name': '테스트 기업', 'facts': [{'id': 'B01-E001', 'statement': '기업 활동',
                        'evidence': {'original_page': 1, 'quote': '확인한 문장', 'section': '사업'}}]}}
        assert json.loads((directory / 'company_facts.json').read_text(encoding='utf-8'))['company_name'] == '테스트 기업'
        return {'markdown': '# 개인화 보고서\n경험과 기업의 연결', 'extracts': {'cv': {}, 'jd': {}}}

    app = create_app(Settings(data_dir=tmp_path), start_jobs=False, job_runner=runner)
    with TestClient(app) as client:
        headers, _ = sign_in(app, client)
        yield app, client, headers


def start_brief(client, headers):
    report = upload(client, headers, 'report').json()['id']
    response = client.post('/api/jobs', json={'jobType': 'brief', 'reportDocumentId': report}, headers=headers)
    assert response.status_code == 202
    return report, response.json()


def test_brief_graph_persists_result_evidence_and_private_download(analysis_service):
    app, client, headers = analysis_service
    report, job = start_brief(client, headers)
    assert client.delete(f'/api/documents/{report}', headers=headers).status_code == 409
    assert app.state.jobs.run_one()
    done = client.get('/api/jobs/' + job['id']).json()
    assert done['status'] == 'succeeded'
    briefs = client.get('/api/analyses').json()['briefs']
    assert briefs[0]['id'] == done['resultId']
    result = client.get('/api/analyses/brief/' + done['resultId']).json()
    assert result['evidence'][0]['page'] == 1
    assert result['result']['facts']['facts'][0]['id'] == 'B01-E001'
    assert 'work_dir' not in json.dumps(result)
    download = client.get('/api/analyses/brief/' + done['resultId'] + '/download')
    assert '# 기업 브리프' in download.text and 'attachment' in download.headers['content-disposition']
    assert client.get(f'/api/documents/{report}/preview').headers['content-disposition'].startswith('inline')
    assert list((app.state.settings.data_dir / 'jobs').iterdir()) == []


def test_repeated_clicks_reuse_active_job_and_wrong_document_kind_is_rejected(analysis_service):
    app, client, headers = analysis_service
    report, job = start_brief(client, headers)
    repeated = client.post('/api/jobs', json={'jobType': 'brief', 'reportDocumentId': report}, headers=headers)
    assert repeated.json()['id'] == job['id']
    assert len(client.get('/api/jobs').json()['jobs']) == 1
    cv = upload(client, headers).json()['id']
    assert client.post('/api/jobs', json={'jobType': 'brief', 'reportDocumentId': cv}, headers=headers).status_code == 404


def test_personal_uses_selected_brief_and_requires_jd_then_cv_delete_preserves_brief(analysis_service):
    app, client, headers = analysis_service
    _, brief_job = start_brief(client, headers)
    app.state.jobs.run_one()
    brief_id = client.get('/api/jobs/' + brief_job['id']).json()['resultId']
    cv, jd = upload(client, headers).json()['id'], upload(client, headers, 'jd').json()['id']
    body = {'jobType': 'personal', 'briefId': brief_id, 'cvDocumentId': cv, 'targetRole': '데이터 분석'}
    assert client.post('/api/jobs', json=body, headers=headers).status_code == 422
    response = client.post('/api/jobs', json={**body, 'jdDocumentId': jd}, headers=headers)
    assert response.status_code == 202
    app.state.jobs.run_one()
    personal = client.get('/api/analyses').json()['personal'][0]
    assert personal['cvDocumentId'] == cv and personal['jdDocumentId'] == jd
    assert client.get('/api/analyses/personal/' + personal['id']).json()['result']['extracts'] == {'cv': {}, 'jd': {}}
    assert client.delete('/api/documents/' + cv, headers=headers).status_code == 204
    assert client.get('/api/analyses').json()['personal'] == []
    assert client.get('/api/analyses/brief/' + brief_id).status_code == 200


def test_another_user_cannot_start_or_read_analyses(analysis_service):
    app, client, headers = analysis_service
    report, job = start_brief(client, headers)
    app.state.jobs.run_one()
    result_id = client.get('/api/jobs/' + job['id']).json()['resultId']
    bob_headers, _ = sign_in(app, client, 'bob')
    assert client.get('/api/jobs').json()['jobs'] == []
    assert client.get('/api/analyses').json() == {'briefs': [], 'personal': []}
    assert client.get('/api/jobs/' + job['id']).status_code == 404
    assert client.get('/api/analyses/brief/' + result_id).status_code == 404
    assert client.get('/api/analyses/brief/' + result_id + '/download').status_code == 404
    assert client.post('/api/jobs', json={'jobType': 'brief', 'reportDocumentId': report}, headers=bob_headers).status_code == 404


def test_failure_has_safe_message_no_partial_result_and_no_temp_files(analysis_service):
    app, client, headers = analysis_service
    _, job = start_brief(client, headers)

    def failed(*args):
        raise RuntimeError('provider secret should never reach the UI')

    app.state.jobs.runner = failed
    app.state.jobs.run_one()
    response = client.get('/api/jobs/' + job['id']).json()
    assert response['status'] == 'failed' and response['error']
    assert 'provider secret' not in json.dumps(response)
    assert response['resultId'] is None
    assert client.get('/api/analyses').json()['briefs'] == []
    assert list((app.state.settings.data_dir / 'jobs').iterdir()) == []


def test_restart_marks_inflight_job_failed_instead_of_repeating_agent_calls(analysis_service):
    app, client, headers = analysis_service
    _, job = start_brief(client, headers)
    with app.state.db.connect() as conn:
        conn.execute("UPDATE analysis_jobs SET status='running' WHERE id=?", (job['id'],))
    app.state.jobs.start()
    app.state.jobs.close()
    response = client.get('/api/jobs/' + job['id']).json()
    assert response['status'] == 'failed' and '재시작' in response['error']
