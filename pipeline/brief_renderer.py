"""Render the Agent 4 JSON result as a reader-friendly Markdown brief."""

from __future__ import annotations

import re

from pipeline.brief_presenter import build_brief_view_model, emphasize_markdown, strip_inline_metadata


def clean_saved_brief_markdown(markdown: str) -> str:
    markdown = re.sub(r"^(#{1,6}[ \t]+)3분[ \t]+핵심 요약(?=[ \t]*\r?$)", r"\1핵심 요약", markdown, flags=re.MULTILINE)
    markdown = re.sub(
        r"(?m)^(- \*\*출처:\*\* [^\r\n]*?) · 근거 B\d+-E\d+(?:,\s*B\d+-E\d+)*(?=\r?$)",
        r"\1",
        markdown,
    )
    return strip_inline_metadata(markdown)


def render_company_brief(result: dict) -> str:
    view = build_brief_view_model(result)
    sources = {}
    for raw in view["evidence_ids"]:
        match = re.match(r"^([A-Z]+\d+)\s*\|\s*source_ids=([^|]+)", raw)
        if match:
            sources[match.group(1)] = re.findall(r"B\d+-E\d+", match.group(2))

    section_sources: dict[str, None] = {}

    def linked(text: str, item_id: str, evidence_ids: list[str] | None = None) -> str:
        rendered = emphasize_markdown(text, view["highlight_terms"])
        ids = evidence_ids if evidence_ids is not None else sources.get(item_id, [])
        section_sources.update(dict.fromkeys(ids))
        return rendered

    def append_sources(pages: list[str] | None = None) -> None:
        links = [
            f"[근거 {index}](#evidence-id-{source_id})"
            for index, source_id in enumerate(section_sources, start=1)
        ]
        page_links = [
            f"[{page}쪽](#evidence-page-{page})"
            for page in dict.fromkeys(pages or [])
            if page.isdigit()
        ]
        if page_links or links:
            lines.extend(["출처 · " + " · ".join(page_links + links), ""])
        section_sources.clear()

    lines = [f"# {view['company_name']} 취업용 기업분석 브리프", ""]

    if view["data_recency"]:
        lines.extend([f"> {view['data_recency']}", ""])

    lines.extend(
        [
            "## 핵심 요약",
            "",
            linked(view["one_sentence"], "SUM01"),
            "",
        ]
    )
    append_sources()
    for highlight in view["highlights"]:
        lines.extend([f"### {highlight['title']}", ""])
        items = highlight["items"]
        lines.extend(
            f"- {linked(item['text'], item['id'])}"
            for item in items
        ) if items else lines.append("- 정보 없음")
        lines.append("")
        append_sources()

    lines.extend(["## 취업 준비 핵심 포인트", ""])
    if view["evidence_cards"]:
        for card in view["evidence_cards"]:
            title = linked(card["title"], card["id"], card["evidence_ids"])
            lines.extend([f"### {title}", ""])
            if card["why_it_matters"]:
                lines.append(f"- **왜 중요한가:** {card['why_it_matters']}")
            if card["usable_question"]:
                lines.append(f"- **생각해볼 질문:** {card['usable_question']}")
            lines.append("")
            append_sources(card["original_pages"])
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
            append_sources()

    if view["official_terms"]:
        lines.extend(["## 회사의 공식 표현", ""])
        lines.append(" · ".join(linked(item["text"], item["id"]) for item in view["official_terms"]))
        lines.append("")
        append_sources()

    lines.extend(["## 해석 시 유의사항", ""])
    lines.extend(
        (f"- {item}" for item in view["limitations"])
        if view["limitations"]
        else ["- 특이사항 없음"]
    )
    lines.append("")
    return "\n".join(lines)
