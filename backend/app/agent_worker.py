"""One isolated process per analysis. Never return internal file paths to the UI."""

import json
import sys
from pathlib import Path

from backend.app.db import Database


def execute(request: dict, progress):
    import config

    # Rebind before importing legacy services, which import these constants by value.
    root = Path(request['work_dir'])
    config.DATA_DIR = root / 'data'
    config.OUTPUT_DIR = root / 'output'
    config.RESULT_DIR = root / 'result'
    config.RUNS_DIR = root / 'output' / 'runs'
    config.CANDIDATE_RUNS_DIR = root / 'output' / 'candidate_runs'
    if request['job_type'] == 'brief':
        from service import run_company_brief_pipeline
        result = run_company_brief_pipeline(request['report_path'], source_document_name=request['report_name'], progress=progress)
        return {'brief': result['company_brief'], 'facts': result['merged_company_data'],
                'markdown': result['company_brief_markdown']}
    from contribution_service import run_contribution_pipeline
    merged = json.loads(Path(request['facts_path']).read_text(encoding='utf-8'))
    merged['limitations'] = list(merged.get('limitations') or []) + [
        '서비스 사용자 입력 · 지원 직무: ' + request['target_role'] + '. 이 값은 사용자 요청 정보이며 기업 사실이나 JD 원문이 아닙니다.'
    ]
    contextual_facts = root / 'facts_with_user_context.json'
    contextual_facts.write_text(json.dumps(merged, ensure_ascii=False), encoding='utf-8')
    result = run_contribution_pipeline(request['cv_path'], request['jd_path'], contextual_facts, progress=progress)
    extracts = {}
    for kind in ('cv', 'jd'):
        path = Path(result['paths'][kind + '_json']).resolve()
        if not path.is_relative_to(root.resolve()):
            raise ValueError('Unexpected result path')
        extracts[kind] = json.loads(path.read_text(encoding='utf-8'))
    return {'markdown': result['report'], 'extracts': extracts}


def main():
    path = Path(sys.argv[1])
    request = json.loads(path.read_text(encoding='utf-8'))
    db = Database(Path(request['database']))

    def progress(message):
        import re
        text = re.sub(r'job_[A-Za-z0-9_-]+', '', str(message))[:180]
        with db.connect() as conn:
            conn.execute("UPDATE analysis_jobs SET stage=? WHERE id=? AND status='running'", (text, request['job_id']))

    try:
        output = {'result': execute(request, progress)}
    except Exception as error:
        name = type(error).__name__
        code = {'AuthenticationError': 'AGENT_AUTH', 'PermissionDeniedError': 'AGENT_AUTH',
                'RateLimitError': 'AGENT_RATE_LIMIT', 'BadRequestError': 'AGENT_REQUEST',
                'TimeoutError': 'TIMEOUT', 'APITimeoutError': 'TIMEOUT',
                'ModuleNotFoundError': 'DEPENDENCIES_MISSING', 'ValueError': 'INVALID_RESULT',
                'MergeValidationError': 'INVALID_RESULT'}.get(name, 'AGENT_FAILED')
        output = {'error': code}
    path.with_name('response.json').write_text(json.dumps(output, ensure_ascii=False), encoding='utf-8')


if __name__ == '__main__':
    main()
