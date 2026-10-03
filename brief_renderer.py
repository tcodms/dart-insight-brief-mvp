"""Render the Agent 4 JSON result as a reader-friendly Markdown brief."""

from __future__ import annotations

from brief_presenter import build_brief_view_model


def render_company_brief(result: dict) -> str:
    view = build_brief_view_model(result)
    lines = [f"# {view['company_name']} 취업용 기업분석 브리프", ""]

    if view["data_recency"]:
        lines.extend([f"> {view['data_recency']}", ""])

    lines.extend(["## 3분 핵심 요약", "", view["one_sentence"], ""])
    for highlight in view["highlights"]:
        lines.extend([f"### {highlight['title']}", ""])
        items = highlight["items"]
        lines.extend(f"- {item['text']}" for item in items) if items else lines.append("- 정보 없음")
        lines.append("")

    lines.extend(["## 취업 준비 핵심 포인트", ""])
    if view["evidence_cards"]:
        for card in view["evidence_cards"]:
            lines.extend([f"### {card['title']}", ""])
            lines.append(f"- **기업 사실:** {card['company_fact']}")
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
            lines.extend(f"- {item['text']}" for item in items) if items else lines.append("- 정보 없음")
            lines.append("")

    if view["official_terms"]:
        lines.extend(["## 회사의 공식 표현", ""])
        lines.append(" · ".join(item["text"] for item in view["official_terms"]))
        lines.append("")

    lines.extend(["## 해석 시 유의사항", ""])
    lines.extend(
        (f"- {item}" for item in view["limitations"])
        if view["limitations"]
        else ["- 특이사항 없음"]
    )
    lines.append("")
    return "\n".join(lines)
