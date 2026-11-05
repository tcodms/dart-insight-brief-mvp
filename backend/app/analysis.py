import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal
from urllib.parse import quote
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from starlette.responses import Response

from backend.app.auth import require_mutation, require_session
from backend.app.job_runner import BRIEF_KEYS, PERSONAL_KEYS, agent_settings, now
from backend.app.personal_evidence import candidate_evidence
from pipeline.brief_renderer import clean_saved_brief_markdown, render_company_brief

router = APIRouter(prefix='/api')
ERRORS = {
    'INTERRUPTED': '서버가 재시작되어 분석이 중단되었습니다. 필요하면 다시 실행해 주세요.',
    'TIMEOUT': '분석 제한 시간을 초과했습니다. 자동으로 재실행하지 않습니다.',
    'AGENT_AUTH': 'Agent 인증 또는 접근 권한을 확인해 주세요.',
    'AGENT_CREDIT': '분석 서비스의 크레딧이 부족합니다. 운영자 확인 후 다시 시도해 주세요.',
    'AGENT_CONNECTION': '분석 서비스에 연결하지 못했습니다. 잠시 후 다시 시도해 주세요.',
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
            if not body.briefId or not body.cvDocumentId or not body.jdDocumentId or body.reportDocumentId:
                raise HTTPException(422, '현재 기여 Agent는 기업 브리프·CV·JD가 모두 필요합니다.')
            brief = conn.execute('SELECT * FROM company_briefs WHERE id=? AND user_id=?', (body.briefId, owner)).fetchone()
            if not brief:
                raise HTTPException(404, '기업 브리프를 찾을 수 없습니다.')
            document(body.cvDocumentId, 'cv')
            jd = document(body.jdDocumentId, 'jd')
            target_role = body.targetRole.strip() or Path(jd['original_name']).stem[:120]
            report_id = brief['report_document_id']
        if body.jobType == 'brief':
            target_role = ''
        active = conn.execute("SELECT * FROM analysis_jobs WHERE user_id=? AND status IN ('queued','running')", (owner,)).fetchone()
        if active:
            # Double-clicks return the same job; a different request must wait.
            if (active['job_type'], active['report_document_id'], active['brief_id'], active['cv_document_id'], active['jd_document_id'], active['target_role']) == (body.jobType, report_id, body.briefId, body.cvDocumentId, body.jdDocumentId, target_role):
                return job_json(active)
            raise HTTPException(409, '이미 진행 중인 분석이 있습니다. 완료 후 실행해 주세요.')
        if conn.execute("SELECT COUNT(*) FROM analysis_jobs WHERE status IN ('queued','running')").fetchone()[0] >= 20:
            raise HTTPException(429, '분석 대기열이 가득 찼습니다. 잠시 후 시도해 주세요.')
        job_id = str(uuid4())
        conn.execute('''INSERT INTO analysis_jobs
            (id,user_id,job_type,report_document_id,brief_id,cv_document_id,jd_document_id,target_role,status,stage,created_at)
            VALUES(?,?,?,?,?,?,?,?,'queued','분석 대기 중',?)''',
            (job_id, owner, body.jobType, report_id, body.briefId, body.cvDocumentId, body.jdDocumentId, target_role, now()))
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


def brief_names(company, period):
    match = re.match(r'^(\d{4})(?:\b|년)', period or '')
    year = match[1] if match else ''
    label = f'{year}년 기업 브리프' if year else '기업 브리프'
    return f'{company} · {label}', '_'.join(filter(None, (company, year, '기업브리프')))


def personal_names(company, role, jd_name, created_at):
    if jd_name and role == Path(jd_name).stem[:120]:
        role = ''
    label = f'{role} 기여 보고서' if role else '기여 보고서'
    date = datetime.fromisoformat(created_at).astimezone(timezone(timedelta(hours=9))).date().isoformat()
    return f'{company} · {label}', '_'.join(filter(None, (company, role, '기여보고서', date)))


@router.get('/analyses')
def list_analyses(request: Request, session=Depends(require_session)):
    with request.app.state.db.connect() as conn:
        briefs = conn.execute('''SELECT b.id,b.company_name,b.report_document_id,b.created_at,d.original_name,
            json_extract(b.result_json, '$.brief.report_period') AS report_period FROM company_briefs b
            JOIN documents d ON d.id=b.report_document_id WHERE b.user_id=? ORDER BY b.created_at DESC''', (session['user_id'],)).fetchall()
        personal = conn.execute('''SELECT p.id,p.brief_id,p.target_role,p.cv_document_id,p.jd_document_id,p.created_at,b.company_name,d.version,
            jd.original_name AS jd_name
            FROM personal_analyses p JOIN company_briefs b ON b.id=p.brief_id JOIN documents d ON d.id=p.cv_document_id
            LEFT JOIN documents jd ON jd.id=p.jd_document_id
            WHERE p.user_id=? ORDER BY p.created_at DESC''', (session['user_id'],)).fetchall()
    return {'briefs': [{'id': row['id'], 'companyName': row['company_name'], 'reportDocumentId': row['report_document_id'],
                        'displayTitle': brief_names(row['company_name'], row['report_period'])[0],
                        'reportName': row['original_name'], 'createdAt': row['created_at']} for row in briefs],
            'personal': [{'id': row['id'], 'briefId': row['brief_id'], 'companyName': row['company_name'], 'targetRole': row['target_role'],
                          'displayTitle': personal_names(row['company_name'], row['target_role'], row['jd_name'], row['created_at'])[0],
                          'cvDocumentId': row['cv_document_id'], 'jdDocumentId': row['jd_document_id'], 'cvVersion': f"v{row['version']}", 'createdAt': row['created_at']} for row in personal]}


def result_record(kind, result_id, request, owner):
    table = 'company_briefs' if kind == 'brief' else 'personal_analyses'
    with request.app.state.db.connect() as conn:
        row = conn.execute(f'SELECT * FROM {table} WHERE id=? AND user_id=?', (result_id, owner)).fetchone()
        brief_row = row if kind == 'brief' else conn.execute('SELECT b.result_json,b.report_document_id,b.company_name FROM company_briefs b WHERE b.id=? AND b.user_id=?', (row['brief_id'], owner)).fetchone() if row else None
        jd = conn.execute('SELECT original_name FROM documents WHERE id=? AND user_id=?', (row['jd_document_id'], owner)).fetchone() if row and kind == 'personal' else None
        source_docs = {label: conn.execute('SELECT id,original_name,pages FROM documents WHERE id=? AND user_id=?', (row[label + '_document_id'], owner)).fetchone()
                       for label in ('cv', 'jd')} if row and kind == 'personal' else {}
    if not row:
        raise HTTPException(404, '분석 결과를 찾을 수 없습니다.')
    brief_result = json.loads(brief_row['result_json']) if brief_row else {}
    result = brief_result if kind == 'brief' else json.loads(row['result_json'])
    if kind == 'brief':
        title, filename = brief_names(row['company_name'], result.get('brief', {}).get('report_period'))
    else:
        title, filename = personal_names(brief_row['company_name'], row['target_role'], jd['original_name'] if jd else None, row['created_at'])
    filename = re.sub(r'[<>:"/\\|?*\x00-\x1f\x7f]', '_', filename)
    filename = filename.encode('utf-8')[:240].decode('utf-8', errors='ignore')
    evidence = brief_evidence(brief_result)
    if kind == 'personal':
        evidence = [{**item, 'sourceKind': 'report', 'documentId': brief_row['report_document_id'],
                     'sourceName': '사업보고서'} for item in evidence] if brief_row else []
        evidence += candidate_evidence(result.get('extracts'), source_docs)
    return {'id': row['id'], 'kind': kind, 'createdAt': row['created_at'],
            'displayTitle': title, 'downloadName': f'{filename}.md', 'jdName': jd['original_name'] if jd else None,
            'result': render_result(kind, result),
            'reportDocumentId': brief_row['report_document_id'] if brief_row else None,
            'evidence': evidence}


def brief_evidence(result):
    facts = result.get('facts', {}).get('facts', [])
    evidence = []
    for fact in facts:
        source = fact.get('evidence', {}) if isinstance(fact, dict) else {}
        page = source.get('original_page') if isinstance(source, dict) else None
        if isinstance(page, int) and page > 0 and source.get('quote') and fact.get('id'):
            evidence.append({'id': str(fact['id']), 'page': page, 'quote': str(source['quote']),
                             'section': str(source.get('section', ''))})
    return evidence


def render_result(kind, result):
    if kind == 'brief':
        if isinstance(result.get('brief'), dict) and result['brief'].get('evidence_ids'):
            result['markdown'] = render_company_brief(result['brief'])
        elif isinstance(result.get('markdown'), str):
            result['markdown'] = clean_saved_brief_markdown(result['markdown'])
    return result


@router.get('/analyses/{kind}/{result_id}')
def get_result(kind: Literal['brief', 'personal'], result_id: str, request: Request, session=Depends(require_session)):
    return result_record(kind, result_id, request, session['user_id'])


@router.get('/analyses/{kind}/{result_id}/impact')
def result_delete_impact(kind: Literal['brief', 'personal'], result_id: str, request: Request, session=Depends(require_session)):
    owner = session['user_id']
    table = 'company_briefs' if kind == 'brief' else 'personal_analyses'
    with request.app.state.db.connect() as conn:
        row = conn.execute(f'SELECT id FROM {table} WHERE id=? AND user_id=?', (result_id, owner)).fetchone()
        if not row:
            raise HTTPException(404, '분석 결과를 찾을 수 없습니다.')
        related = conn.execute('SELECT COUNT(*) FROM personal_analyses WHERE brief_id=? AND user_id=?', (result_id, owner)).fetchone()[0] if kind == 'brief' else 0
    return {'relatedPersonalAnalyses': related}


@router.delete('/analyses/{kind}/{result_id}', status_code=204)
def delete_result(kind: Literal['brief', 'personal'], result_id: str, request: Request, session=Depends(require_mutation)):
    owner = session['user_id']
    table = 'company_briefs' if kind == 'brief' else 'personal_analyses'
    with request.app.state.db.connect() as conn:
        conn.execute('BEGIN IMMEDIATE')
        row = conn.execute(f'SELECT id FROM {table} WHERE id=? AND user_id=?', (result_id, owner)).fetchone()
        if not row:
            raise HTTPException(404, '분석 결과를 찾을 수 없습니다.')
        if kind == 'brief':
            active = conn.execute("SELECT 1 FROM analysis_jobs WHERE user_id=? AND brief_id=? AND status IN ('queued','running')", (owner, result_id)).fetchone()
            if active:
                raise HTTPException(409, '이 기업 브리프를 사용하는 분석이 끝난 뒤 삭제할 수 있습니다.')
            related = conn.execute('SELECT id FROM personal_analyses WHERE brief_id=? AND user_id=?', (result_id, owner)).fetchall()
            result_ids = [result_id, *(item['id'] for item in related)]
        else:
            result_ids = [result_id]
        conn.executemany('DELETE FROM analysis_jobs WHERE user_id=? AND result_id=?', [(owner, item) for item in result_ids])
        conn.execute(f'DELETE FROM {table} WHERE id=? AND user_id=?', (result_id, owner))
    return Response(status_code=204)


@router.get('/analyses/{kind}/{result_id}/download')
def download_result(kind: Literal['brief', 'personal'], result_id: str, request: Request, session=Depends(require_session)):
    result = result_record(kind, result_id, request, session['user_id'])
    return Response(result['result']['markdown'], media_type='text/markdown; charset=utf-8',
                    headers={'Content-Disposition': f'attachment; filename="{kind}-{result_id}.md"; filename*=UTF-8\'\'{quote(result["downloadName"], safe="")}'})
