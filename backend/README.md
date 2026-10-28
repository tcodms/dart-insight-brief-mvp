# FastAPI 개발 API

Google OIDC 로그인·서버 세션, 사용자별 PDF 관리, 기존 Upstage Agent의 기업 브리프·CV/JD 기여 분석을 제공한다. LangGraph의 입력 준비→Agent 호출→결과 저장 흐름을 SQLite 작업 대기열과 연결한다. Agent 설정은 루트 `.env`, Google 설정은 `.env.service`를 사용한다.

저장소 루트에서 Python 3.11 이상과 uv를 사용한다.

```powershell
uv sync
uv run uvicorn backend.app.main:app --host 127.0.0.1 --port 8001 --reload --no-access-log
```

- `GET /api/health`: 서버 상태와 `ui-preview` 실행 모드
- `GET /api/demo/workspace`: 고정된 가상 기업·CV·JD·근거 데이터
- `GET /api/auth/session`: 로그인 상태·사용자·CSRF 토큰
- `GET /api/documents`, `POST /api/documents`: 본인 문서 조회·등록
- API 명세: <http://127.0.0.1:8001/docs>

```powershell
uv run pytest -q
```

이 명령은 `backend/tests`의 API 검증을 실행한다. 기존 Agent 테스트(`tests/`)는 기존 의존성과 별도 실행 환경을 사용한다. 새 API 환경은 `requirements.txt`를 대체하지 않는다.

Google 설정과 자료 관리 API는 [서비스 설정 안내](../docs/service-setup.md), Agent 실행 API와 제한은 [Agent 연결 안내](../docs/agent-integration.md)를 참고한다. 로컬 서버 한 프로세스에서 실행하며 `--workers`를 늘리지 않는다.
