import hashlib
import io
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from pypdf import PdfReader
from starlette.concurrency import run_in_threadpool
from starlette.responses import FileResponse, Response

from backend.app.auth import require_mutation, require_session

router = APIRouter(prefix='/api')


def document_json(row):
    return {'id': row['id'], 'name': row['original_name'], 'kind': row['kind'],
            'version': f"v{row['version']}", 'date': row['created_at'][:10].replace('-', '.'),
            'createdAt': row['created_at'], 'pages': row['pages'], 'bytes': row['byte_size']}


def owned_document(db, document_id, user_id):
    with db.connect() as conn:
        row = conn.execute('SELECT * FROM documents WHERE id=? AND user_id=?', (document_id, user_id)).fetchone()
    if not row:
        raise HTTPException(404, '자료를 찾을 수 없습니다.')
    return row


@router.get('/documents')
def list_documents(request: Request, session=Depends(require_session)):
    with request.app.state.db.connect() as conn:
        rows = conn.execute('SELECT * FROM documents WHERE user_id=? ORDER BY created_at DESC,id DESC', (session['user_id'],)).fetchall()
    return {'documents': [document_json(row) for row in rows]}


def persist_pdf(request, payload, filename, kind, user_id):
    if not payload.startswith(b'%PDF-'):
        raise HTTPException(422, '올바른 PDF 파일이 아닙니다.')
    try:
        reader = PdfReader(io.BytesIO(payload), strict=True)
        if reader.is_encrypted:
            raise HTTPException(422, '암호가 걸린 PDF는 등록할 수 없습니다.')
        pages = len(reader.pages)
        if pages < 1 or pages > 2000:
            raise HTTPException(422, '1~2,000쪽 PDF만 등록할 수 있습니다.')
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(422, 'PDF를 읽을 수 없습니다. 파일을 확인해 주세요.') from None
    name = re.sub(r'[\x00-\x1f\x7f]', '', filename.replace('\\', '/').rsplit('/', 1)[-1])[:180]
    doc_id = str(uuid4())
    storage_key = doc_id + '.pdf'
    path = request.app.state.settings.data_dir / 'files' / storage_key
    try:
        with path.open('xb') as output:
            output.write(payload)
            output.flush()
            os.fsync(output.fileno())
        with request.app.state.db.connect() as conn:
            conn.execute('BEGIN IMMEDIATE')
            conn.execute('''INSERT INTO document_counters(user_id,kind,last_version) VALUES(?,?,1)
                ON CONFLICT(user_id,kind) DO UPDATE SET last_version=last_version+1''', (user_id, kind))
            version = conn.execute('SELECT last_version FROM document_counters WHERE user_id=? AND kind=?', (user_id, kind)).fetchone()[0]
            conn.execute('''INSERT INTO documents
                (id,user_id,kind,original_name,storage_key,version,content_hash,byte_size,pages,created_at)
                VALUES(?,?,?,?,?,?,?,?,?,?)''', (doc_id, user_id, kind, name, storage_key, version,
                hashlib.sha256(payload).hexdigest(), len(payload), pages, datetime.now(timezone.utc).isoformat()))
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return document_json(owned_document(request.app.state.db, doc_id, user_id))


@router.post('/documents', status_code=201)
async def upload_document(request: Request, kind: Literal['report', 'cv', 'jd'] = Form(...),
                          file: UploadFile = File(...), session=Depends(require_mutation)):
    try:
        if not file.filename or not file.filename.lower().endswith('.pdf'):
            raise HTTPException(422, 'PDF 파일을 선택해 주세요.')
        payload = bytearray()
        while chunk := await file.read(64 * 1024):
            payload.extend(chunk)
            if len(payload) > request.app.state.settings.max_upload_bytes:
                raise HTTPException(413, 'PDF는 20MB 이하만 등록할 수 있습니다.')
        return await run_in_threadpool(persist_pdf, request, bytes(payload), file.filename, kind, session['user_id'])
    finally:
        await file.close()


@router.get('/documents/{document_id}/file')
def download_document(document_id: str, request: Request, session=Depends(require_session)):
    row = owned_document(request.app.state.db, document_id, session['user_id'])
    path = request.app.state.settings.data_dir / 'files' / row['storage_key']
    if not path.is_file():
        raise HTTPException(404, '원본 파일을 찾을 수 없습니다.')
    return FileResponse(path, media_type='application/pdf', filename=row['original_name'], content_disposition_type='attachment')


@router.get('/documents/{document_id}/impact')
def deletion_impact(document_id: str, request: Request, session=Depends(require_session)):
    row = owned_document(request.app.state.db, document_id, session['user_id'])
    with request.app.state.db.connect() as conn:
        briefs = conn.execute('SELECT COUNT(*) FROM company_briefs WHERE user_id=? AND report_document_id=?', (session['user_id'], document_id)).fetchone()[0]
        personal = conn.execute('''SELECT COUNT(*) FROM personal_analyses WHERE user_id=? AND
            (cv_document_id=? OR jd_document_id=? OR brief_id IN
             (SELECT id FROM company_briefs WHERE user_id=? AND report_document_id=?))''',
            (session['user_id'], document_id, document_id, session['user_id'], document_id)).fetchone()[0]
    return {'briefs': briefs, 'personalAnalyses': personal, 'preservesBriefs': row['kind'] != 'report'}


@router.delete('/documents/{document_id}', status_code=204)
def delete_document(document_id: str, request: Request, session=Depends(require_mutation)):
    row = owned_document(request.app.state.db, document_id, session['user_id'])
    path = request.app.state.settings.data_dir / 'files' / row['storage_key']
    trash = path.with_suffix('.trash')
    moved = False
    try:
        with request.app.state.db.connect() as conn:
            conn.execute('BEGIN IMMEDIATE')
            if path.exists():
                path.replace(trash)
                moved = True
            conn.execute('DELETE FROM documents WHERE id=? AND user_id=?', (document_id, session['user_id']))
    except Exception:
        if moved:
            trash.replace(path)
        raise
    if moved:
        trash.unlink(missing_ok=True)
    return Response(status_code=204)
