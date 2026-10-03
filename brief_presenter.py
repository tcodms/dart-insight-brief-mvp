"""Transform the Agent 4 payload into a reader-friendly view model."""

from __future__ import annotations

import re
from typing import Any


TAG_PATTERN = re.compile(r"^\s*\[([A-Z]+\d+)\]\s*")

DETAIL_GROUPS = (
    (
        "사업·시장",
        (
            ("business_and_revenue_model", "사업과 수익모델"),
            ("key_products_services", "주요 제품·서비스"),
            ("market_and_competition", "시장과 경쟁"),
        ),
    ),
    (
        "성과·변화",
        (
            ("recent_changes", "최근 변화"),
            ("performance_change_reasons", "실적 변화 원인"),
        ),
    ),
    (
        "전략·투자",
        (
            ("new_business_and_investment", "신규사업과 투자"),
            ("company_stated_strengths", "회사가 밝힌 강점"),
            ("management_priorities", "경영 우선순위"),
        ),
    ),
    (
        "위험·조직",
        (
            ("company_stated_risks", "회사가 밝힌 위험"),
            ("workforce_snapshot", "인력 현황"),
        ),
    ),
)


def as_list(value: Any) -> list[str]:
    if value in (None, ""):
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def split_tag(value: Any) -> tuple[str, str]:
    text = str(value or "").strip()
    match = TAG_PATTERN.match(text)
    if not match:
        return "", text
    return match.group(1), text[match.end() :].strip()


def clean_text(value: Any) -> str:
    return split_tag(value)[1]


def truncate_text(value: Any, limit: int) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip(" ,.;·") + "…"


def clean_items(value: Any, limit: int | None = None) -> list[dict[str, str]]:
    items = []
    for raw in as_list(value):
        item_id, text = split_tag(raw)
        items.append({"id": item_id, "text": text})
    return items if limit is None else items[:limit]


def parse_evidence_card(value: Any) -> dict[str, Any]:
    item_id, text = split_tag(value)
    fields: dict[str, str] = {}
    for part in text.split(" | "):
        if "=" not in part:
            continue
        key, field_value = part.split("=", 1)
        fields[key.strip()] = field_value.strip()

    pages = [
        page.strip()
        for page in fields.get("original_pages", "").split(",")
        if page.strip()
    ]
    evidence_ids = [
        evidence_id.strip()
        for evidence_id in fields.get("evidence_ids", "").split(",")
        if evidence_id.strip()
    ]
    title = fields.get("official_term") or fields.get("company_fact") or "취업 활용 포인트"
    if len(title) > 42:
        title = title[:39].rstrip() + "…"

    return {
        "id": item_id,
        "title": title,
        "company_fact": fields.get("company_fact", text),
        "why_it_matters": fields.get("why_it_matters", ""),
        "usable_question": fields.get("usable_question", ""),
        "official_term": fields.get("official_term", ""),
        "evidence_ids": evidence_ids,
        "original_pages": pages,
    }


def build_brief_view_model(result: dict) -> dict:
    def highlight_items(key: str) -> list[dict[str, str]]:
        items = clean_items(result.get(key), 3)
        return [
            {**item, "text": truncate_text(item["text"], 115)}
            for item in items
        ]

    highlights = (
        {
            "title": "핵심 사업",
            "items": highlight_items("business_and_revenue_model"),
        },
        {
            "title": "최근 변화",
            "items": highlight_items("recent_changes"),
        },
        {
            "title": "향후 방향",
            "items": highlight_items("management_priorities"),
        },
    )

    detail_groups = []
    for group_title, section_specs in DETAIL_GROUPS:
        sections = []
        for key, title in section_specs:
            sections.append(
                {
                    "key": key,
                    "title": title,
                    "items": clean_items(result.get(key)),
                }
            )
        detail_groups.append({"title": group_title, "sections": sections})

    return {
        "company_name": str(result.get("company_name") or "기업 분석").strip(),
        "report_period": str(result.get("report_period") or "").strip(),
        "filing_date": str(result.get("filing_date") or "").strip(),
        "data_recency": str(result.get("data_recency") or "").strip(),
        "one_sentence": truncate_text(
            clean_text(result.get("company_in_one_sentence")) or "정보 없음",
            280,
        ),
        "highlights": highlights,
        "evidence_cards": [
            parse_evidence_card(item)
            for item in as_list(result.get("job_seeker_evidence_cards"))
        ],
        "detail_groups": detail_groups,
        "official_terms": clean_items(result.get("official_terms")),
        "limitations": as_list(result.get("limitations")),
        "evidence_ids": as_list(result.get("evidence_ids")),
    }
