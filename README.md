# DART Insight 취업용 기업분석 브리프

## 2차 서비스 개발 미리보기

`production-transition`에서 **React + TypeScript + Vite / FastAPI** 구조로 전환 중입니다. `frontend/`가 새 UI이며 기존 Streamlit과 Agent 코드는 별도로 유지합니다.

현재 구현: 무채색 Light/Dark UI와 샘플 분석 탐색, Google OIDC 연결 코드·서버 세션, SQLite와 파일 저장소 기반 사용자별 PDF 등록·조회·다운로드·삭제. Google 인증 정보를 설정한 뒤 실제 로그인과 자료 저장을 사용할 수 있습니다. 설정 순서는 [서비스 설정 안내](docs/service-setup.md)를 참고하세요.

**샘플 화면의 기업·문서·분석은 모두 가상 예시입니다.** 로그인한 사용자의 실제 PDF는 별도의 개인 작업 공간에서 관리합니다. 샘플 삭제는 새로고침하면 복원되고, 실제 문서 삭제는 원본과 연결 결과를 지웁니다. 샘플 결과 다운로드는 예시 JSON, 개인 자료 다운로드는 등록한 PDF입니다. 실제 Agent 실행·분석 결과 생성·PDF 원문 뷰어·LangGraph·ChromaDB·Docker는 아직 연결하지 않았습니다.

Python 3.11+, uv, Node.js 22.12+ 또는 24 LTS가 필요합니다. 저장소 루트에서 두 터미널로 실행합니다.

```powershell
# 터미널 1: 백엔드
uv sync
uv run uvicorn backend.app.main:app --host 127.0.0.1 --port 8001 --reload --no-access-log
```

```powershell
# 터미널 2: 프런트엔드
cd frontend
npm ci
npm run dev
```

화면: <http://127.0.0.1:5173> · API 명세: <http://127.0.0.1:8001/docs>

Vite가 `/api` 요청을 FastAPI로 전달합니다. 개발 서버를 별도 포트로 실행하면 `API_PROXY_TARGET`을 지정합니다. Vite 배포 산출물만으로 API가 실행되지는 않습니다.

```powershell
# 루트: 새 API 검사
uv run pytest -q
# frontend/: UI 규칙 검사와 프로덕션 빌드
npm test
npm run build
```

구현 범위와 다음 작업은 [UI 개발 메모](docs/ui/implementation.md)를 참고합니다.

## 기존 1차 MVP와 Agent 실행

장문 DART 사업보고서에서 취업 준비에 필요한 회사 고유 사실과 원문 근거를 추출하여 짧은 기업분석 브리프를 만드는 1차 MVP입니다.

## 처리 흐름

```text
사업보고서 PDF 1개
  -> Python 전처리: 목적별 PDF 3개
  -> Agent 1: 사업·전략
  -> Agent 2: 재무·경영진단
  -> Agent 3: 인력·조직·ESG
  -> Python 검증·병합: merged_company_data.json
  -> Agent 4: 취업용 기업분석 브리프
  -> company_brief_result.json + company_brief.md
```

Agent 5 개인화와 공식 직무기술서 분석은 1차 MVP 범위에서 제외합니다.

## CV/JD 에이전트 실행

CV·JD 분석은 기존 기업 브리프 파이프라인과 분리되어 있습니다. Studio에서 각 에이전트를 만든 뒤 `.env`에 `CANDIDATE_UPSTAGE_API_KEY`, `CV_AGENT_ID`, `CV_CONFIG_ID`, `JD_AGENT_ID`, `JD_CONFIG_ID`를 설정합니다. CV·JD PDF 업로드와 두 에이전트 호출은 `CANDIDATE_UPSTAGE_API_KEY`를 사용하며, 기존 1차 MVP는 `UPSTAGE_API_KEY`를 계속 사용합니다. `.env.example`에 빈 입력 형식이 있습니다.

Streamlit 화면에서는 먼저 사업보고서로 기업 브리프를 생성합니다. `개인 경험 연결` 영역에는 해당 보고서의 회사명·연도와 함께 사용할 기업 fact가 자동 표시됩니다. CV와 JD PDF를 올리고 버튼을 누르면, 두 추출 에이전트의 결과와 해당 실행의 `merged_company_data.json`을 한 PDF로 묶어 기여 분석 에이전트에 전달합니다. 화면에는 최종 자기소개서·면접용 보고서만 표시하고 Markdown 다운로드를 제공합니다. `.env`에는 `CONTRIBUTION_AGENT_ID`, `CONTRIBUTION_CONFIG_ID`도 설정해야 합니다. CLI에서 CV·JD 추출만 독립 실행할 수도 있습니다.

```powershell
python analyze_candidate_documents.py --cv "CV.pdf" --jd "JD.pdf"
```

`--cv` 또는 `--jd` 하나만 지정해도 실행됩니다. PDF는 지정한 경로에서 읽어 Upstage Files API로 업로드하고, 각 Studio Agent의 JSON 결과를 `output/candidate_runs/<실행 ID>/cv_result.json`과 `jd_result.json`에 저장합니다. 이 단계에서는 기업 브리프와 합치거나 기여 분석을 수행하지 않습니다. 에이전트 설정이 없으면 해당 환경변수를 표시하고 중단합니다.

### JD Agent 검증 (2026-10-26)

예시 직무기술서 PDF로 `--jd` 단독 실행을 확인했습니다. Studio에서 목록 설정을 적용한 Config ID를 `.env`에 지정한 뒤 Agent 작업이 완료됐고, 결과 JSON의 22개 항목이 모두 반환됐습니다. 단일값 6개는 문자열, 목록 16개는 배열이며, 명시되지 않은 필수 경력·자격증은 빈 배열로 반환됐습니다. 실행 결과와 `.env`는 Git에서 제외됩니다.

```powershell
python analyze_candidate_documents.py --jd "직무기술서.pdf"
```

CV와 JD를 자동 비교할 때는 `required_education`의 선택 조건을 주의해야 합니다. 예시 공고의 "학사 학위 이상 보유 또는 2027년 2월 졸업예정"은 두 배열 항목으로 나뉘어 추출되므로, 두 조건을 모두 충족해야 한다고 해석하면 안 됩니다.

## 프로젝트 구조

```text
dart-insight-brief-mvp/
├── streamlit_app.py
├── service.py
├── preprocessor.py
├── merge_builder.py
├── brief_renderer.py
├── agent_client.py
├── upload.py
├── *_agent.py
├── agent_configs/       # Studio 가져오기용 Agent JSON 4개
├── tests/
├── output/runs/         # 실행별 중간 산출물
└── result/              # 가장 최근 최종 브리프
```

## 1. Studio Agent 가져오기

`agent_configs` 폴더의 JSON을 번호 순서대로 Studio에서 가져옵니다.

1. DART Business & Strategy Extract Agent
2. DART Finance & Management Extract Agent
3. DART Workforce, Organization & ESG Extract Agent
4. DART Job Seeker Company Brief Agent

가져온 뒤 각 Agent의 최신 Agent ID와 Config ID를 확인합니다.

## 2. 환경변수

`.env`에 값을 입력합니다.

```text
UPSTAGE_API_KEY=
BUSINESS_STRATEGY_AGENT_ID=
BUSINESS_STRATEGY_CONFIG_ID=
FINANCE_MANAGEMENT_AGENT_ID=
FINANCE_MANAGEMENT_CONFIG_ID=
WORKFORCE_ESG_AGENT_ID=
WORKFORCE_ESG_CONFIG_ID=
COMPANY_BRIEF_AGENT_ID=
COMPANY_BRIEF_CONFIG_ID=
```

## 3. 설치와 실행

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## 전처리 페이지 범위

기본 범위는 현재 IBK기업은행 845쪽 샘플 보고서에 맞춰져 있습니다.

- 페이지 범위는 PDF의 DART 목차/북마크와 페이지 본문 키워드로 자동 판정합니다.
- 기업별 페이지 번호를 코드나 화면에 저장하지 않습니다.
- 목차를 인식하지 못하면 임의 범위로 실행하지 않고 오류로 중단합니다.

Streamlit의 `전처리 페이지 범위`에서 수정할 수 있습니다. 각 분할 PDF에는 표지와 `ORIGINAL_PDF_PAGE`, `SOURCE_BATCH`가 추가됩니다.

## 테스트

```powershell
pytest -q
```

외부 Agent API를 호출하지 않는 전처리·병합·렌더링 단위 테스트입니다.
