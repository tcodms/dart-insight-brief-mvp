import json

import httpx
import pytest
from openai import AuthenticationError, PermissionDeniedError, RateLimitError

from backend.app.agent_errors import diagnose_error, progress_stage
from pipeline.service import ExtractAgentError


def provider_error(cls, status, message, code='api_key_is_not_allowed'):
    request = httpx.Request('POST', 'https://api.upstage.ai/v2/responses',
                            headers={'Authorization': 'Bearer secret-test-key'})
    response = httpx.Response(status, request=request)
    return cls(message, response=response, body={'error': {'message': message, 'code': code}})


def test_credit_reason_survives_parallel_wrapper_without_leaking_provider_message():
    message = 'API key suspended due to insufficient credit. secret-test-key private CV text'
    error = provider_error(PermissionDeniedError, 403, message)
    wrapped = ExtractAgentError([
        ('3/6 Agent 2 재무·경영진단 추출', ValueError('private PDF content')),
        ('2/6 Agent 1 사업·전략 추출', error),
    ])
    code, diagnostics = diagnose_error(wrapped, 'extract')
    assert code == 'AGENT_CREDIT'
    assert diagnostics['stage'] == '사업·전략 추출'
    assert len(diagnostics['failures']) == 2
    assert diagnostics['failures'][1]['operation'] == 'job_create'
    assert diagnostics['failures'][1]['http_status'] == 403
    assert 'secret-test-key' not in json.dumps(diagnostics)
    assert 'private' not in json.dumps(diagnostics)
    assert message not in str(wrapped)


@pytest.mark.parametrize('cls,status,message,expected', [
    (PermissionDeniedError, 403, 'Access denied', 'AGENT_AUTH'),
    (AuthenticationError, 401, 'Invalid key', 'AGENT_AUTH'),
    (RateLimitError, 429, 'Rate limit exceeded', 'AGENT_RATE_LIMIT'),
    (PermissionDeniedError, 403, 'API key suspended due to insufficient credit.', 'AGENT_CREDIT'),
])
def test_credit_is_distinguished_from_auth_and_rate_limit(cls, status, message, expected):
    code, _ = diagnose_error(provider_error(cls, status, message), 'cv')
    assert code == expected


def test_stage_tracks_cv_jd_and_final_report_separately():
    stage = progress_stage('CV PDF 업로드 및 Agent 분석', 'prepare')
    assert stage == 'cv'
    assert progress_stage('Agent 상태: queued', stage) == 'cv'
    stage = progress_stage('JD PDF 업로드 및 Agent 분석', stage)
    assert stage == 'jd'
    assert progress_stage('기업 fact·CV·JD 결과를 기여 에이전트에 전달합니다.', stage) == 'contribution'
