"""Build Studio-importable agent configs with stricter provenance rules."""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE_DIR = ROOT / "agent_configs"
OUTPUT_DIR = SOURCE_DIR / "validated_v3"

SOURCES = {
    "01_DART_Business_Strategy_Extract_Agent_v3.json": (
        SOURCE_DIR / "revised" / "01_DART_Business_Strategy_Extract_Agent_v2.json"
    ),
    "02_DART_Finance_Management_Extract_Agent_v3.json": (
        SOURCE_DIR / "revised" / "02_DART_Finance_Management_Extract_Agent_v2.json"
    ),
    "03_DART_Workforce_Organization_ESG_Extract_Agent_v3.json": (
        SOURCE_DIR / "revised" / "03_DART_Workforce_Organization_ESG_Extract_Agent_v2.json"
    ),
    "04_DART_Job_Seeker_Company_Brief_Agent_v2.json": (
        SOURCE_DIR / "04_DART_Job_Seeker_Company_Brief_Agent.json"
    ),
}

EVIDENCE_DESCRIPTION = (
    "limitations를 제외한 모든 [E###] 사실과 1:1로 대응한다. 형식: "
    "E001 | original_page=30 | section=사업의 개요 | quote=원문. "
    "original_page는 각 페이지 상단의 'ORIGINAL_PDF_PAGE: 숫자'에 표시된 숫자만 "
    "사용한다. DART 본문 하단 Page 번호와 전처리 PDF 쪽수는 사용하지 않는다. "
    "상단 값을 확인하지 못하면 original_page=0으로 기록하고 limitations에 남긴다. "
    "quote는 고쳐 쓰지 않으며 표는 항목명·기간·값·공통 단위가 함께 이해되게 기록한다. "
    "동일 사실을 여러 필드에 반복하거나 근거 없는 사실을 생성하지 않는다."
)

SOURCE_DOCUMENT_DESCRIPTION = (
    "전처리 PDF 표지의 SOURCE_DOCUMENT 값을 그대로 기록한다. 현재 업로드 파일의 "
    "임시 이름이나 전처리 배치 파일명으로 바꾸지 않는다."
)

COMPENSATION_DESCRIPTION = (
    "1인 평균 급여액, 총급여와 산정기간을 추출한다. 표 상단 또는 표 주석의 공통 단위를 "
    "각 수치에 결합해 '1인평균 급여액 94백만원'처럼 기록한다. 단위를 확인할 수 없으면 "
    "단위 없는 수치를 만들지 말고 limitations에 기록한다. 평균 급여를 신입 초봉으로 "
    "해석하지 않는다. 각 항목은 [E001]부터 전체 출력에서 순차적으로 부여한 고유 ID로 "
    "시작한다."
)

ACCURACY_BLOCK = """

[원문 표기 및 최종 검증]
- 숫자, 소수점, 부호, 날짜, 단위, 영문 대소문자와 공식 명칭은 source_ids가 가리키는 facts에서 그대로 복사한다.
- O와 0, I와 1처럼 모양이 비슷한 문자를 임의로 바꾸지 않는다. 예: tCO2eq를 tC02eq로 바꾸지 않는다.
- 입력 사실에 단위가 없으면 숫자만 단정적으로 제시하지 않고 limitations에 단위 미확인을 기록한다.
- job_seeker_evidence_cards의 original_pages는 각 source_id의 evidence.original_page를 그대로 사용한다.
- 최종 출력 전 모든 항목의 수치·단위·공식 명칭·source_ids·original_pages를 입력 JSON과 한 번 더 대조한다.
- 입력 limitations에 없는 충돌이나 누락을 새로 만들어내지 않는다.
"""


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _schema(config: dict) -> dict:
    return config["workflowConfig"]["informationExtractConfiguration"]["schemas"][0][
        "json_schema"
    ]["schema"]


def _prepare_extract(config: dict, version: str) -> dict:
    result = deepcopy(config)
    workflow = result["workflowConfig"]
    workflow["workflow_name"] = f"{workflow['workflow_name']} {version}"
    schema = _schema(result)
    schema["properties"]["source_document"]["description"] = (
        SOURCE_DOCUMENT_DESCRIPTION
    )
    schema["properties"]["evidence_refs"]["items"]["description"] = (
        EVIDENCE_DESCRIPTION
    )
    return result


def _prepare_brief(config: dict) -> dict:
    result = deepcopy(config)
    workflow = result["workflowConfig"]
    workflow["workflow_name"] = f"{workflow['workflow_name']} v2"
    nodes = workflow["instructConfiguration"]["nodes"]
    nodes[0]["prompt"] = nodes[0]["prompt"].replace(
        "\n\n최종 결과는 지정된 JSON 스키마로만 출력한다.",
        ACCURACY_BLOCK + "\n최종 결과는 지정된 JSON 스키마로만 출력한다.",
    )
    schema = _schema(result)
    schema["properties"]["workforce_snapshot"]["items"]["description"] = (
        "[W01]부터 시작해 직원 규모·구성·근속·평균보상·근무제도를 최대 5개로 "
        "정리한다. 수치에는 입력 facts에서 확인되는 단위를 반드시 함께 기록하며, "
        "단위가 없는 수치는 만들지 않는다."
    )
    schema["properties"]["job_seeker_evidence_cards"]["items"]["description"] = (
        "[J01]부터 시작한다. company_fact, why_it_matters, usable_question, "
        "official_term, evidence_ids, original_pages를 |로 구분한다. 숫자·단위·공식 "
        "표기는 입력 facts에서 그대로 복사하고 original_pages는 연결한 evidence의 "
        "original_page만 사용한다. 회사 고유 근거를 우선해 3~6개 작성한다."
    )
    return result


def build() -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    timestamp = datetime.now(timezone.utc).isoformat()
    for output_name, source_path in SOURCES.items():
        config = _load(source_path)
        if output_name.startswith("04_"):
            revised = _prepare_brief(config)
        else:
            revised = _prepare_extract(config, "v3")
            if output_name.startswith("03_"):
                _schema(revised)["properties"]["average_compensation"]["items"][
                    "description"
                ] = COMPENSATION_DESCRIPTION
        revised["exportedAt"] = timestamp
        output_path = OUTPUT_DIR / output_name
        output_path.write_text(
            json.dumps(revised, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        written.append(output_path)
    return written


if __name__ == "__main__":
    for path in build():
        print(path)
