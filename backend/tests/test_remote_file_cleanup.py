from types import SimpleNamespace
from unittest.mock import MagicMock

import httpx
from openai import APIConnectionError

from backend.app.db import Database
from backend.app.remote_file_cleanup import delete_next_file, record_upload


def test_failed_remote_deletion_survives_restart_and_retries(tmp_path, monkeypatch):
    clock = MagicMock(return_value=100)
    monkeypatch.setattr('backend.app.remote_file_cleanup.time.time', clock)
    sdk = MagicMock()
    monkeypatch.setattr('backend.app.remote_file_cleanup.OpenAI', sdk)
    delete = sdk.return_value.__enter__.return_value.files.delete
    delete.side_effect = [
        APIConnectionError(request=httpx.Request('DELETE', 'https://example.test')),
        SimpleNamespace(deleted=True),
    ]
    db = Database(tmp_path / 'service.sqlite3')
    db.initialize()
    record_upload(db, 'file-test', 'candidate-key')
    assert not delete_next_file(db, 'another-key')
    assert delete_next_file(db, 'candidate-key')

    restarted = Database(db.path)
    restarted.initialize()
    assert not delete_next_file(restarted, 'candidate-key')
    clock.return_value = 160
    assert delete_next_file(restarted, 'candidate-key')
    assert not delete_next_file(restarted, 'candidate-key')
    assert delete.call_count == 2
