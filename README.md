# DART Insight 취업용 기업분석 브리프

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
