"""Persist and retry deletion of Upstage files that contain candidate data."""

import hashlib
import logging
import time

from openai import NotFoundError, OpenAI, OpenAIError


logger = logging.getLogger(__name__)


def key_digest(api_key):
    return hashlib.sha256(api_key.encode()).hexdigest()


def record_upload(db, file_id, api_key):
    with db.connect() as conn:
        conn.execute('INSERT INTO remote_file_cleanup(file_id,key_digest) VALUES(?,?)',
                     (file_id, key_digest(api_key)))


def delete_next_file(db, api_key):
    """Call between analyses, when no local worker is using the pending files."""
    if not api_key:
        return False
    with db.connect() as conn:
        row = conn.execute('''SELECT file_id FROM remote_file_cleanup
            WHERE key_digest=? AND retry_after<=? ORDER BY retry_after, rowid LIMIT 1''',
                           (key_digest(api_key), int(time.time()))).fetchone()
    if row is None:
        return False
    file_id = row['file_id']
    try:
        with OpenAI(api_key=api_key, base_url='https://api.upstage.ai/v2', timeout=5, max_retries=0) as client:
            deleted = client.files.delete(file_id).deleted
    except NotFoundError:
        deleted = True
    except OpenAIError:
        deleted = False
    with db.connect() as conn:
        if deleted:
            conn.execute('DELETE FROM remote_file_cleanup WHERE file_id=?', (file_id,))
        else:
            conn.execute('UPDATE remote_file_cleanup SET retry_after=? WHERE file_id=?',
                         (int(time.time()) + 60, file_id))
            logger.warning('Upstage candidate file deletion failed; queued for retry')
    return True
