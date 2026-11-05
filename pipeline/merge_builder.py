"""Validate and merge the three Extract Agent outputs."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


LOCAL_ID_RE = re.compile(r"^\[?(E\d{3,})\]?\s*(.*)$", re.DOTALL)
EVIDENCE_RE = re.compile(
    r"^\[?(E\d{3,})\]?\s*\|\s*original_page=(\d+)\s*\|\s*section=(.*?)\s*\|\s*quote=(.*)$",
    re.DOTALL,
)
JO_EOK_VALUE_RE = re.compile(
    r"value=(\d+)조\s*([\d,]+)\s*\|\s*unit=억원"
)

METADATA_FIELDS = {
    "company_name",
    "report_type",
    "report_period",
    "filing_date",
    "source_batch",
    "source_document",
}
SPECIAL_FIELDS = METADATA_FIELDS | {"evidence_refs", "limitations"}


class MergeValidationError(ValueError):
    pass


@dataclass(frozen=True)
class BatchInput:
    prefix: str
    expected_source_batch: str
    data: dict[str, Any]


def _single_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return str(value[0]).strip() if value else ""
    return str(value).strip()


def _string_list(value: Any, field_name: str) -> list[str]:
    if value in (None, ""):
        return []
    if isinstance(value, str):
        return [value]
    if not isinstance(value, list):
        raise MergeValidationError(f"{field_name}은 문자열 목록이어야 합니다.")
    return [str(item) for item in value if str(item).strip()]


def _parse_fact(raw: str, field_name: str) -> tuple[str, str]:
    match = LOCAL_ID_RE.match(raw.strip())
    if not match:
        raise MergeValidationError(f"{field_name} 항목에 [E###] ID가 없습니다: {raw[:80]}")
    local_id, statement = match.groups()
    return local_id, _normalize_statement(statement.strip())


def _normalize_statement(statement: str) -> str:
    """Normalize deterministic number formats without changing their value."""

    def replace_jo_eok(match: re.Match[str]) -> str:
        jo = int(match.group(1))
        eok = int(match.group(2).replace(",", ""))
        total_eok = jo * 10_000 + eok
        return f"value={total_eok:,} | unit=억원"

    return JO_EOK_VALUE_RE.sub(replace_jo_eok, statement)


def _parse_evidence(raw: str) -> tuple[str, dict[str, Any]]:
    match = EVIDENCE_RE.match(raw.strip())
    if not match:
        raise MergeValidationError(f"evidence_refs 형식이 올바르지 않습니다: {raw[:120]}")
    local_id, page, section, quote = match.groups()
    return local_id, {
        "original_page": int(page),
        "section": section.strip(),
        "quote": quote.strip(),
        "raw": raw.strip(),
    }


def _resolve_metadata(batches: list[BatchInput], field_name: str) -> tuple[str, list[str]]:
    values = [_single_text(batch.data.get(field_name)) for batch in batches]
    present = [value for value in values if value]
    unique = list(dict.fromkeys(present))
    warnings: list[str] = []
    if len(unique) > 1:
        warnings.append(f"{field_name} 값이 배치마다 다릅니다: {unique}")
    return (unique[0] if unique else ""), warnings


def merge_extract_results(batch_payloads: list[tuple[str, str, dict]]) -> dict:
    """Merge ``(B01, expected_source_batch, result)`` tuples into one JSON object."""
    if len(batch_payloads) != 3:
        raise MergeValidationError("Agent 1·2·3 결과 세 개가 모두 필요합니다.")

    batches = [BatchInput(*payload) for payload in batch_payloads]
    merge_warnings: list[str] = []
    merged_metadata: dict[str, str] = {}
    for field_name in ("company_name", "report_type", "report_period", "filing_date"):
        value, warnings = _resolve_metadata(batches, field_name)
        merged_metadata[field_name] = value
        merge_warnings.extend(warnings)

    facts: list[dict[str, Any]] = []
    merged_evidence_refs: list[str] = []
    limitations: list[str] = []
    seen_global_ids: set[str] = set()
    seen_fact_keys: set[tuple[int, str, str]] = set()
    source_documents: list[str] = []
    batch_summaries: list[dict[str, Any]] = []

    for batch in batches:
        data = batch.data
        if not isinstance(data, dict):
            raise MergeValidationError(f"{batch.prefix} 결과는 JSON 객체여야 합니다.")

        actual_source_batch = _single_text(data.get("source_batch"))
        if actual_source_batch and actual_source_batch != batch.expected_source_batch:
            merge_warnings.append(
                f"{batch.prefix} source_batch 예상값은 {batch.expected_source_batch}이지만 "
                f"결과는 {actual_source_batch}입니다."
            )

        source_document = _single_text(data.get("source_document"))
        if source_document and source_document not in source_documents:
            source_documents.append(source_document)

        evidence_by_id: dict[str, dict[str, Any]] = {}
        for raw_evidence in _string_list(data.get("evidence_refs"), "evidence_refs"):
            local_id, parsed = _parse_evidence(raw_evidence)
            if local_id in evidence_by_id:
                raise MergeValidationError(f"{batch.prefix}에 중복 근거 ID가 있습니다: {local_id}")
            evidence_by_id[local_id] = parsed

        local_fact_ids: set[str] = set()
        kept_count = 0
        for field_name, raw_value in data.items():
            if field_name in SPECIAL_FIELDS:
                continue
            for raw_fact in _string_list(raw_value, field_name):
                local_id, statement = _parse_fact(raw_fact, field_name)
                if local_id in local_fact_ids:
                    raise MergeValidationError(f"{batch.prefix}에 중복 사실 ID가 있습니다: {local_id}")
                local_fact_ids.add(local_id)

                evidence = evidence_by_id.get(local_id)
                if evidence is None:
                    raise MergeValidationError(
                        f"{batch.prefix}-{local_id} 사실에 대응하는 evidence_refs가 없습니다."
                    )

                global_id = f"{batch.prefix}-{local_id}"
                if global_id in seen_global_ids:
                    raise MergeValidationError(f"병합 ID가 중복됩니다: {global_id}")
                seen_global_ids.add(global_id)

                duplicate_key = (
                    evidence["original_page"],
                    evidence["quote"].strip(),
                    statement.strip(),
                )
                if duplicate_key in seen_fact_keys:
                    merge_warnings.append(f"완전 중복 사실을 제외했습니다: {global_id}")
                    continue
                seen_fact_keys.add(duplicate_key)

                prefixed_statement = f"[{global_id}] {statement}"
                prefixed_evidence = (
                    f"{global_id} | original_page={evidence['original_page']} | "
                    f"section={evidence['section']} | quote={evidence['quote']}"
                )
                facts.append(
                    {
                        "id": global_id,
                        "category": field_name,
                        "statement": statement,
                        "display": prefixed_statement,
                        "source_batch": batch.expected_source_batch,
                        "source_document": source_document,
                        "evidence_id": global_id,
                        "evidence": {
                            "original_page": evidence["original_page"],
                            "section": evidence["section"],
                            "quote": evidence["quote"],
                        },
                    }
                )
                merged_evidence_refs.append(prefixed_evidence)
                kept_count += 1

        unused_evidence = sorted(set(evidence_by_id) - local_fact_ids)
        if unused_evidence:
            raise MergeValidationError(
                f"{batch.prefix}에 사실과 연결되지 않은 근거 ID가 있습니다: {unused_evidence}"
            )

        for item in _string_list(data.get("limitations"), "limitations"):
            tagged = f"{batch.prefix} | {item.strip()}"
            if tagged not in limitations:
                limitations.append(tagged)

        batch_summaries.append(
            {
                "batch_prefix": batch.prefix,
                "source_batch": batch.expected_source_batch,
                "source_document": source_document,
                "fact_count": kept_count,
            }
        )

    if not facts:
        raise MergeValidationError("병합할 사실이 하나도 없습니다.")

    return {
        **merged_metadata,
        "source_documents": source_documents,
        "batches": batch_summaries,
        "facts": facts,
        "evidence_refs": merged_evidence_refs,
        "limitations": limitations,
        "merge_warnings": merge_warnings,
        "fact_count": len(facts),
    }
