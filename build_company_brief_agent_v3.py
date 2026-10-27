"""Build the Studio-importable Company Brief Agent v3 configuration."""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = (
    ROOT
    / "agent_configs"
    / "validated_v3"
    / "04_DART_Job_Seeker_Company_Brief_Agent_v2.json"
)
OUTPUT = (
    ROOT
    / "agent_configs"
    / "validated_v3"
    / "04_DART_Job_Seeker_Company_Brief_Agent_v3.json"
)

SELECTION_BLOCK = """

[정보 선택 우선순위]
입력 facts가 많더라도 일반적인 설명보다 취업 준비에 직접 활용할 수 있는 회사 고유 수치, 변화, 프로젝트와 공식 명칭을 우선한다.

1. recent_changes
- three_year_financial_trends가 있으면 매출액, 영업이익, 당기순이익의 현재값·비교값·방향을 먼저 포함한다.
- 세 지표를 확인할 수 있으면 recent_changes의 앞 3개로 배치한다.
- 나머지 항목에는 최근 제품 출시, 생산시설, 신규사업, 투자 또는 조직 변화를 선택한다.
- 오래된 상호 변경과 단순 사업목적 추가는 더 최근의 사업·재무 변화가 있으면 우선하지 않는다.

2. market_and_competition
- 시장별 판매량, 점유율과 변화가 있으면 국내 한 곳만 선택하지 말고 주요 지역을 비교할 수 있게 구성한다.
- 회사 고유 점유율·판매량·경쟁우위를 일반적인 산업 경쟁요소보다 우선한다.
- 경쟁사 명칭이 입력에 없으면 추정하지 않는다.

3. new_business_and_investment
- research_development facts가 있으면 일반적인 '연구개발을 수행한다'보다 연구개발비, 매출 대비 비율, 명명된 연구과제, 특허·지식재산을 우선한다.
- technology_investment, 생산시설, 스마트팩토리, 디지털 플랫폼, 신규사업, 해외투자를 서로 다른 관점에서 선택한다.
- 최대 5개 안에서 가능하면 정량 R&D 1개, 구체적 연구·기술 1개, 생산·설비·디지털 투자 1개, 신규사업 1개를 포함한다.

4. company_stated_strengths
- 회사의 실적, 점유율, 제품, 기술, 생산성과 같이 회사 facts가 직접 뒷받침하는 강점만 선택한다.
- '제품력·마케팅력·비용 경쟁력이 중요하다'처럼 업계 전체에 적용되는 일반론은 회사 고유 강점으로 분류하지 않는다.

5. company_stated_risks
- 회사에 직접 적용되는 관세, 환율, 공급망, 품질·판매보증, 안전, 규제, 유동성 위험을 우선한다.
- audit_opinion과 contingent_liabilities에 중요한 회사 고유 신호가 있으면 사실 범위에서 반영한다.
- 문장의 주어와 지표명을 생략하지 않는다. 예: '매출원가율은 전년 대비 3.4%p 상승한 80.3%'처럼 작성한다.

6. management_priorities
- 같은 전략의 유사 문장을 반복하지 않는다.
- 제품·시장, 생산·공급망, 기술·R&D, 신규사업·투자 등 서로 다른 경영축을 균형 있게 선택한다.
- 경영진이 제시한 목표 수치, 일정, 모델명과 지역명을 보존한다.

7. workforce_snapshot과 ESG
- 직원 수, 고용형태, 근속, 보상과 근무제도를 우선한다.
- 안전·환경·거버넌스의 회사 고유 신호가 위험 또는 투자 판단에 중요하면 관련 필드에 반영한다.

8. job_seeker_evidence_cards
- 카드가 한 분야에 편중되지 않도록 사업·신규 프로젝트, 시장·실적, R&D·기술, 생산·운영 또는 위험 중 서로 다른 관점에서 4~6개를 선택한다.
- 정량 사실이나 공식 프로젝트명이 있는 카드를 일반적인 설명보다 우선한다.

[누락 방지 검증]
최종 출력 전에 다음을 검사한다.
- three_year_financial_trends가 있는데 recent_changes에 재무 추이가 하나도 없는지
- 정량 research_development가 있는데 일반적인 연구개발 문장만 선택했는지
- 여러 지역의 market_position 또는 industry_specific_metrics가 있는데 국내 정보만 선택했는지
- 회사 고유 근거가 아닌 산업 일반론을 company_stated_strengths에 넣었는지
- risk 문장에서 지표명이나 주어가 빠져 의미가 불완전한지
- management_priorities가 하나의 전략 주제로만 채워졌는지
- job_seeker_evidence_cards가 프로젝트 한 종류에 편중되었는지
조건에 해당하면 입력 facts 안에서 항목을 다시 선택한 뒤 출력한다.
"""


def _schema(config: dict) -> dict:
    return config["workflowConfig"]["informationExtractConfiguration"]["schemas"][0][
        "json_schema"
    ]["schema"]


def build() -> Path:
    config = deepcopy(json.loads(SOURCE.read_text(encoding="utf-8")))
    config["exportedAt"] = datetime.now(timezone.utc).isoformat()
    workflow = config["workflowConfig"]
    workflow["workflow_name"] = "DART Job Seeker Company Brief Agent v3"

    node = workflow["instructConfiguration"]["nodes"][0]
    marker = "\n[원문 표기 및 최종 검증]"
    if marker not in node["prompt"]:
        raise ValueError("Agent 4 prompt insertion marker was not found.")
    node["prompt"] = node["prompt"].replace(marker, SELECTION_BLOCK + marker, 1)

    properties = _schema(config)["properties"]
    properties["recent_changes"]["items"]["description"] = (
        "[C01]부터 시작해 최대 5개로 정리한다. three_year_financial_trends가 있으면 "
        "매출액·영업이익·당기순이익의 현재값, 비교값과 방향을 먼저 선택하고, 이후 최근 "
        "제품·사업·생산시설·투자 변화를 기록한다. 오래된 연혁은 최근 변화보다 우선하지 않는다."
    )
    properties["market_and_competition"]["items"]["description"] = (
        "[M01]부터 시작해 최대 5개로 정리한다. 회사 고유의 지역별 판매량·시장점유율·경쟁우위를 "
        "산업 일반론보다 우선하고, 여러 주요 시장 정보가 있으면 비교 가능하게 선택한다."
    )
    properties["new_business_and_investment"]["items"]["description"] = (
        "[N01]부터 시작해 최대 5개로 정리한다. 정량 연구개발비·비율, 명명된 연구과제·특허, "
        "기술·생산시설·디지털 투자, 신규사업과 해외투자를 우선하며 일반적인 R&D 문장은 후순위로 둔다."
    )
    properties["company_stated_strengths"]["items"]["description"] = (
        "[S01]부터 시작해 최대 4개로 정리한다. 회사의 실적·점유율·제품·기술·생산성처럼 회사 "
        "facts가 직접 입증하는 강점만 선택하고 업계 전체에 적용되는 경쟁요소는 제외한다."
    )
    properties["company_stated_risks"]["items"]["description"] = (
        "[R01]부터 시작해 최대 5개로 정리한다. 회사에 직접 적용되는 관세·환율·공급망·품질·"
        "판매보증·안전·규제·유동성 신호를 우선하며 주어와 지표명을 생략하지 않는다."
    )
    properties["management_priorities"]["items"]["description"] = (
        "[P01]부터 시작해 최대 5개로 정리한다. 제품·시장, 생산·공급망, 기술·R&D, 신규사업·투자 "
        "등 서로 다른 전략축을 균형 있게 선택하고 목표 수치·일정·공식 명칭을 보존한다."
    )
    properties["job_seeker_evidence_cards"]["items"]["description"] = (
        "[J01]부터 시작한다. company_fact, why_it_matters, usable_question, official_term, evidence_ids, "
        "original_pages를 |로 구분한다. 사업·프로젝트, 시장·실적, R&D·기술, 생산·운영 또는 위험의 "
        "서로 다른 관점에서 정량 사실과 회사 고유 명칭을 우선해 4~6개 작성한다."
    )
    properties["limitations"]["items"]["description"] = (
        "전체 facts를 확인한 뒤에도 해결되지 않은 누락·충돌·OCR 오류·기준 불일치만 기록한다. "
        "다른 배치의 facts로 해결된 한계와 단순 처리 메모는 남기지 않는다. 평균 급여와 근속을 "
        "신입 초봉이나 조직문화로 해석하지 않는다."
    )

    OUTPUT.write_text(
        json.dumps(config, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return OUTPUT


if __name__ == "__main__":
    print(build())
