# FastAPI 개발 API

Google OIDC 로그인·서버 세션과 SQLite 기반 사용자별 PDF 등록·조회·다운로드·삭제 API를 제공한다. 기존 Agent는 아직 호출하지 않는다. Google 인증 정보 등록 전에는 로그인과 실제 사용자 자료 등록을 시작할 수 없다.

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

Google 설정, API 명세와 저장 구조는 [서비스 설정 안내](../docs/service-setup.md)를 참고한다. 분석 결과 관련 테이블은 준비했으며 실제 Agent 실행과 결과 생성은 다음 단계다.
