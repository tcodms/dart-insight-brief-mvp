"""Automatically map a DART report to the three MVP analysis batches.

The detector uses PDF bookmarks (the table of contents embedded in DART PDFs)
as its primary source.  It never contains company-specific page numbers.  A
text-heading fallback is used for PDFs without bookmarks.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from pypdf import PdfReader


ROMAN_HEADING = re.compile(r"^\s*([IVXLC]+)\.\s*(.+?)\s*$", re.MULTILINE)

BUSINESS_TITLE_KEYWORDS = (
    "사업의 개요",
    "영업의 현황",
    "주요 제품",
    "주요 서비스",
    "시장",
    "경쟁",
    "매출",
    "연구개발",
    "설비",
    "원재료",
    "신규사업",
    "전략",
)

ESG_KEYWORDS = (
    "ESG",
    "환경경영",
    "기후리스크",
    "기후변화",
    "지속가능경영",
    "지속가능",
    "녹색금융",
    "탄소중립",
    "사회공헌",
    "인권경영",
    "다양성",
)

FINANCE_SUBSECTION_KEYWORDS = (
    "재무건전성",
    "재무 건전성",
    "건전성 및 기타 참고사항",
)

REPORT_METADATA_KEYWORDS = (
    "사업보고서",
    "반기보고서",
    "분기보고서",
    "보고기간",
    "회사명",
)

MAX_BUSINESS_PAGES = 80
MAX_FINANCE_PAGES = 80
MAX_WORKFORCE_ESG_PAGES = 50
FINANCE_FRONT_PAGES = 20


@dataclass(frozen=True)
class OutlineEntry:
    title: str
    page: int
    depth: int
    roman: str = ""


@dataclass(frozen=True)
class Section:
    roman: str
    title: str
    start_page: int
    end_page: int


def compact_ranges(pages: Iterable[int]) -> str:
    ordered = sorted(set(pages))
    if not ordered:
        return ""
    parts: list[str] = []
    start = previous = ordered[0]
    for page in ordered[1:]:
        if page == previous + 1:
            previous = page
            continue
        parts.append(str(start) if start == previous else f"{start}-{previous}")
        start = previous = page
    parts.append(str(start) if start == previous else f"{start}-{previous}")
    return ", ".join(parts)


def _roman_from_title(title: str) -> str:
    match = ROMAN_HEADING.match(title.strip())
    return match.group(1) if match else ""


def _flatten_outline(reader: PdfReader) -> list[OutlineEntry]:
    entries: list[OutlineEntry] = []

    def walk(items: list, depth: int) -> None:
        for item in items:
            if isinstance(item, list):
                walk(item, depth + 1)
                continue
            title = str(item.get("/Title", "")).strip()
            if not title:
                continue
            try:
                page = reader.get_destination_page_number(item) + 1
            except Exception:
                continue
            entries.append(
                OutlineEntry(
                    title=title,
                    page=page,
                    depth=depth,
                    roman=_roman_from_title(title) if depth == 0 else "",
                )
            )

    try:
        walk(reader.outline, 0)
    except Exception:
        return []
    return entries


def _headings_from_text(reader: PdfReader) -> list[OutlineEntry]:
    """Fallback for DART PDFs that have no bookmark tree."""
    entries: list[OutlineEntry] = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        # A top-level heading normally appears near the top of a DART page.
        for match in ROMAN_HEADING.finditer(text[:1400]):
            roman, title = match.groups()
            entries.append(
                OutlineEntry(
                    title=f"{roman}. {title.strip()}",
                    page=page_number,
                    depth=0,
                    roman=roman,
                )
            )
            break
    return entries


def _top_sections(entries: list[OutlineEntry], total_pages: int) -> list[Section]:
    starts: list[OutlineEntry] = []
    seen: set[str] = set()
    for entry in entries:
        if entry.depth != 0 or not entry.roman or entry.roman in seen:
            continue
        seen.add(entry.roman)
        starts.append(entry)
    starts.sort(key=lambda item: item.page)

    sections: list[Section] = []
    for index, entry in enumerate(starts):
        next_page = starts[index + 1].page if index + 1 < len(starts) else total_pages + 1
        sections.append(
            Section(
                roman=entry.roman,
                title=entry.title,
                start_page=entry.page,
                end_page=max(entry.page, next_page - 1),
            )
        )
    return sections


def _range(section: Section) -> list[int]:
    return list(range(section.start_page, section.end_page + 1))


def _bounded_section_pages(
    section: Section,
    entries: list[OutlineEntry],
    *,
    limit: int,
    title_keywords: tuple[str, ...],
) -> list[int]:
    pages = _range(section)
    if len(pages) <= limit:
        return pages

    selected = set(pages[:5] + pages[-3:])
    children = [
        entry
        for entry in entries
        if entry.depth > 0 and section.start_page <= entry.page <= section.end_page
    ]
    children.sort(key=lambda item: item.page)
    for index, child in enumerate(children):
        if not any(keyword in child.title for keyword in title_keywords):
            continue
        next_page = (
            children[index + 1].page
            if index + 1 < len(children)
            else section.end_page + 1
        )
        selected.update(range(child.page, min(next_page, child.page + 8)))
        if len(selected) >= limit:
            break
    return sorted(selected)[:limit]


def _keyword_pages(
    reader: PdfReader,
    candidate_pages: Iterable[int],
    keywords: tuple[str, ...],
) -> tuple[list[int], dict[int, list[str]]]:
    hits: dict[int, list[str]] = {}
    candidates = sorted(set(candidate_pages))
    candidate_set = set(candidates)
    for page_number in candidates:
        text = reader.pages[page_number - 1].extract_text() or ""
        matched = [keyword for keyword in keywords if keyword.casefold() in text.casefold()]
        if matched:
            hits[page_number] = matched

    expanded: set[int] = set()
    for page_number in hits:
        for neighbor in (page_number - 1, page_number, page_number + 1):
            if neighbor in candidate_set:
                expanded.add(neighbor)
    return sorted(expanded), hits


def _direct_children(
    entries: list[OutlineEntry], section: Section
) -> list[OutlineEntry]:
    return sorted(
        (
            entry
            for entry in entries
            if entry.depth == 1
            and section.start_page <= entry.page <= section.end_page
        ),
        key=lambda item: item.page,
    )


def _child_pages(
    children: list[OutlineEntry], index: int, section_end: int
) -> list[int]:
    start = children[index].page
    end = children[index + 1].page - 1 if index + 1 < len(children) else section_end
    return list(range(start, max(start, end) + 1))


def _metadata_pages(reader: PdfReader, first_section_page: int) -> list[int]:
    """Find the filing cover without assuming a fixed physical page."""
    scored: list[tuple[int, int]] = []
    for page_number in range(1, first_section_page):
        text = (reader.pages[page_number - 1].extract_text() or "").replace(" ", "")
        score = sum(keyword.replace(" ", "") in text for keyword in REPORT_METADATA_KEYWORDS)
        if score:
            scored.append((score, page_number))
    if not scored:
        return []
    best_score = max(score for score, _ in scored)
    return [page for score, page in scored if score == best_score][:2]


def detect_report_sections(source_pdf: str) -> dict:
    reader = PdfReader(source_pdf)
    if reader.is_encrypted:
        raise ValueError("암호화된 PDF는 자동 전처리할 수 없습니다.")
    total_pages = len(reader.pages)
    if total_pages == 0:
        raise ValueError("페이지가 없는 PDF입니다.")

    entries = _flatten_outline(reader)
    detection_source = "pdf_outline"
    sections = _top_sections(entries, total_pages)
    if not sections:
        entries = _headings_from_text(reader)
        sections = _top_sections(entries, total_pages)
        detection_source = "page_heading_text"

    by_roman = {section.roman: section for section in sections}
    required = {"I", "II", "III", "VIII"}
    missing = sorted(required - set(by_roman))
    if missing:
        raise ValueError(
            "DART 목차 구조를 자동 인식하지 못했습니다. "
            f"누락된 상위 장: {', '.join(missing)}. 임의 페이지로 분할하지 않습니다."
        )

    metadata_pages = _metadata_pages(reader, by_roman["I"].start_page)
    business: set[int] = set(metadata_pages)
    business_reasons: list[str] = []
    for roman, limit in (("I", 30), ("II", 50)):
        section = by_roman[roman]
        if roman == "II":
            children = _direct_children(entries, section)
            finance_child_index = next(
                (
                    index
                    for index, child in enumerate(children)
                    if any(
                        keyword in child.title
                        for keyword in FINANCE_SUBSECTION_KEYWORDS
                    )
                ),
                None,
            )
            if finance_child_index is not None:
                end_page = children[finance_child_index].page - 1
                selected = list(range(section.start_page, end_page + 1))[:limit]
            else:
                selected = _bounded_section_pages(
                    section,
                    entries,
                    limit=limit,
                    title_keywords=BUSINESS_TITLE_KEYWORDS,
                )
        else:
            selected = _bounded_section_pages(
                section,
                entries,
                limit=limit,
                title_keywords=BUSINESS_TITLE_KEYWORDS,
            )
        business.update(selected)
        business_reasons.append(
            f"{section.title}: {compact_ranges(selected)}"
        )

    finance: set[int] = set(metadata_pages)
    finance_reasons: list[str] = []
    business_section = by_roman["II"]
    business_children = _direct_children(entries, business_section)
    for index, child in enumerate(business_children):
        if any(keyword in child.title for keyword in FINANCE_SUBSECTION_KEYWORDS):
            pages = _child_pages(business_children, index, business_section.end_page)
            finance.update(pages)
            finance_reasons.append(
                f"{child.title}: {compact_ranges(pages)}"
            )

    finance_section = by_roman["III"]
    finance_children = _direct_children(entries, finance_section)
    summary_index = next(
        (
            index
            for index, child in enumerate(finance_children)
            if "요약재무정보" in child.title.replace(" ", "")
        ),
        None,
    )
    if summary_index is not None:
        finance_front = _child_pages(
            finance_children, summary_index, finance_section.end_page
        )
    else:
        finance_front = _range(finance_section)[:FINANCE_FRONT_PAGES]
    finance.update(finance_front)
    finance_reasons.append(
        f"{finance_section.title} 앞부분(요약재무정보 및 주요 재무표): "
        f"{compact_ranges(finance_front)}"
    )
    if "IV" in by_roman:
        mda = _range(by_roman["IV"])
        finance.update(mda)
        finance_reasons.append(
            f"{by_roman['IV'].title}: {compact_ranges(mda)}"
        )
    if "V" in by_roman:
        audit = _range(by_roman["V"])
        finance.update(audit)
        finance_reasons.append(
            f"{by_roman['V'].title}: {compact_ranges(audit)}"
        )
    finance = set(sorted(finance)[:MAX_FINANCE_PAGES])

    workforce_section = by_roman["VIII"]
    workforce = set(metadata_pages + _range(workforce_section))
    workforce_reasons = [
        f"{workforce_section.title}: {compact_ranges(workforce)}"
    ]

    # ESG disclosure is not assigned a fixed DART chapter. Search all
    # non-financial chapters and preserve one-page context around every hit.
    esg_candidates: set[int] = set()
    for section in sections:
        if section.roman in {"VI", "VII", "VIII", "IX", "X", "XI"}:
            esg_candidates.update(_range(section))
    esg_pages, esg_hits = _keyword_pages(reader, esg_candidates, ESG_KEYWORDS)
    workforce.update(esg_pages)
    if esg_pages:
        workforce_reasons.append(
            "ESG 키워드가 직접 확인된 페이지와 인접 문맥: "
            f"{compact_ranges(esg_pages)}"
        )

    batches = {
        "01_business_strategy": sorted(business)[:MAX_BUSINESS_PAGES],
        "02_finance_management": sorted(finance)[:MAX_FINANCE_PAGES],
        "03_workforce_esg": sorted(workforce)[:MAX_WORKFORCE_ESG_PAGES],
    }
    empty = [name for name, pages in batches.items() if not pages]
    if empty:
        raise ValueError(f"자동 분류 결과가 비어 있습니다: {', '.join(empty)}")

    return {
        "method": detection_source,
        "source_page_count": total_pages,
        "top_level_sections": [
            {
                "roman": section.roman,
                "title": section.title,
                "start_page": section.start_page,
                "end_page": section.end_page,
            }
            for section in sections
        ],
        "batches": batches,
        "selection_reasons": {
            "01_business_strategy": business_reasons,
            "02_finance_management": finance_reasons,
            "03_workforce_esg": workforce_reasons,
        },
        "keyword_hits": {
            str(page): values for page, values in sorted(esg_hits.items())
        },
        "metadata_pages": metadata_pages,
    }
