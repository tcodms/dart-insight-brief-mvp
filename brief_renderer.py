"""Render the Agent 4 JSON result as a reader-friendly Markdown brief."""

from __future__ import annotations

import re

from brief_presenter import build_brief_view_model, emphasize_markdown


def render_company_brief(result: dict) -> str:
    view = build_brief_view_model(result)
    sources = {}
    for raw in view["evidence_ids"]:
        match = re.match(r"^([A-Z]+\d+)\s*\|\s*source_ids=([^|]+)", raw)
        if match:
            sources[match.group(1)] = re.findall(r"B\d+-E\d+", match.group(2))

    def linked(text: str, item_id: str, evidence_ids: list[str] | None = None) -> str:
        rendered = emphasize_markdown(text, view["highlight_terms"])
        ids = evidence_ids if evidence_ids is not None else sources.get(item_id, [])
        if not ids:
            return rendered
        links = " ".join(f"[근거 {index + 2}](#evidence-id-{source_id})" for index, source_id in enumerate(ids[1:]))
        return f"[{rendered}](#evidence-id-{ids[0]})" + (f" {links}" if links else "")

    lines = [f"# {view['company_name']} 취업용 기업분석 브리프", ""]

    if view["data_recency"]:
        lines.extend([f"> {view['data_recency']}", ""])

    lines.extend(
        [
            "## 3분 핵심 요약",
            "",
            linked(view["one_sentence"], "SUM01"),
            "",
        ]
    )
    for highlight in view["highlights"]:
        lines.extend([f"### {highlight['title']}", ""])
        items = highlight["items"]
        lines.extend(
            f"- {linked(item['text'], item['id'])}"
            for item in items
        ) if items else lines.append("- 정보 없음")
        lines.append("")

    lines.extend(["## 취업 준비 핵심 포인트", ""])
    if view["evidence_cards"]:
        for card in view["evidence_cards"]:
            lines.extend([f"### {card['title']}", ""])
            lines.append(
                "- **기업 사실:** "
                + linked(card["company_fact"], card["id"], card["evidence_ids"])
            )
            if card["why_it_matters"]:
                lines.append(f"- **왜 중요한가:** {card['why_it_matters']}")
            if card["usable_question"]:
                lines.append(f"- **생각해볼 질문:** {card['usable_question']}")
            source_parts = []
            if card["original_pages"]:
                source_parts.append("원본 " + ", ".join(card["original_pages"]) + "쪽")
            if card["evidence_ids"]:
                source_parts.append("근거 " + ", ".join(card["evidence_ids"]))
            if source_parts:
                lines.append(f"- **출처:** {' · '.join(source_parts)}")
            lines.append("")
    else:
        lines.extend(["정보 없음", ""])

    lines.extend(["## 상세 분석", ""])
    for group in view["detail_groups"]:
        lines.extend([f"### {group['title']}", ""])
        for section in group["sections"]:
            lines.append(f"#### {section['title']}")
            items = section["items"]
            lines.extend(
                f"- {linked(item['text'], item['id'])}"
                for item in items
            ) if items else lines.append("- 정보 없음")
            lines.append("")

    if view["official_terms"]:
        lines.extend(["## 회사의 공식 표현", ""])
        lines.append(" · ".join(linked(item["text"], item["id"]) for item in view["official_terms"]))
        lines.append("")

    lines.extend(["## 해석 시 유의사항", ""])
    lines.extend(
        (f"- {item}" for item in view["limitations"])
        if view["limitations"]
        else ["- 특이사항 없음"]
    )
    lines.append("")
    return "\n".join(lines)
