# DART Insight

**기업 공시와 나의 경험을 연결하는 취업·이직 준비 서비스**

취업·이직 준비자가 긴 DART 사업보고서에서 기업의 핵심 사업·전략·재무·조직 정보를 파악하고, 자신의 경험을 지원 직무에 어떻게 활용할지 설명하도록 돕습니다. 사업보고서 기반 **기업 브리프**와 기업 사실·CV·JD를 연결한 **기여 보고서**를 제공하며, 보고서에서 원문 근거를 확인할 수 있습니다.

- [배포 서비스](https://dart-insight-brief-mvp-production-d02b.up.railway.app/) — Google 로그인 후 이용
- [GitHub 저장소](https://github.com/tcodms/dart-insight-brief-mvp)
- [서비스 소개](#서비스-소개와-범위) · [아키텍처](#아키텍처) · [실행 방법](#실행-방법) · [환경변수](#환경변수) · [API](#api) · [팀원](#팀원)

## 서비스 소개와 범위

- **기업 분석:** 사업보고서 PDF를 업로드하면 기업 사실을 추출하고 취업 준비용 브리프를 생성합니다.
- **기여 보고서:** 기업 브리프·CV·JD와 지원 직무를 바탕으로 직무 요구사항별 준비 현황, 활용할 경험과 보완할 점, 자기소개서·면접 활용 내용을 제공합니다. 현재 세 문서 입력이 모두 필요합니다.
- **원문 확인:** 연결된 기업 사실과 CV·JD 근거에서 인용문을 확인하고 해당 PDF 페이지를 엽니다. 저장된 근거가 없는 문장은 임의로 연결하지 않습니다.
- **개인 작업 공간:** Google 로그인, 사용자별 PDF·분석 결과 저장, 하이라이트·메모, Markdown 다운로드와 삭제를 지원합니다. 읽기 메모는 다운로드에 포함되지 않습니다.
- **기업 둘러보기:** 자주 찾을 만한 기업의 공용 브리프를 운영자가 등록합니다. **브리프 읽기**는 결과를 바로 열고, **가져오기**는 해당 브리프를 개인 작업 공간의 기업 분석에 추가합니다.
- **사업보고서 찾기:** OpenDART로 기업·공시 목록을 조회하고 공식 원문 페이지로 연결합니다. PDF는 사용자가 내려받아 업로드합니다.

### 사용 흐름

1. Google 계정으로 로그인합니다.
2. **기업 분석 → 사업보고서 등록**에서 기업을 검색해 DART 공시로 이동하거나, 준비한 사업보고서 PDF를 선택해 등록합니다. 원문 PDF는 사용자가 DART에서 내려받습니다.
3. **새 기업 브리프**에서 등록한 보고서를 선택해 분석합니다. 저장한 원본은 **사업보고서 관리**, 완료된 브리프는 **기업 분석**에서 확인합니다.
4. 브리프의 목차로 내용을 탐색하고, 연결된 근거와 **원문 열기**에서 실제 사업보고서의 해당 페이지를 확인합니다.
5. **기업 둘러보기**에서 준비된 브리프를 바로 읽거나 개인 공간으로 가져올 수도 있습니다.
6. **내 자료**에서 CV와 직무기술서(JD) PDF를 등록합니다.
7. **기여 보고서 → 새 기여 보고서**에서 기업 브리프·CV·JD를 선택하고 지원 직무를 입력해 분석합니다.
8. 완료된 기여 보고서에서 경험의 연결 가능성, 준비할 점과 근거를 확인하고 메모하거나 Markdown으로 내려받습니다.

최종 시연에서는 생성 대기를 줄이기 위해 분석 설정과 시작 버튼을 보여준 뒤 사전 생성한 결과를 열 수 있습니다. 이 경우 사전 생성 결과임을 안내합니다. 공용 카탈로그에는 운영자가 등록한 자료만 표시되며, 개인 작업 공간에는 로그인한 사용자의 자료와 결과를 표시합니다.

평가는 기업별 사실·수치·연도·근거 페이지·핵심 내용 누락을 중심으로 진행할 예정입니다. 5개 기업의 품질 검증 완료나 다른 서비스 대비 성능 우위를 주장하지 않습니다. 기업 순위·합격 가능성 점수, 원문 자동 수집, JD 없는 기여 분석은 현재 제공하지 않습니다. ChromaDB와 벡터 검색은 도입하지 않았습니다.

## 아키텍처

```text
브라우저: React + TypeScript + Vite
  -> FastAPI: Google OAuth · 서버 세션 · 문서/분석 API
      -> OpenDART API: 기업·사업보고서 공시 검색 -> 공식 DART 원문 연결
      -> SQLite: 사용자 · 작업 · 결과 · 근거 · 읽기 메모 · 공용 브리프
      -> 파일 저장소: 원본 PDF · 공용 PDF
      -> 단일 작업 큐 / LangGraph: 입력 준비 -> Agent 호출 -> 결과 저장
          -> 실행별 Python 프로세스 -> Upstage Studio / Files API
```

기업 분석은 DART 목차·북마크와 본문 키워드로 보고서를 세 구간으로 나눕니다. 기업별 페이지 번호를 고정하지 않으며, 구간을 식별하지 못하면 중단합니다. 분할 PDF에는 원본 페이지 정보가 포함됩니다.

```text
사업보고서 PDF
  -> Python 전처리
  -> Agent 1 사업·전략 / Agent 2 재무·경영진단 / Agent 3 인력·조직·ESG (병렬)
  -> Python 검증·병합: merged_company_data.json
  -> 비교값 정리: brief_input.json
  -> Agent 4 기업 브리프

기업 fact + CV PDF + JD PDF
  -> Agent 5 CV 추출 / Agent 6 JD 추출 (현재 순차 호출)
  -> 기업 fact·CV·JD 추출 결과를 입력 PDF로 구성
  -> Agent 7 기여 보고서
```

Studio 설정 7개는 [agent_configs/latest](agent_configs/latest)에 있습니다. 사용하는 계정의 Studio로 가져온 후 각 Agent ID·Config ID를 환경변수에 지정합니다. 세부 연결은 [Agent 실행 안내](docs/agent-integration.md), 기여 보고서 출처 연결은 [원문 연결 안내](docs/contribution-source-links.md)를 참고하세요.

## 실행 방법

### 1. 저장소 받기와 준비 사항

```powershell
git clone https://github.com/tcodms/dart-insight-brief-mvp.git
cd dart-insight-brief-mvp
```

Python 3.11+, uv, Node.js 22.12+가 필요합니다. Node 24 LTS도 사용할 수 있습니다. 다음 명령은 저장소 루트 기준 PowerShell 예시입니다.

Google OAuth 웹 클라이언트, OpenDART API 키, Upstage API 키와 Studio Agent 7개의 Agent ID·Config ID를 준비합니다. Studio 설정은 [agent_configs/latest](agent_configs/latest)에서 가져올 수 있습니다. 필요한 값과 발급·설정 안내는 아래 [환경변수](#환경변수)를 참고하세요.

### 2. 설치와 환경 파일

```powershell
uv sync --frozen
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
if (-not (Test-Path .env.service)) { Copy-Item .env.service.example .env.service }
cd frontend
npm ci
cd ..
```

`.env`와 `.env.service`에 아래 설정을 입력합니다. Google OAuth 설정과 콜백 등록 절차는 [서비스 설정](docs/service-setup.md)을 참고하세요.

### 3. 서버 실행

```powershell
# 터미널 1: 저장소 루트
uv run uvicorn backend.app.main:app --host 127.0.0.1 --port 8001 --reload --no-access-log
```

```powershell
# 터미널 2: 저장소 루트
cd frontend
npm run dev
```

- 화면: <http://127.0.0.1:5173>
- API 명세: <http://127.0.0.1:8001/docs>
- 헬스체크: <http://127.0.0.1:8001/api/health>

Vite가 `/api` 요청을 FastAPI로 전달합니다. 백엔드 포트를 변경하면 프론트엔드 실행 환경의 `API_PROXY_TARGET`도 변경합니다. 브라우저 주소는 `127.0.0.1`로 통일하고 Google 승인 리디렉션 URI에 `http://127.0.0.1:5173/api/auth/callback`을 등록합니다. 외부 앱이 OAuth 테스트 모드이면 사용할 계정을 테스트 사용자로 추가해야 합니다.

`--reload`는 개발용입니다. 실행 중 코드 변경·서버 재시작은 진행 중 분석을 중단시킵니다. 현재는 단일 프로세스 작업 큐이므로 `--workers`를 늘리지 않습니다.

## 환경변수

예제 파일: [.env.example](.env.example), [.env.service.example](.env.service.example). 실제 값은 Git에 포함하지 않습니다.

- **`.env.example` → `.env`:** Upstage API 키와 기업 분석·CV·JD·기여 보고서 Agent 설정입니다.
- **`.env.service.example` → `.env.service`:** Google 로그인, 서버 세션, 서비스 주소·저장 경로 및 OpenDART 설정입니다.

`.env.service`는 실제 실행 환경 파일이므로 GitHub에는 예제인 `.env.service.example`만 제공합니다. 위 설치 명령은 기존 환경 파일이 있을 때 덮어쓰지 않습니다. 예제의 빈 인증값은 본인 환경에 맞게 입력해야 합니다.

| 위치 | 변수 | 용도 |
|---|---|---|
| `.env` | `UPSTAGE_API_KEY` | 기업 추출·브리프용 키 |
| `.env` | `BUSINESS_STRATEGY_AGENT_ID`, `BUSINESS_STRATEGY_CONFIG_ID` | 사업·전략 Agent |
| `.env` | `FINANCE_MANAGEMENT_AGENT_ID`, `FINANCE_MANAGEMENT_CONFIG_ID` | 재무·경영진단 Agent |
| `.env` | `WORKFORCE_ESG_AGENT_ID`, `WORKFORCE_ESG_CONFIG_ID` | 인력·조직·ESG Agent |
| `.env` | `COMPANY_BRIEF_AGENT_ID`, `COMPANY_BRIEF_CONFIG_ID` | 기업 브리프 Agent |
| `.env` | `CANDIDATE_UPSTAGE_API_KEY` | CV·JD·기여 보고서용 키 |
| `.env` | `CV_AGENT_ID`, `CV_CONFIG_ID` | CV Agent |
| `.env` | `JD_AGENT_ID`, `JD_CONFIG_ID` | JD Agent |
| `.env` | `CONTRIBUTION_AGENT_ID`, `CONTRIBUTION_CONFIG_ID` | 기여 보고서 Agent |
| `.env.service` | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | Google 웹 OAuth 클라이언트 |
| `.env.service` | `SERVICE_SESSION_SECRET` | 32자 이상의 고정 세션 서명 비밀값 |
| `.env.service` | `SERVICE_ORIGIN` | 로컬 기본값 `http://127.0.0.1:5173`, 배포 시 실제 HTTPS 주소 |
| `.env.service` | `SERVICE_COOKIE_SECURE` | 로컬 `false`, HTTPS 배포 `true` |
| `.env.service` | `SERVICE_DATA_DIR` | 로컬 기본값 `.service-data`, Railway `/data` |
| `.env.service` | `DART_API_KEY` | 사업보고서 찾기에 사용하는 OpenDART 키 |

두 Upstage 키 변수에는 같은 키를 사용할 수 있습니다. 각 키가 해당 Agent와 Config에 접근할 수 있어야 합니다. 키 인증·파일 업로드 성공이 분석 크레딧이나 Agent 실행 권한을 보장하지 않습니다.

세션 비밀값은 다음 명령으로 생성해 `.env.service`의 `SERVICE_SESSION_SECRET`에 입력합니다. 생성한 값은 서버 재시작 후에도 동일하게 유지합니다.

```powershell
uv run python -c "import secrets; print(secrets.token_urlsafe(48))"
```

로컬 개발의 Google 승인 리디렉션 URI는 `http://127.0.0.1:5173/api/auth/callback`입니다. Railway에서는 `SERVICE_ORIGIN`을 실제 HTTPS 주소로, `SERVICE_COOKIE_SECURE`를 `true`로 지정하고 Google 콜백도 같은 도메인의 `/api/auth/callback`으로 등록합니다. 자세한 절차는 [서비스 설정](docs/service-setup.md)을 참고하세요.

## Docker와 Railway 배포

**React 빌드와 Python 서버 실행을 하나의 배포 절차로 정의하기 위해 Dockerfile을 사용합니다.** Node 단계에서 프론트엔드를 빌드하고 Python 단계에 결과를 복사합니다. 실행 시 FastAPI가 화면과 API를 같은 도메인에서 제공합니다. 로컬 개발은 위의 두 서버 방식을 유지합니다.

Docker 엔진이 실행 중인 환경에서는 아래 명령으로 이미지를 빌드할 수 있습니다.

```powershell
docker build -t dart-insight .
```

### Docker로 로컬 실행

Docker Desktop을 실행하고 위 설치 절차의 `.env`, `.env.service`를 준비한 다음 저장소 루트에서 실행합니다. 환경 파일의 키는 컨테이너 실행 시 전달하며 이미지에 포함하지 않습니다.

```powershell
docker compose up --build -d
docker compose ps
docker compose logs --tail 100 web
```

화면: <http://127.0.0.1:8000> · 상태: <http://127.0.0.1:8000/api/health>

Google OAuth의 승인 리디렉션 URI에 `http://127.0.0.1:8000/api/auth/callback`을 추가합니다. Compose는 로컬용 Origin·쿠키·데이터 경로를 지정하며, 개발 서버와는 별도의 `service-data` Docker 볼륨에 SQLite와 PDF를 저장합니다. 기존 로컬 자료는 자동 복사하지 않습니다.

```powershell
# 종료: 저장 자료 유지
docker compose down
# 코드 변경 후 다시 빌드·실행
docker compose up --build -d
```

`docker compose down -v`는 저장 볼륨까지 삭제하므로 자료를 유지하려면 사용하지 않습니다. 이 Compose 설정은 로컬 확인용이며, 공개 배포는 아래 Railway의 HTTPS·볼륨 설정을 사용합니다.

Railway는 GitHub 저장소 루트의 [Dockerfile](Dockerfile)과 [railway.toml](railway.toml)을 사용합니다. 로컬 Docker 엔진 없이 Railway에서 빌드할 수 있습니다.

1. GitHub 저장소와 배포할 브랜치를 연결하고 Root Directory를 저장소 루트로 둡니다.
2. Build/Start Command를 별도로 덮어쓰지 않고 Dockerfile 설정을 사용합니다.
3. 영구 볼륨을 `/data`에 연결하고 `SERVICE_DATA_DIR=/data`를 지정합니다.
4. 위 환경변수를 Railway Variables에 입력합니다. 로컬 환경 파일은 이미지에 포함되지 않습니다.
5. 공개 도메인을 생성하고 `SERVICE_ORIGIN`, 보안 쿠키, Google 콜백 주소를 맞춥니다.
6. `/api/health`, 로그인, PDF 등록·분석·근거 확인, 재배포 후 자료 보존을 검증합니다.

설정값과 절차는 [Railway 배포 안내](docs/railway-deploy.md)를 참고하세요. 현재 데모는 README 상단의 배포 서비스에서 확인할 수 있습니다. 배포 화면의 대표 흐름 확인과 전체 기업의 분석 품질·장기 운영 검증은 구분합니다.

SQLite와 PDF는 같은 영구 볼륨의 `service.sqlite3`, `files/`에 저장합니다. 로컬 데이터는 배포 시 자동 이전되지 않습니다. 운영 데이터 이전·백업은 분석을 멈춘 상태에서 DB와 파일을 함께 일관되게 보관해야 합니다. 사용자 데이터가 있는 운영 DB를 로컬 DB로 덮어쓰지 않습니다. 공용 브리프 등록 명령은 [운영자 등록 안내](docs/service-setup.md#공용-기업-브리프-등록)를 따릅니다.

## API

전체 요청·응답 형식은 실행 중인 서버의 `/docs`에서 확인합니다. 헬스체크와 인증 진입 경로를 제외한 아래 자료 API는 로그인한 본인 범위로 접근합니다. 공용 브리프는 로그인 후 조회합니다.

| 메서드·경로 | 기능 |
|---|---|
| `GET /api/health` | 서버 상태 |
| `GET /api/auth/session` | 세션 상태·CSRF 토큰 |
| `GET /api/auth/login`, `GET /api/auth/callback` | Google 로그인 |
| `POST /api/auth/logout` | 로그아웃 |
| `GET /api/documents`, `POST /api/documents` | 자료 목록·PDF 등록 |
| `GET /api/documents/{id}/file` | 본인 원본 PDF 다운로드 |
| `GET /api/documents/{id}/preview` | 본인 원본 PDF 열기 |
| `GET /api/documents/{id}/impact` | 자료 삭제 시 연결 결과 영향 조회 |
| `DELETE /api/documents/{id}` | 자료와 연결 결과 삭제 |
| `GET /api/analysis/capabilities` | Agent 설정 여부 |
| `POST /api/jobs` | 기업 브리프·기여 분석 시작 |
| `GET /api/jobs`, `GET /api/jobs/{id}` | 작업 상태·실패 안내 |
| `GET /api/analyses` | 본인 분석 목록 |
| `GET /api/analyses/{kind}/{id}` | 결과·근거 조회 (`kind`: `brief` 또는 `personal`) |
| `GET /api/analyses/{kind}/{id}/download` | Markdown 다운로드 |
| `GET /api/analyses/{kind}/{id}/impact` | 분석 결과 삭제 영향 조회 |
| `DELETE /api/analyses/{kind}/{id}` | 분석 결과 삭제 |
| `GET`, `POST /api/analyses/{kind}/{id}/annotations` | 보고서 하이라이트·메모 조회·작성 |
| `PATCH`, `DELETE /api/analyses/{kind}/{id}/annotations/{annotationId}` | 하이라이트·메모 수정·삭제 |
| `GET /api/public-briefs` | 공용 기업 브리프 목록 |
| `GET /api/public-briefs/{id}` | 공용 본문·근거 조회 |
| `GET /api/public-briefs/{id}/preview` | 공용 원본 PDF 열기 |
| `POST /api/public-briefs/{id}/import` | 개인 공간으로 가져오기 |
| `GET /api/dart/companies`, `GET /api/dart/reports` | 기업·공시 목록 검색 |

변경 요청에는 세션 쿠키, `Origin: SERVICE_ORIGIN`, `X-CSRF-Token`이 필요합니다. 자세한 문서·메모 API는 [서비스 설정](docs/service-setup.md)과 `/docs`를 참고하세요.

`POST /api/documents`는 파일과 자료 종류(`report`, `cv`, `jd`)를 multipart form으로 받습니다. `POST /api/jobs`의 분석 입력은 다음과 같습니다. 아래 문서·브리프 ID는 본인 계정에 저장된 실제 ID로 바꿉니다.

```json
{
  "jobType": "brief",
  "reportDocumentId": "등록한 사업보고서 ID"
}
```

```json
{
  "jobType": "personal",
  "briefId": "완료된 기업 브리프 ID",
  "cvDocumentId": "등록한 CV ID",
  "jdDocumentId": "등록한 JD ID",
  "targetRole": "QA"
}
```

분석 시작 요청은 작업을 등록하며, 클라이언트는 `GET /api/jobs/{id}`로 진행 상태를 조회하고 완료 후 결과 API를 호출합니다. PDF 등록만으로 Agent 분석을 실행하지 않습니다.

## 운영 안정성과 현재 한계

- **호출·비용:** 문서 등록만으로 Agent를 호출하지 않습니다. 분석 시작 시 선택한 자료를 Upstage로 전송합니다. 같은 활성 요청의 중복 클릭은 기존 작업을 반환합니다. CV·JD는 기여 분석마다 다시 추출합니다.
- **실패·복구:** 크레딧 부족, 인증·접근 권한, 요청 한도, 연결 실패, 시간 초과를 구분해 안내합니다. 병렬 추출의 개별 실패 원인도 분류에 보존합니다. 과거 기록에 원인이 없으면 새 오류 분류를 소급 적용하지 않습니다.
- **운영 진단:** 백엔드 로그에서 `analysis_failure`를 검색하면 작업 ID·실패 단계·API 동작·HTTP 상태·오류 분류를 확인할 수 있습니다. 이 진단에는 원문·키·원시 API 응답을 기록하지 않습니다. 로컬 실행 로그를 파일에 연결한 경우 `.local-servers/backend.stderr.log`, Railway에서는 서비스 실행 로그를 확인합니다.
- **지연·재시작:** 진행 상태를 폴링합니다. SSE·체크포인트 재개·외부 작업 큐는 없습니다. 재시작 시 실행 중 작업은 실패 처리하고 대기 작업은 이어서 실행합니다. 실패 작업은 자동 재실행하지 않으며, 외부 실행 취소는 지원하지 않습니다.
- **동시 실행:** 단일 인스턴스·단일 서버 프로세스로 운영합니다. 사용자당 진행 작업 1개, 전체 대기·진행 작업 최대 20개입니다. Railway Serverless/App Sleeping은 끕니다.
- **보안·보존:** 서버에서 로그인·문서 소유권·CSRF를 확인합니다. 업로드는 PDF 최대 20MB·2,000쪽이며 손상·암호화·빈 PDF는 거절합니다. CV 삭제 시 연결 기여 결과도 삭제합니다. 실제 개인정보를 포함한 문서는 시연용 공용 데이터에 등록하지 않습니다.

## 검증

```powershell
# 저장소 루트: API·파이프라인 회귀 검사 (외부 Agent 호출 없음)
uv run pytest backend/tests -q
uv run pytest tests -q
```

```powershell
# frontend/: UI 테스트·프로덕션 빌드
npm test
npm run build
```

기본 `uv run pytest -q`의 수집 범위는 `backend/tests`입니다. 실제 Studio 분석 품질·처리 시간·호출 비용과 배포 환경의 Google 로그인·데이터 보존은 별도로 검증해야 합니다. 크레딧 부족 안내와 진단 전달은 제공자 오류를 대체한 테스트로 확인했으며, 공용 5개 기업의 실제 평가는 준비 중입니다.

## 팀원

| 담당 | 역할 |
|---|---|
| 손채은 | 서비스 구조, FastAPI·인증·저장·LangGraph 연동, React UI, 배포 구성·README |
| 이상협 | Studio Agent 프롬프트·노드·출력 품질, CV·JD·기여 분석 고도화 |
| 공동 | 평가 사례 선정·검증, 기여 기준·출력 규격·범위 협의 |

역할 분담 기준이며 개별 기능의 기여 내역은 커밋 이력을 참고합니다.

## 프로젝트 구조와 기존 MVP

```text
backend/              FastAPI·인증·SQLite·작업 큐와 API 테스트
frontend/             React + TypeScript + Vite
pipeline/             전처리·Agent 호출·검증·브리프·기여 보고서
agent_configs/latest/ Studio 설정 7개
scripts/              CV/JD CLI·Agent 설정 생성
legacy/               기존 Streamlit 화면
fonts/                입력 PDF 생성용 글꼴
tests/                파이프라인 테스트
docs/                 서비스·배포·Agent 안내
Dockerfile            프론트 빌드 + Python 실행 이미지
railway.toml          Railway 빌더·헬스체크 설정
```

현재 웹 서비스는 React/FastAPI 기준입니다. 기존 Streamlit은 `requirements.txt`의 별도 의존성을 설치한 뒤 `python -m streamlit run legacy/streamlit_app.py`로 실행할 수 있습니다. CV·JD 추출만 실행하려면 `uv run python -m scripts.analyze_candidate_documents --cv "CV.pdf" --jd "JD.pdf"`를 사용합니다. CLI는 한 문서만 지정할 수도 있으며, 이 명령만으로 기업 브리프나 기여 보고서를 생성하지 않습니다. CLI 결과는 Git 제외 경로인 `output/candidate_runs/<실행 ID>/`에 저장합니다.
