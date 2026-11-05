# 취업용 기업 브리프 Agent

Studio 가져오기 파일은 [최신 Agent 4](../agent_configs/latest/04_DART_Job_Seeker_Company_Brief_Agent_v4.json)이다.

## 입력과 출력

Agent 1~3의 결과를 검증·병합한 `merged_company_data.json`에 Python 전처리가
원문 근거의 전년·당기 비교값을 정리해 `brief_input.json`을 만든다.
웹 파이프라인은 이를 Agent 4에 전달한다. Studio에서 직접 테스트할 때도 같은 입력을 사용한다.

출력은 문자열과 문자열 배열로 구성된 JSON이다.
사업·고객·실적 변화·시장·전략·투자·위험·인력을 고정 목차로 정리한다.
입력 FACT와 원문 인용만 사용하며 외부 지식, 새 계산, 근거 없는 인과관계를 추가하지 않는다.

## 근거와 표시

- `evidence_ids`는 각 본문 항목을 실제 입력 FACT ID와 연결한다.
- `executive_summary_item_ids`는 요약에 표시할 본문 항목을 선택한다.
- `essential_fact_coverage`는 개발·평가용 선정 기록이며 사용자 본문에는 표시하지 않는다.
- 렌더러는 내부 ID·연결 정보를 본문에서 제거하고 주제 하단의 작은 출처 링크로 표시한다.

## 재생성과 검증

저장소 루트에서 `python build_company_brief_agent_v4.py`로 현재 04 파일을 갱신한다.
생성기는 현재 파일에서 파이프라인·파싱·모델 설정을 읽고 프롬프트와 스키마를 재생성한다.
생성된 JSON을 Studio에 가져오고 Instruct → Extract 연결과 출력 스키마를 확인한다.
실행에 사용할 Agent ID·Config ID는 로컬 `.env`에서 관리한다.

같은 FACT 입력으로 필수 내용 포함, 수치·기간·연결/별도 범위, 근거 연결과 중복을 비교한다.
원문에는 있지만 입력 FACT에 없는 내용은 추출 단계 보완으로 기록한다.
골든셋 점수와 반복 실행 결과를 함께 확인하고 특정 기업의 수치를 규칙에 고정하지 않는다.
