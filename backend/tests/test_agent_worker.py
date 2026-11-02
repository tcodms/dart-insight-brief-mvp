import json

from backend.app import agent_worker


def test_worker_keeps_private_failure_location_without_error_content(tmp_path, monkeypatch):
    request = tmp_path / 'request.json'
    request.write_text(json.dumps({'database': str(tmp_path / 'service.sqlite3')}))

    def fail(request, progress):
        raise ValueError('private document text and secret key')

    monkeypatch.setattr(agent_worker, 'execute', fail)
    monkeypatch.setattr('sys.argv', ['agent_worker', str(request)])
    agent_worker.main()

    response = json.loads(request.with_name('response.json').read_text())
    assert response['error'] == 'INVALID_RESULT'
    assert response['diagnostic']['type'] == 'ValueError'
    assert any(frame.endswith(':fail') for frame in response['diagnostic']['frames'])
    assert 'private document text' not in json.dumps(response)
    assert 'secret key' not in json.dumps(response)
