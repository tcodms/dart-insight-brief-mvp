"""CV/JD extraction -> company fact input -> contribution report."""

from __future__ import annotations

import json
import re
from pathlib import Path

from agent_client import AgentClient, ProgressCallback
from candidate_document_service import run_candidate_document_analysis
from config import (
    validate_candidate_config,
    validate_contribution_config,
)
from contribution_input import build_contribution_input_pdf
from file_manager import save_text
from upload import upload_file


def _report_text(output_text: str) -> str:
    raw = output_text.strip()
    if not raw:
        raise ValueError("기여 에이전트 응답이 비어 있습니다.")
    try:
        decoded = json.loads(raw)
    except json.JSONDecodeError:
        decoded = raw
    if not isinstance(decoded, str) or not decoded.strip():
        raise ValueError("기여 에이전트 결과가 보고서 텍스트가 아닙니다.")
    # Studio may emit numbered markers without resolvable annotation metadata.
    return re.sub(r"【†\d+】", "", decoded).strip()


def run_contribution_pipeline(
    cv_path: str | Path,
    jd_path: str | Path,
    company_fact_path: str | Path,
    *,
    progress: ProgressCallback | None = None,
) -> dict:
    """Create the personalized report using this company's merged fact file."""
    fact_path = Path(company_fact_path)
    if not fact_path.is_file():
        raise FileNotFoundError(f"기업 fact 파일을 찾을 수 없습니다: {fact_path}")
    merged = json.loads(fact_path.read_text(encoding="utf-8"))
    if not isinstance(merged, dict) or not merged.get("facts"):
        raise ValueError("기업 fact 파일에 병합된 facts가 없습니다.")
    validate_candidate_config(include_cv=True, include_jd=True)
    contribution_config = validate_contribution_config()

    candidate = run_candidate_document_analysis(cv_path, jd_path, progress=progress)
    run_dir = Path(candidate["run_dir"])
    input_pdf = build_contribution_input_pdf(
        merged, candidate["cv"], candidate["jd"], run_dir / "contribution_input.pdf"
    )
    if progress:
        progress("기업 fact·CV·JD 결과를 기여 에이전트에 전달합니다.")
    file_id = upload_file(
        input_pdf, api_key=contribution_config["CANDIDATE_UPSTAGE_API_KEY"]
    )
    client = AgentClient(
        contribution_config["CONTRIBUTION_AGENT_ID"],
        contribution_config["CONTRIBUTION_CONFIG_ID"],
        api_key=contribution_config["CANDIDATE_UPSTAGE_API_KEY"],
        max_wait_seconds=1800,
    )
    job_id = client.create_job(file_id)
    response = client.wait_until_complete(job_id, progress=progress)
    raw_text = (getattr(response, "output_text", None) or "").strip()
    report = _report_text(raw_text)
    raw_path = save_text(raw_text, run_dir / "contribution_result_raw.txt")
    report_path = save_text(report, run_dir / "contribution_result.md")
    return {
        "report": report,
        "run_dir": str(run_dir),
        "paths": {
            **candidate["paths"],
            "input_pdf": str(input_pdf),
            "raw": str(raw_path),
            "report_markdown": str(report_path),
        },
    }
