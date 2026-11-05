"""Reconcile Agent evidence page numbers with the original PDF text."""

from __future__ import annotations

import copy
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from pypdf import PdfReader


EVIDENCE_RE = re.compile(
    r"^(E\d{3,})\s*\|\s*original_page=(\d+)\s*\|\s*"
    r"section=(.*?)\s*\|\s*quote=(.*)$",
    re.DOTALL,
)
TOKEN_RE = re.compile(r"[0-9A-Za-z가-힣.%△]+")


def _normalize(text: str) -> str:
    return re.sub(r"[^0-9A-Za-z가-힣.%△]+", "", text).casefold()


def _match_score(quote: str, page_text: str) -> float:
    quote_normalized = _normalize(quote)
    text_normalized = _normalize(page_text)
    if not quote_normalized:
        return 0.0
    if quote_normalized in text_normalized:
        return 1.0
    tokens = [
        _normalize(token)
        for token in TOKEN_RE.findall(quote)
        if len(_normalize(token)) >= 2
    ]
    token_score = (
        sum(token in text_normalized for token in tokens) / len(tokens)
        if tokens
        else 0.0
    )
    longest = SequenceMatcher(
        None, quote_normalized, text_normalized, autojunk=False
    ).find_longest_match()
    sequence_score = longest.size / len(quote_normalized)
    return max(token_score, sequence_score)


def reconcile_evidence_pages(
    result: dict[str, Any],
    source_pdf: str | Path,
    selected_pages: list[int],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Correct only high-confidence page mismatches; never guess weak matches."""
    revised = copy.deepcopy(result)
    raw_evidence = revised.get("evidence_refs") or []
    if isinstance(raw_evidence, str):
        raw_evidence = [raw_evidence]
    if not isinstance(raw_evidence, list) or not raw_evidence:
        return revised, []

    reader = PdfReader(str(source_pdf))
    candidates = sorted(
        page for page in set(selected_pages) if 1 <= page <= len(reader.pages)
    )
    texts = {
        page: reader.pages[page - 1].extract_text() or "" for page in candidates
    }

    corrected_refs: list[str] = []
    corrections: list[dict[str, Any]] = []
    for raw in raw_evidence:
        text = str(raw).strip()
        match = EVIDENCE_RE.match(text)
        if not match:
            corrected_refs.append(text)
            continue
        evidence_id, page_text, section, quote = match.groups()
        stated_page = int(page_text)
        stated_score = _match_score(quote, texts.get(stated_page, ""))
        ranked = sorted(
            ((_match_score(quote, texts[page]), page) for page in candidates),
            reverse=True,
        )
        best_score, best_page = ranked[0] if ranked else (0.0, stated_page)
        should_correct = (
            best_page != stated_page
            and best_score >= 0.80
            and best_score - stated_score >= 0.25
        )
        if should_correct:
            corrected_refs.append(
                f"{evidence_id} | original_page={best_page} | "
                f"section={section.strip()} | quote={quote.strip()}"
            )
            corrections.append(
                {
                    "evidence_id": evidence_id,
                    "from_page": stated_page,
                    "to_page": best_page,
                    "stated_score": round(stated_score, 3),
                    "matched_score": round(best_score, 3),
                }
            )
        else:
            corrected_refs.append(text)

    revised["evidence_refs"] = corrected_refs
    page_changes: dict[int, set[int]] = {}
    for correction in corrections:
        page_changes.setdefault(correction["from_page"], set()).add(
            correction["to_page"]
        )
    unambiguous = {
        old: next(iter(new_pages))
        for old, new_pages in page_changes.items()
        if len(new_pages) == 1
    }
    limitations = revised.get("limitations") or []
    if isinstance(limitations, list):
        updated: list[str] = []
        for limitation in limitations:
            value = str(limitation)
            for old, new in unambiguous.items():
                value = re.sub(
                    rf"(ORIGINAL_PDF_PAGE\s*){old}(?!\d)",
                    rf"\g<1>{new}",
                    value,
                )
            updated.append(value)
        revised["limitations"] = updated
    return revised, corrections
