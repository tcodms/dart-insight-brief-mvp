from backend.app.public_briefs import publish
from backend.tests.test_analysis import analysis_service, start_brief
from backend.tests.test_service import sign_in, upload


def test_catalog_reads_public_versions_and_imports_once_per_account(analysis_service):
    app, client, alice = analysis_service
    directory = app.state.settings.data_dir / 'files'
    db = app.state.db
    _, job = start_brief(client, alice)
    assert app.state.jobs.run_one()
    source = client.get('/api/jobs/' + job['id']).json()['resultId']
    first = publish(db, directory, source, '00000001', '20260301000001', '2026-03-01')
    latest = publish(db, directory, source, '00000001', '20260302000001', '2026-03-02')
    url = f'/api/public-briefs/{latest}'
    assert [item['id'] for item in client.get('/api/public-briefs').json()['briefs']] == [latest]
    assert client.get(f'/api/public-briefs/{first}').status_code == 200
    assert client.get(url).json()['evidence'][0]['id'] == 'B01-E001'
    assert client.get(url + '/preview').content.startswith(b'%PDF-')
    assert client.post(url + '/import').status_code == 403
    imported = client.post(url + '/import', headers=alice).json()['briefId']
    assert client.post(url + '/import', headers=alice).json()['briefId'] == imported
    assert len(client.get('/api/documents').json()['documents']) == 2
    private_url = f'/api/analyses/brief/{imported}'
    assert client.get(private_url).json()['result']['markdown'] == client.get(url).json()['markdown']

    bob, _ = sign_in(app, client, 'bob')
    assert client.get(private_url).status_code == 404
    assert client.get(private_url + '/annotations').status_code == 404
    assert client.get('/api/documents').json()['documents'] == []
    bob_brief = client.post(url + '/import', headers=bob).json()['briefId']
    assert bob_brief != imported
    cv = upload(client, bob).json()['id']
    jd = upload(client, bob, 'jd').json()['id']
    personal = client.post('/api/jobs', headers=bob, json={
        'jobType': 'personal', 'briefId': bob_brief, 'cvDocumentId': cv, 'jdDocumentId': jd,
    })
    assert personal.status_code == 202
    assert app.state.jobs.run_one()
    assert client.get('/api/jobs/' + personal.json()['id']).json()['status'] == 'succeeded'
    client.cookies.clear()
    assert client.get(url + '/preview').status_code == 401
