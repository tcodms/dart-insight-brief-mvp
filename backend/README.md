# FastAPI 개발 API

현재는 React UI 확인을 위한 읽기 전용 API다. 실제 사용자 문서나 기존 Agent를 호출하지 않는다.

저장소 루트에서 Python 3.11 이상과 uv를 사용한다.

```powershell
uv sync
uv run uvicorn backend.app.main:app --host 127.0.0.1 --port 8001 --reload
```

- `GET /api/health`: 서버 상태와 `ui-preview` 실행 모드
- `GET /api/demo/workspace`: 고정된 가상 기업·CV·JD·근거 데이터
- `GET /api/auth/session`: 로그인 미연결 상태
- API 명세: <http://127.0.0.1:8001/docs>

```powershell
uv run pytest -q
```

이 명령은 `backend/tests`의 API 검증을 실행한다. 기존 Agent 테스트(`tests/`)는 기존 의존성과 별도 실행 환경을 사용한다. 새 API 환경은 `requirements.txt`를 대체하지 않는다.

실제 업로드·분석·저장 API는 아직 없다. 다음 단계에서 Google 인증과 사용자 소유권 검증을 연결하고, Agent 어댑터의 입력·출력 계약을 정한 후 추가한다.
