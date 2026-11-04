"""Private reading annotations, separate from generated report content."""
from hashlib import sha256
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, model_validator
from starlette.responses import Response

from backend.app.analysis import result_record
from backend.app.auth import require_mutation, require_session
from backend.app.job_runner import now

router = APIRouter(prefix='/api/analyses')
Kind = Literal['brief', 'personal']


class AnnotationInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    contentVersion: str = Field(pattern=r'^[a-f0-9]{64}$')
    start: int = Field(ge=0, le=2_000_000)
    end: int = Field(gt=0, le=2_000_000)
    quote: str = Field(min_length=1, max_length=10_000)
    note: str = Field(default='', max_length=5_000)

    @model_validator(mode='after')
    def valid_range(self):
        if self.end <= self.start or self.end - self.start != len(self.quote.encode('utf-16-le')) // 2 or not self.quote.strip():
            raise ValueError('선택한 문장 범위를 확인해 주세요.')
        return self


class NoteInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    note: str = Field(max_length=5_000)


def report_version(kind, result_id, request, owner):
    record = result_record(kind, result_id, request, owner)
    return sha256(record['result']['markdown'].encode('utf-8')).hexdigest()


def annotation_json(row):
    return {'id': row['id'], 'start': row['start_offset'], 'end': row['end_offset'],
            'quote': row['quote'], 'note': row['note'], 'createdAt': row['created_at']}


@router.get('/{kind}/{result_id}/annotations')
def list_annotations(kind: Kind, result_id: str, request: Request, session=Depends(require_session)):
    owner = session['user_id']
    version = report_version(kind, result_id, request, owner)
    column = 'brief_id' if kind == 'brief' else 'personal_analysis_id'
    with request.app.state.db.connect() as conn:
        rows = conn.execute(f'SELECT * FROM report_annotations WHERE {column}=? AND user_id=? AND content_version=? ORDER BY start_offset,created_at,id',
                            (result_id, owner, version)).fetchall()
    return {'contentVersion': version, 'annotations': [annotation_json(row) for row in rows]}


@router.post('/{kind}/{result_id}/annotations', status_code=201)
def create_annotation(kind: Kind, result_id: str, body: AnnotationInput, request: Request, session=Depends(require_mutation)):
    owner = session['user_id']
    if report_version(kind, result_id, request, owner) != body.contentVersion:
        raise HTTPException(409, '보고서가 변경되었습니다. 다시 열고 문장을 선택해 주세요.')
    column = 'brief_id' if kind == 'brief' else 'personal_analysis_id'
    annotation_id = str(uuid4())
    with request.app.state.db.connect() as conn:
        conn.execute('BEGIN IMMEDIATE')
        if conn.execute(f'SELECT COUNT(*) FROM report_annotations WHERE {column}=? AND user_id=?', (result_id, owner)).fetchone()[0] >= 500:
            raise HTTPException(409, '보고서당 최대 500개의 하이라이트를 저장할 수 있습니다.')
        if conn.execute(f'''SELECT 1 FROM report_annotations WHERE {column}=? AND user_id=?
                            AND content_version=? AND start_offset<? AND end_offset>?''',
                        (result_id, owner, body.contentVersion, body.end, body.start)).fetchone():
            raise HTTPException(409, '이미 강조된 문장입니다. 기존 하이라이트에 메모를 추가해 주세요.')
        conn.execute(f'''INSERT INTO report_annotations
            (id,user_id,{column},content_version,start_offset,end_offset,quote,note,created_at)
            VALUES(?,?,?,?,?,?,?,?,?)''',
            (annotation_id, owner, result_id, body.contentVersion, body.start, body.end, body.quote, body.note.strip(), now()))
        row = conn.execute('SELECT * FROM report_annotations WHERE id=?', (annotation_id,)).fetchone()
    return annotation_json(row)


@router.patch('/{kind}/{result_id}/annotations/{annotation_id}')
def update_annotation(kind: Kind, result_id: str, annotation_id: str, body: NoteInput, request: Request, session=Depends(require_mutation)):
    report_version(kind, result_id, request, session['user_id'])
    column = 'brief_id' if kind == 'brief' else 'personal_analysis_id'
    with request.app.state.db.connect() as conn:
        row = conn.execute(f'SELECT * FROM report_annotations WHERE id=? AND {column}=? AND user_id=?', (annotation_id, result_id, session['user_id'])).fetchone()
        if not row:
            raise HTTPException(404, '메모를 찾을 수 없습니다.')
        conn.execute('UPDATE report_annotations SET note=? WHERE id=?', (body.note.strip(), annotation_id))
        row = conn.execute('SELECT * FROM report_annotations WHERE id=?', (annotation_id,)).fetchone()
    return annotation_json(row)


@router.delete('/{kind}/{result_id}/annotations/{annotation_id}', status_code=204)
def delete_annotation(kind: Kind, result_id: str, annotation_id: str, request: Request, session=Depends(require_mutation)):
    report_version(kind, result_id, request, session['user_id'])
    column = 'brief_id' if kind == 'brief' else 'personal_analysis_id'
    with request.app.state.db.connect() as conn:
        deleted = conn.execute(f'DELETE FROM report_annotations WHERE id=? AND {column}=? AND user_id=?', (annotation_id, result_id, session['user_id']))
        if not deleted.rowcount:
            raise HTTPException(404, '메모를 찾을 수 없습니다.')
    return Response(status_code=204)
