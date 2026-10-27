"""Independent CV/JD PDF analysis, separate from the company brief pipeline."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from uuid import uuid4

from agent_client import ProgressCallback
from config import CANDIDATE_RUNS_DIR, CANDIDATE_UPSTAGE_API_KEY, validate_candidate_config
from cv_agent import analyze_cv
from file_manager import save_json
from jd_agent import analyze_jd
from upload import upload_file


def _pdf_path(value: str | Path, label: str) -> Path:
    path = Path(value).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"{label} PDF를 찾을 수 없습니다: {path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"{label} 입력은 PDF 파일이어야 합니다: {path}")
    return path


def run_candidate_document_analysis(
    cv_path: str | Path | None = None,
    jd_path: str | Path | None = None,
    *,
    progress: ProgressCallback | None = None,
) -> dict:
    """Upload supplied PDFs, invoke their Studio agents, and save each JSON result."""
    if cv_path is None and jd_path is None:
        raise ValueError("CV 또는 JD PDF를 하나 이상 지정하세요.")

    cv_pdf = _pdf_path(cv_path, "CV") if cv_path is not None else None
    jd_pdf = _pdf_path(jd_path, "JD") if jd_path is not None else None
    validate_candidate_config(include_cv=cv_pdf is not None, include_jd=jd_pdf is not None)

    run_id = f"{datetime.now():%Y%m%d-%H%M%S}-{uuid4().hex[:8]}"
    run_dir = CANDIDATE_RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    result = {"run_dir": str(run_dir.resolve()), "cv": None, "jd": None, "paths": {}}

    for label, pdf, analyzer, output_name in (
        ("cv", cv_pdf, analyze_cv, "cv_result.json"),
        ("jd", jd_pdf, analyze_jd, "jd_result.json"),
    ):
        if pdf is None:
            continue
        if progress:
            progress(f"{label.upper()} PDF 업로드 및 Agent 분석")
        file_id = upload_file(pdf, api_key=CANDIDATE_UPSTAGE_API_KEY)
        analysis = analyzer(file_id, progress=progress)
        output_path = save_json(analysis, run_dir / output_name)
        result[label] = analysis
        result["paths"][f"{label}_json"] = str(output_path.resolve())

    return result
