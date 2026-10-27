"""Make a readable Studio input PDF from company facts and CV/JD results."""

from __future__ import annotations

import html
import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate

from config import FONT_PATH


def build_contribution_input_pdf(
    merged: dict, cv: dict, jd: dict, output_path: str | Path
) -> Path:
    """Keep source labels, fact IDs, and quotes visible to the Instruct agent."""
    facts = merged.get("facts")
    if not isinstance(facts, list) or not facts:
        raise ValueError("기업 fact 병합 결과에 facts가 없습니다.")
    if not isinstance(cv, dict) or not isinstance(jd, dict):
        raise ValueError("CV와 JD 추출 결과는 JSON 객체여야 합니다.")

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    if "ContributionNanum" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("ContributionNanum", str(FONT_PATH)))

    styles = {
        "title": ParagraphStyle(
            "contribution-title", fontName="ContributionNanum", fontSize=16,
            leading=24, spaceAfter=14, wordWrap="CJK",
        ),
        "section": ParagraphStyle(
            "contribution-section", fontName="ContributionNanum", fontSize=12,
            leading=19, spaceBefore=14, spaceAfter=7,
            textColor=colors.HexColor("#2156A5"), wordWrap="CJK",
        ),
        "body": ParagraphStyle(
            "contribution-body", fontName="ContributionNanum", fontSize=8.5,
            leading=13.5, spaceAfter=5, wordWrap="CJK",
        ),
    }

    def paragraph(value: object, style: str = "body") -> Paragraph:
        text = html.escape(str(value)).replace("\n", "<br/>")
        return Paragraph(text, styles[style])

    story = [
        paragraph("기여 분석 입력 자료", "title"),
        paragraph("[기업 fact 병합결과] / [CV Agent 추출 결과] / [JD Agent 추출 결과]"),
        paragraph("기업 사실, 지원자 경험, 직무 요건을 구분해서 해석하세요."),
        paragraph("[기업 fact 병합결과]", "section"),
    ]
    for key in ("company_name", "report_type", "report_period", "filing_date"):
        story.append(paragraph(f"{key}: {merged.get(key, '')}"))
    story.append(paragraph(f"source_documents: {', '.join(map(str, merged.get('source_documents', [])))}"))
    for item in merged.get("limitations", []):
        story.append(paragraph(f"해석 유의사항: {item}"))

    for fact in facts:
        evidence = fact.get("evidence") or {}
        story.extend(
            [
                paragraph(f"[{fact.get('id', '')}] {fact.get('category', '')}", "section"),
                paragraph(f"기업 fact: {fact.get('statement', '')}"),
                paragraph(
                    f"근거: {fact.get('source_batch', '')} / 원문 {evidence.get('original_page', '미기재')}쪽"
                    f" / {evidence.get('section', '미기재')}"
                ),
                paragraph(f"원문 인용: {evidence.get('quote', '미기재')}"),
            ]
        )

    for heading, values in (
        ("[CV Agent 추출 결과]", cv),
        ("[JD Agent 추출 결과]", jd),
    ):
        story.extend([PageBreak(), paragraph(heading, "section")])
        for key, value in values.items():
            story.append(paragraph(key, "section"))
            items = value if isinstance(value, list) else [value]
            if not items:
                story.append(paragraph("문서에 명시된 값 없음"))
            for item in items:
                rendered = json.dumps(item, ensure_ascii=False) if isinstance(item, (dict, list)) else item
                story.append(paragraph(rendered if rendered else "문서에 명시된 값 없음"))

    doc = SimpleDocTemplate(
        str(output), pagesize=A4, leftMargin=48, rightMargin=48,
        topMargin=48, bottomMargin=48, title="기업 fact·CV·JD 기여 분석 입력",
    )
    doc.build(story)
    return output
