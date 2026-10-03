"""Business workflow: preprocess -> three extracts -> merge -> company brief."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from brief_renderer import render_company_brief
from business_strategy_agent import analyze_business_strategy
from company_brief_agent import analyze_company_brief
from config import RESULT_DIR, RUNS_DIR, create_directories, validate_config
from evidence_validator import reconcile_evidence_pages
from file_manager import save_json, save_text
from finance_management_agent import analyze_finance_management
from merge_builder import merge_extract_results
from preprocessor import preprocess_report
from upload import upload_file
from workforce_esg_agent import analyze_workforce_esg


ProgressCallback = Callable[[str], None]


def _notify(callback: ProgressCallback | None, message: str) -> None:
    print(message)
    if callback:
        callback(message)


def _new_run_dir() -> Path:
    run_id = f"{datetime.now():%Y%m%d-%H%M%S}-{uuid4().hex[:8]}"
    path = RUNS_DIR / run_id
    path.mkdir(parents=True, exist_ok=False)
    return path


def run_company_brief_pipeline(
    report_path: str | Path,
    *,
    source_document_name: str | None = None,
    progress: ProgressCallback | None = None,
) -> dict:
    validate_config()
    create_directories()
    run_dir = _new_run_dir()
    batch_dir = run_dir / "batches"

    _notify(progress, "1/6 DART 목차를 분석해 세 구간을 자동 전처리합니다.")
    manifest = preprocess_report(
        report_path,
        batch_dir,
        source_document_name=source_document_name,
    )

    agent_steps = [
        (
            "B01",
            "01_business_strategy",
            "01_business_strategy_result.json",
            "2/6 Agent 1 사업·전략 추출",
            analyze_business_strategy,
        ),
        (
            "B02",
            "02_finance_management",
            "02_finance_management_result.json",
            "3/6 Agent 2 재무·경영진단 추출",
            analyze_finance_management,
        ),
        (
            "B03",
            "03_workforce_esg",
            "03_workforce_esg_result.json",
            "4/6 Agent 3 인력·조직·ESG 추출",
            analyze_workforce_esg,
        ),
    ]

    extract_results: dict[str, dict] = {}
    evidence_page_corrections: dict[str, list[dict]] = {}
    merge_inputs: list[tuple[str, str, dict]] = []

    for prefix, batch_id, output_name, label, analyzer in agent_steps:
        _notify(progress, label)
        batch_pdf = Path(manifest["batches"][batch_id]["output_pdf"])
        file_id = upload_file(batch_pdf)
        result = analyzer(file_id, progress=progress)
        result, corrections = reconcile_evidence_pages(
            result,
            report_path,
            manifest["batches"][batch_id]["selected_pages"],
        )
        evidence_page_corrections[batch_id] = corrections
        if corrections:
            _notify(
                progress,
                f"{label}: 원문 인용 대조로 근거 페이지 {len(corrections)}건을 교정했습니다.",
            )
        save_json(result, run_dir / output_name)
        extract_results[batch_id] = result
        merge_inputs.append((prefix, batch_id, result))

    _notify(progress, "5/6 세 결과를 검증하고 merged_company_data.json으로 병합합니다.")
    merged = merge_extract_results(merge_inputs)
    merged_path = save_json(merged, run_dir / "merged_company_data.json")
    correction_path = save_json(
        evidence_page_corrections,
        run_dir / "evidence_page_corrections.json",
    )

    _notify(progress, "6/6 Agent 4 취업용 기업분석 브리프를 생성합니다.")
    merged_file_id = upload_file(merged_path)
    company_brief = analyze_company_brief(merged_file_id, progress=progress)
    brief_json_path = save_json(company_brief, run_dir / "company_brief_result.json")
    brief_markdown = render_company_brief(company_brief)
    brief_markdown_path = save_text(brief_markdown, run_dir / "company_brief.md")

    save_json(company_brief, RESULT_DIR / "latest_company_brief.json")
    save_text(brief_markdown, RESULT_DIR / "latest_company_brief.md")

    _notify(progress, "분석이 완료되었습니다.")
    return {
        "run_dir": str(run_dir.resolve()),
        "manifest": manifest,
        "extract_results": extract_results,
        "evidence_page_corrections": evidence_page_corrections,
        "merged_company_data": merged,
        "company_brief": company_brief,
        "company_brief_markdown": brief_markdown,
        "paths": {
            "manifest": str((batch_dir / "preprocess_manifest.json").resolve()),
            "merged": str(merged_path.resolve()),
            "brief_json": str(brief_json_path.resolve()),
            "brief_markdown": str(brief_markdown_path.resolve()),
            "extract_1": str((run_dir / "01_business_strategy_result.json").resolve()),
            "extract_2": str((run_dir / "02_finance_management_result.json").resolve()),
            "extract_3": str((run_dir / "03_workforce_esg_result.json").resolve()),
            "evidence_page_corrections": str(correction_path.resolve()),
        },
    }
