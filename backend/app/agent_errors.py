"""Classify provider failures without logging keys, documents, or raw responses."""

STAGES = {
    'prepare': '입력 준비', 'preprocess': '사업보고서 전처리',
    'extract': '기업 사실 추출', 'merge': '기업 사실 병합',
    'brief': '기업 브리프 생성', 'cv': 'CV 추출', 'jd': 'JD 추출',
    'contribution': '기여 보고서 생성',
}
EXTRACT_STAGES = {
    '2/6 Agent 1 사업·전략 추출': '사업·전략 추출',
    '3/6 Agent 2 재무·경영진단 추출': '재무·경영진단 추출',
    '4/6 Agent 3 인력·조직·ESG 추출': '인력·조직·ESG 추출',
}


def progress_stage(message, current):
    text = str(message)
    for prefix, stage in (
        ('1/6', 'preprocess'), ('2~4/6', 'extract'), ('5/6', 'merge'),
        ('6/6', 'brief'), ('CV PDF', 'cv'), ('JD PDF', 'jd'),
        ('기업 fact·CV·JD', 'contribution'),
    ):
        if text.startswith(prefix):
            return stage
    return current


def _failure(error, stage):
    name = type(error).__name__
    status = getattr(error, 'status_code', None)
    body = getattr(error, 'body', None)
    body = body if isinstance(body, dict) else {}
    detail = body.get('error', body)
    detail = detail if isinstance(detail, dict) else {}
    # A generic 403 is not proof of insufficient credit. Require the provider's
    # explicit billing reason; do not expose the message itself in diagnostics.
    message = str(detail.get('message', '')).lower()
    provider_code = detail.get('code')
    credit = (provider_code in ('insufficient_credit', 'insufficient_quota') or
              'insufficient credit' in message or 'insufficient balance' in message)
    code = 'AGENT_CREDIT' if credit else {
        'AuthenticationError': 'AGENT_AUTH', 'PermissionDeniedError': 'AGENT_AUTH',
        'RateLimitError': 'AGENT_RATE_LIMIT', 'BadRequestError': 'AGENT_REQUEST',
        'NotFoundError': 'AGENT_REQUEST', 'TimeoutError': 'TIMEOUT',
        'APITimeoutError': 'TIMEOUT', 'APIConnectionError': 'AGENT_CONNECTION',
        'ModuleNotFoundError': 'DEPENDENCIES_MISSING', 'ValueError': 'INVALID_RESULT',
        'MergeValidationError': 'INVALID_RESULT',
    }.get(name, 'AGENT_FAILED')
    operation = 'local'
    request = getattr(error, 'request', None)
    path = getattr(getattr(request, 'url', None), 'path', '')
    if path.endswith('/files'):
        operation = 'file_upload' if request.method == 'POST' else 'file_api'
    elif '/responses' in path:
        operation = 'job_create' if request.method == 'POST' else 'job_poll'
    return {
        'code': code, 'stage': stage, 'operation': operation,
        'exception_type': name, 'http_status': status if isinstance(status, int) else None,
        'provider_code': provider_code if provider_code in (
            'api_key_is_not_allowed', 'insufficient_credit', 'insufficient_quota',
            'invalid_api_key', 'rate_limit_exceeded',
        ) else None,
    }


def diagnose_error(error, stage='prepare'):
    failures = getattr(error, 'failures', None)
    details = ([_failure(cause, EXTRACT_STAGES.get(label, STAGES['extract']))
                for label, cause in failures] if failures else
               [_failure(error, STAGES.get(stage, STAGES['prepare']))])
    # Preserve every parallel failure, and prioritize actionable credit errors.
    primary = next((item for item in details if item['code'] == 'AGENT_CREDIT'), details[0])
    return primary['code'], {'stage': primary['stage'], 'failures': details}
