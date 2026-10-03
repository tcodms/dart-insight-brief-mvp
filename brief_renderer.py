"""Render the Agent 4 JSON result as a concise Markdown brief."""

from __future__ import annotations

from typing import Any


SECTIONS = [
    ("business_and_revenue_model", "사업과 수익모델"),
    ("key_products_services", "주요 제품·서비스"),
    ("recent_changes", "최근 변화"),
    ("performance_change_reasons", "실적 변화 원인"),
    ("market_and_competition", "시장과 경쟁"),
    ("new_business_and_investment", "신규사업과 투자"),
    ("company_stated_strengths", "회사가 밝힌 강점"),
    ("company_stated_risks", "회사가 밝힌 위험"),
    ("management_priorities", "경영 우선순위"),
    ("workforce_snapshot", "인력 현황"),
    ("official_terms", "공식 용어"),
    ("job_seeker_evidence_cards", "취업 활용 근거 카드"),
]


def _as_list(value: Any) -> list[str]:
    if value in (None, ""):
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return [str(value)]


def render_company_brief(result: dict) -> str:
    company_name = str(result.get("company_name") or "기업 분석").strip()
    lines = [f"# {company_name} 취업용 기업분석 브리프", ""]

    recency = str(result.get("data_recency") or "").strip()
    if recency:
        lines.extend([f"> {recency}", ""])

    one_sentence = str(result.get("company_in_one_sentence") or "").strip()
    lines.extend(["## 한 문장 요약", "", one_sentence or "정보 없음", ""])

    for key, title in SECTIONS:
        lines.extend([f"## {title}", ""])
        items = _as_list(result.get(key))
        if items:
            lines.extend(f"- {item}" for item in items)
        else:
            lines.append("정보 없음")
        lines.append("")

    limitations = _as_list(result.get("limitations"))
    lines.extend(["## 한계", ""])
    lines.extend((f"- {item}" for item in limitations) if limitations else ["특이사항 없음"])
    lines.append("")
    return "\n".join(lines)
