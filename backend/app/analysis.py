import json
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from starlette.responses import Response

from backend.app.auth import require_mutation, require_session
from backend.app.job_runner import BRIEF_KEYS, PERSONAL_KEYS, agent_settings, now

router = APIRouter(prefix='/api')
ERRORS = {
    'INTERRUPTED': '서버가 재시작되어 분석이 중단되었습니다. 필요하면 다시 실행해 주세요.',
    'TIMEOUT': '분석 제한 시간을 초과했습니다. 자동으로 재실행하지 않습니다.',
    'AGENT_AUTH': 'Agent 인증 또는 접근 권한을 확인해 주세요.',
    'AGENT_RATE_LIMIT': 'Agent 요청 한도에 도달했습니다. 잠시 후 다시 시도해 주세요.',
    'AGENT_REQUEST': 'Agent ID·Config 설정과 입력 문서 형식을 확인해 주세요.',
    'INVALID_RESULT': 'Agent 응답 형식이나 문서 구조를 확인하지 못했습니다.',
    'INPUT_MISSING': '분석에 필요한 자료를 찾을 수 없습니다.',
    'DEPENDENCIES_MISSING': '서버의 Agent 실행 패키지가 준비되지 않았습니다.',
    'AGENT_FAILED': 'Agent 분석을 완료하지 못했습니다. 설정과 문서를 확인한 뒤 다시 시도해 주세요.',
}


class AnalysisInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    jobType: Literal['brief', 'personal']
    reportDocumentId: str | None = Field(default=None, max_length=80)
    briefId: str | None = Field(default=None, max_length=80)
    cvDocumentId: str | None = Field(default=None, max_length=80)
    jdDocumentId: str | None = Field(default=None, max_length=80)
    targetRole: str = Field(default='', max_length=120)


def job_json(row):
    return {'id': row['id'], 'jobType': row['job_type'], 'status': row['status'], 'stage': row['stage'],
            'resultId': row['result_id'], 'reportDocumentId': row['report_document_id'],
            'briefId': row['brief_id'], 'cvDocumentId': row['cv_document_id'], 'jdDocumentId': row['jd_document_id'],
            'targetRole': row['target_role'], 'createdAt': row['created_at'], 'finishedAt': row['finished_at'],
            'error': ERRORS.get(row['error_code'], ERRORS['AGENT_FAILED']) if row['error_code'] else None}


@router.get('/analysis/capabilities')
def capabilities(session=Depends(require_session)):
    values = agent_settings()
    return {'briefConfigured': all(values[key] for key in BRIEF_KEYS),
            'personalConfigured': all(values[key] for key in PERSONAL_KEYS), 'personalRequiresJd': True}


@router.post('/jobs', status_code=202)
def start_analysis(body: AnalysisInput, request: Request, session=Depends(require_mutation)):
    values = agent_settings()
    keys = BRIEF_KEYS if body.jobType == 'brief' else PERSONAL_KEYS
    if not all(values[key] for key in keys):
        raise HTTPException(503, 'Agent 실행 설정이 준비되지 않았습니다.')
    owner = session['user_id']
    with request.app.state.db.connect() as conn:
        conn.execute('BEGIN IMMEDIATE')

        def document(doc_id, kind):
            row = conn.execute('SELECT * FROM documents WHERE id=? AND user_id=? AND kind=?', (doc_id, owner, kind)).fetchone()
            if not row:
                raise HTTPException(404, f'{kind} 자료를 찾을 수 없습니다.')
            return row

        report_id = body.reportDocumentId
        if body.jobType == 'brief':
            if not report_id or body.briefId or body.cvDocumentId or body.jdDocumentId:
                raise HTTPException(422, '사업보고서 하나를 선택해 주세요.')
            document(report_id, 'report')
        else:
            if not body.briefId or not body.cvDocumentId or not body.jdDocumentId or not body.targetRole.strip() or body.reportDocumentId:
                raise HTTPException(422, '현재 기여 Agent는 기업 브리프·CV·JD·지원 직무가 모두 필요합니다.')
            brief = conn.execute('SELECT * FROM company_briefs WHERE id=? AND user_id=?', (body.briefId, owner)).fetchone()
            if not brief:
                raise HTTPException(404, '기업 브리프를 찾을 수 없습니다.')
            document(body.cvDocumentId, 'cv')
            document(body.jdDocumentId, 'jd')
            report_id = brief['report_document_id']
        active = conn.execute("SELECT * FROM analysis_jobs WHERE user_id=? AND status IN ('queued','running')", (owner,)).fetchone()
        if active:
            # Double-clicks return the same job; a different request must wait.
            if (active['job_type'], active['report_document_id'], active['brief_id'], active['cv_document_id'], active['jd_document_id'], active['target_role']) == (body.jobType, report_id, body.briefId, body.cvDocumentId, body.jdDocumentId, body.targetRole.strip()):
                return job_json(active)
            raise HTTPException(409, '이미 진행 중인 분석이 있습니다. 완료 후 실행해 주세요.')
        if conn.execute("SELECT COUNT(*) FROM analysis_jobs WHERE status IN ('queued','running')").fetchone()[0] >= 20:
            raise HTTPException(429, '분석 대기열이 가득 찼습니다. 잠시 후 시도해 주세요.')
        job_id = str(uuid4())
        conn.execute('''INSERT INTO analysis_jobs
            (id,user_id,job_type,report_document_id,brief_id,cv_document_id,jd_document_id,target_role,status,stage,created_at)
            VALUES(?,?,?,?,?,?,?,?,'queued','분석 대기 중',?)''',
            (job_id, owner, body.jobType, report_id, body.briefId, body.cvDocumentId, body.jdDocumentId, body.targetRole.strip(), now()))
        row = conn.execute('SELECT * FROM analysis_jobs WHERE id=?', (job_id,)).fetchone()
    request.app.state.jobs.wake.set()
    return job_json(row)


@router.get('/jobs')
def list_jobs(request: Request, session=Depends(require_session)):
    with request.app.state.db.connect() as conn:
        rows = conn.execute('SELECT * FROM analysis_jobs WHERE user_id=? ORDER BY created_at DESC,id DESC LIMIT 30', (session['user_id'],)).fetchall()
    return {'jobs': [job_json(row) for row in rows]}


@router.get('/jobs/{job_id}')
def get_job(job_id: str, request: Request, session=Depends(require_session)):
    with request.app.state.db.connect() as conn:
        row = conn.execute('SELECT * FROM analysis_jobs WHERE id=? AND user_id=?', (job_id, session['user_id'])).fetchone()
    if not row:
        raise HTTPException(404, '작업을 찾을 수 없습니다.')
    return job_json(row)


@router.get('/analyses')
def list_analyses(request: Request, session=Depends(require_session)):
    with request.app.state.db.connect() as conn:
        briefs = conn.execute('''SELECT b.id,b.company_name,b.report_document_id,b.created_at,d.original_name FROM company_briefs b
            JOIN documents d ON d.id=b.report_document_id WHERE b.user_id=? ORDER BY b.created_at DESC''', (session['user_id'],)).fetchall()
        personal = conn.execute('''SELECT p.id,p.brief_id,p.target_role,p.cv_document_id,p.jd_document_id,p.created_at,b.company_name,d.version
            FROM personal_analyses p JOIN company_briefs b ON b.id=p.brief_id JOIN documents d ON d.id=p.cv_document_id
            WHERE p.user_id=? ORDER BY p.created_at DESC''', (session['user_id'],)).fetchall()
    return {'briefs': [{'id': row['id'], 'companyName': row['company_name'], 'reportDocumentId': row['report_document_id'],
                        'reportName': row['original_name'], 'createdAt': row['created_at']} for row in briefs],
            'personal': [{'id': row['id'], 'briefId': row['brief_id'], 'companyName': row['company_name'], 'targetRole': row['target_role'],
                          'cvDocumentId': row['cv_document_id'], 'jdDocumentId': row['jd_document_id'], 'cvVersion': f"v{row['version']}", 'createdAt': row['created_at']} for row in personal]}


def result_record(kind, result_id, request, owner):
    table = 'company_briefs' if kind == 'brief' else 'personal_analyses'
    with request.app.state.db.connect() as conn:
        row = conn.execute(f'SELECT * FROM {table} WHERE id=? AND user_id=?', (result_id, owner)).fetchone()
        evidence = conn.execute('SELECT id,page,quote,section FROM evidence WHERE user_id=? AND brief_id=? ORDER BY page', (owner, result_id)).fetchall() if kind == 'brief' else []
    if not row:
        raise HTTPException(404, '분석 결과를 찾을 수 없습니다.')
    return {'id': row['id'], 'kind': kind, 'createdAt': row['created_at'], 'result': json.loads(row['result_json']),
            'reportDocumentId': row['report_document_id'] if kind == 'brief' else None,
            'evidence': [dict(item) for item in evidence]}


@router.get('/analyses/{kind}/{result_id}')
def get_result(kind: Literal['brief', 'personal'], result_id: str, request: Request, session=Depends(require_session)):
    return result_record(kind, result_id, request, session['user_id'])


@router.get('/analyses/{kind}/{result_id}/download')
def download_result(kind: Literal['brief', 'personal'], result_id: str, request: Request, session=Depends(require_session)):
    result = result_record(kind, result_id, request, session['user_id'])
    return Response(result['result']['markdown'], media_type='text/markdown; charset=utf-8',
                    headers={'Content-Disposition': f'attachment; filename="{kind}-{result_id}.md"'})
