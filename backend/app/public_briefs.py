"""Published company briefs and account-owned imports."""

import argparse
import json
import os
import re
from datetime import date, datetime, timezone
from pathlib import Path
from shutil import copyfileobj
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from starlette.responses import FileResponse

from backend.app.analysis import brief_evidence, render_result
from backend.app.auth import require_mutation, require_session
from backend.app.config import Settings
from backend.app.db import Database

router = APIRouter(prefix='/api/public-briefs')


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def copy_pdf(source: Path, target: Path):
    with source.open('rb') as original, target.open('xb') as copy:
        copyfileobj(original, copy)
        copy.flush()
        os.fsync(copy.fileno())


def metadata(row):
    return {
        'id': row['id'],
        'companyName': row['company_name'],
        'reportName': row['report_name'],
        'filedOn': row['filed_on'],
        'sourceUrl': f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={row['receipt_no']}",
    }


def find_public(conn, brief_id):
    row = conn.execute('SELECT * FROM public_briefs WHERE id=?', (brief_id,)).fetchone()
    if not row:
        raise HTTPException(404, '공용 브리프를 찾을 수 없습니다.')
    return row


@router.get('')
def list_public(request: Request, _session=Depends(require_session)):
    with request.app.state.db.connect() as conn:
        rows = conn.execute('''SELECT p.id,p.company_name,p.report_name,p.filed_on,p.receipt_no
            FROM public_briefs p
            WHERE p.id = (SELECT id FROM public_briefs WHERE corp_code=p.corp_code
                          ORDER BY filed_on DESC, receipt_no DESC LIMIT 1)
            ORDER BY p.company_name, p.corp_code''').fetchall()
    return {'briefs': [metadata(row) for row in rows]}


@router.get('/{brief_id}')
def read_public(brief_id: str, request: Request, _session=Depends(require_session)):
    with request.app.state.db.connect() as conn:
        row = find_public(conn, brief_id)
    result = render_result('brief', json.loads(row['result_json']), public=True)
    return {**metadata(row), 'markdown': result['markdown'], 'evidence': brief_evidence(result)}


@router.get('/{brief_id}/preview')
def preview_public(brief_id: str, request: Request, _session=Depends(require_session)):
    with request.app.state.db.connect() as conn:
        row = find_public(conn, brief_id)
    path = request.app.state.settings.data_dir / 'files' / 'public' / f"{row['id']}.pdf"
    if not path.is_file():
        raise HTTPException(404, '공용 원본 PDF를 찾을 수 없습니다.')
    return FileResponse(path, media_type='application/pdf', filename=row['report_name'],
                        content_disposition_type='inline')


@router.post('/{brief_id}/import')
def import_public(brief_id: str, request: Request, session=Depends(require_mutation)):
    owner = session['user_id']
    directory = request.app.state.settings.data_dir / 'files'
    target = None
    try:
        with request.app.state.db.connect() as conn:
            conn.execute('BEGIN IMMEDIATE')
            row = find_public(conn, brief_id)
            previous = conn.execute('''SELECT brief_id FROM public_brief_imports
                WHERE user_id=? AND public_brief_id=?''', (owner, brief_id)).fetchone()
            if previous:
                return {'briefId': previous['brief_id'], 'companyName': row['company_name']}
            source = directory / 'public' / f"{row['id']}.pdf"
            if not source.is_file():
                raise HTTPException(404, '공용 원본 PDF를 찾을 수 없습니다.')
            document_id, imported_id = str(uuid4()), str(uuid4())
            target = directory / f'{document_id}.pdf'
            copy_pdf(source, target)
            created_at = timestamp()
            imported_result = json.loads(row['result_json'])
            imported_result['approximate_won_amounts'] = True
            conn.execute('''INSERT INTO document_counters(user_id,kind,last_version) VALUES(?,'report',1)
                ON CONFLICT(user_id,kind) DO UPDATE SET last_version=last_version+1''', (owner,))
            version = conn.execute("SELECT last_version FROM document_counters WHERE user_id=? AND kind='report'", (owner,)).fetchone()[0]
            conn.execute('''INSERT INTO documents
                (id,user_id,kind,original_name,storage_key,version,content_hash,byte_size,pages,created_at)
                VALUES(?,?,'report',?,?,?,?,?,?,?)''',
                (document_id, owner, row['report_name'], target.name, version, row['content_hash'],
                 row['byte_size'], row['pages'], created_at))
            conn.execute('''INSERT INTO company_briefs
                (id,user_id,report_document_id,company_name,report_year,result_json,schema_version,created_at)
                VALUES(?,?,?,?,?,?,?,?)''',
                (imported_id, owner, document_id, row['company_name'], row['report_year'], json.dumps(imported_result, ensure_ascii=False),
                 row['schema_version'], created_at))
            for evidence in brief_evidence(imported_result):
                conn.execute('''INSERT INTO evidence(id,user_id,document_id,brief_id,page,quote,section)
                    VALUES(?,?,?,?,?,?,?)''', (str(uuid4()), owner, document_id, imported_id,
                                               evidence['page'], evidence['quote'], evidence['section']))
            conn.execute('INSERT INTO public_brief_imports VALUES(?,?,?)', (owner, brief_id, imported_id))
    except Exception:
        if target is not None:
            target.unlink(missing_ok=True)
        raise
    return {'briefId': imported_id, 'companyName': row['company_name']}


def publish(db: Database, directory: Path, source_id: str, corp_code: str, receipt_no: str, filed_on: str):
    if not re.fullmatch(r'[0-9]{8}', corp_code) or not re.fullmatch(r'[0-9]{14}', receipt_no):
        raise ValueError('DART 고유번호 8자리와 접수번호 14자리를 입력하세요.')
    filed_on = date.fromisoformat(filed_on).isoformat()
    target = None
    try:
        with db.connect() as conn:
            conn.execute('BEGIN IMMEDIATE')
            row = conn.execute('''SELECT b.*,d.original_name,d.storage_key,d.content_hash,d.byte_size,d.pages
                FROM company_briefs b JOIN documents d ON d.id=b.report_document_id AND d.user_id=b.user_id
                WHERE b.id=? AND d.kind='report' ''', (source_id,)).fetchone()
            if not row:
                raise ValueError('등록할 기업 브리프를 찾을 수 없습니다.')
            if conn.execute('SELECT 1 FROM public_briefs WHERE receipt_no=?', (receipt_no,)).fetchone():
                raise ValueError('이미 등록된 공시입니다.')
            result = render_result('brief', json.loads(row['result_json']))
            evidence = brief_evidence(result)
            if not result.get('markdown') or not evidence:
                raise ValueError('본문과 원문 근거가 있는 브리프만 등록할 수 있습니다.')
            if any(item['page'] > row['pages'] for item in evidence):
                raise ValueError('원문 PDF 범위를 벗어난 근거 쪽수가 있습니다.')
            public_id = str(uuid4())
            (directory / 'public').mkdir(parents=True, exist_ok=True)
            target = directory / 'public' / f'{public_id}.pdf'
            copy_pdf(directory / row['storage_key'], target)
            conn.execute('''INSERT INTO public_briefs
                (id,corp_code,receipt_no,company_name,filed_on,report_year,report_name,content_hash,
                 byte_size,pages,result_json,schema_version,published_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                (public_id, corp_code, receipt_no, row['company_name'], filed_on, row['report_year'],
                 row['original_name'], row['content_hash'], row['byte_size'], row['pages'], row['result_json'],
                 row['schema_version'], timestamp()))
    except Exception:
        if target is not None:
            target.unlink(missing_ok=True)
        raise
    return public_id


def main():
    parser = argparse.ArgumentParser(description='검토한 공개 DART 사업보고서 브리프를 공용 카탈로그에 등록합니다.')
    parser.add_argument('--brief-id', required=True)
    parser.add_argument('--corp-code', required=True)
    parser.add_argument('--receipt-no', required=True)
    parser.add_argument('--filed-on', required=True)
    parser.add_argument('--confirm-public-source', required=True, action='store_true',
                        help='브리프와 근거를 검토했고 원본이 공개 DART 공시임을 확인했습니다.')
    args = parser.parse_args()
    settings = Settings.from_env()
    db = Database(settings.data_dir / 'service.sqlite3')
    db.initialize()
    try:
        print(publish(db, settings.data_dir / 'files', args.brief_id, args.corp_code, args.receipt_no, args.filed_on))
    except (ValueError, FileNotFoundError) as exc:
        parser.exit(1, f'{exc}\n')


if __name__ == '__main__':
    main()
