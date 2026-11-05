"""Expose comparable percentage rows to the brief agent with their original evidence."""

import argparse
import json
import re
from decimal import Decimal
from pathlib import Path


NUMBER = r"\d+(?:\.\d+)?"
DATED_ROW = re.compile(
    rf"(?P<label>[^/]+?)\s*/\s*제\d+기\s*\((?P<current_year>\d{{4}})년\)\s*"
    rf"(?P<current>{NUMBER})%\s*/\s*제\d+기\s*\((?P<prior_year>\d{{4}})년\)\s*(?P<prior>{NUMBER})%"
)
PERCENT_ROW = re.compile(
    rf"(?P<label>[^()]+?)\s*\(%\)\s+(?P<current>{NUMBER})\s+(?P<prior>{NUMBER})"
    rf"\s+[+-]?{NUMBER}\s+[+-]?{NUMBER}"
)


def prepare_brief_input(merged: dict) -> dict:
    """Keep the source facts and add only comparisons supported by their evidence."""
    facts = merged.get("facts") or []
    period = str(merged.get("report_period") or "")
    year_match = re.fullmatch(r"(\d{4})-\d{2}-\d{2}\s*~\s*\1-\d{2}-\d{2}", period)
    comparisons = []
    for fact in facts:
        quote = str((fact.get("evidence") or {}).get("quote") or "").strip()
        source_id = fact.get("id")
        if not source_id:
            continue
        dated = DATED_ROW.fullmatch(quote)
        if dated:
            row = dated.groupdict()
            if int(row["current_year"]) != int(row["prior_year"]) + 1:
                continue
            source_ids = [source_id]
        else:
            # A row without headers is usable only when a separate source
            # explicitly corroborates its current value and year-over-year change.
            numeric = PERCENT_ROW.fullmatch(quote)
            if not numeric or not year_match:
                continue
            row = numeric.groupdict()
            delta = Decimal(row["current"]) - Decimal(row["prior"])
            if not delta:
                continue
            direction = "증가" if delta > 0 else "감소"
            label = re.escape(row["label"].strip())
            pattern = re.compile(
                rf"{label}(?:이|가|은|는)?\s+전년\s*대비\s+(?P<change>{NUMBER})\s*%p\s*"
                rf"{direction}한\s+(?P<current>{NUMBER})\s*%"
            )
            corroborating = None
            for candidate in facts:
                if (candidate.get("source_batch") != fact.get("source_batch")
                        or candidate.get("source_document") != fact.get("source_document")
                        or not candidate.get("id") or candidate["id"] == source_id):
                    continue
                match = pattern.search(str((candidate.get("evidence") or {}).get("quote") or ""))
                if (match and Decimal(match["current"]) == Decimal(row["current"])
                        and Decimal(match["change"]) == abs(delta)):
                    corroborating = candidate["id"]
                    break
            if not corroborating:
                continue
            row["current_year"] = year_match[1]
            row["prior_year"] = str(int(year_match[1]) - 1)
            source_ids = [source_id, corroborating]
        if year_match and row["current_year"] != year_match[1]:
            continue
        current, prior = Decimal(row["current"]), Decimal(row["prior"])
        comparisons.append({
            "metric": row["label"].strip(),
            "current_year": int(row["current_year"]),
            "current_value": row["current"],
            "prior_year": int(row["prior_year"]),
            "prior_value": row["prior"],
            "unit": "%",
            "direction": "증가" if current > prior else "감소" if current < prior else "동일",
            "source_ids": source_ids,
        })
    return {**merged, "evidence_comparisons": comparisons}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    source = json.loads(args.input.read_text(encoding="utf-8"))
    with args.output.open("x", encoding="utf-8") as output:
        json.dump(prepare_brief_input(source), output, ensure_ascii=False, indent=2)
