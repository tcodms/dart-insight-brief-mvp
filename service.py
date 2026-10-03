"""Business workflow: preprocess -> three extracts -> merge -> company brief."""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from datetime import datetime
from pathlib import Path
from queue import Empty, Queue
import re
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
EXTRACT_AGENT_WORKERS = 3
JOB_CREATION_ID_PATTERN = re.compile(r"(Agent 작업 생성)\s*:\s*job_[A-Za-z0-9_-]+")
JOB_STATUS_ID_PATTERN = re.compile(r"\s*\(job=job_[A-Za-z0-9_-]+\)")


def sanitize_progress_message(message: str) -> str:
    message = JOB_CREATION_ID_PATTERN.sub(r"\1", str(message))
    return JOB_STATUS_ID_PATTERN.sub("", message)


def _notify(callback: ProgressCallback | None, message: str) -> None:
    message = sanitize_progress_message(message)
    print(message)
    if callback:
        callback(message)


def _new_run_dir() -> Path:
    run_id = f"{datetime.now():%Y%m%d-%H%M%S}-{uuid4().hex[:8]}"
    path = RUNS_DIR / run_id
    path.mkdir(parents=True, exist_ok=False)
    return path


def _drain_progress_messages(
    messages: Queue[str], callback: ProgressCallback | None
) -> None:
    while True:
        try:
            message = messages.get_nowait()
        except Empty:
            return
        _notify(callback, message)


def _run_extract_step(
    *,
    report_path: str | Path,
    manifest: dict,
    run_dir: Path,
    step: tuple[str, str, str, str, Callable],
    progress_messages: Queue[str],
) -> tuple[str, str, dict, list[dict]]:
    prefix, batch_id, output_name, label, analyzer = step
    batch_pdf = Path(manifest["batches"][batch_id]["output_pdf"])
    file_id = upload_file(batch_pdf)

    def queue_progress(message: str) -> None:
        progress_messages.put(f"{label}: {message}")

    result = analyzer(file_id, progress=queue_progress)
    result, corrections = reconcile_evidence_pages(
        result,
        report_path,
        manifest["batches"][batch_id]["selected_pages"],
    )
    if corrections:
        progress_messages.put(
            f"{label}: 원문 인용 대조로 근거 페이지 {len(corrections)}건을 교정했습니다."
        )
    save_json(result, run_dir / output_name)
    return prefix, batch_id, result, corrections


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
    progress_messages: Queue[str] = Queue()
    failures: list[tuple[str, Exception]] = []

    _notify(progress, "2~4/6 Agent 1·2·3을 병렬로 실행합니다.")
    with ThreadPoolExecutor(
        max_workers=EXTRACT_AGENT_WORKERS,
        thread_name_prefix="extract-agent",
    ) as executor:
        future_steps: dict[Future, tuple[str, str, str, str, Callable]] = {}
        for step in agent_steps:
            _notify(progress, f"{step[3]} 시작")
            future = executor.submit(
                _run_extract_step,
                report_path=report_path,
                manifest=manifest,
                run_dir=run_dir,
                step=step,
                progress_messages=progress_messages,
            )
            future_steps[future] = step

        pending = set(future_steps)
        while pending:
            completed, pending = wait(
                pending,
                timeout=0.25,
                return_when=FIRST_COMPLETED,
            )
            _drain_progress_messages(progress_messages, progress)
            for future in completed:
                step = future_steps[future]
                try:
                    prefix, batch_id, result, corrections = future.result()
                except Exception as exc:  # Other agents should still finish and save.
                    failures.append((step[3], exc))
                    _notify(progress, f"{step[3]} 실패: {exc}")
                    continue
                extract_results[batch_id] = result
                evidence_page_corrections[batch_id] = corrections
                _notify(progress, f"{step[3]} 완료")

    _drain_progress_messages(progress_messages, progress)
    if failures:
        details = "; ".join(f"{label}: {exc}" for label, exc in failures)
        raise RuntimeError(
            "Extract Agent 병렬 실행 중 일부 작업이 실패했습니다. "
            f"성공한 중간 결과는 실행 폴더에 보존했습니다. {details}"
        )

    # Completion order is nondeterministic; merge order must remain B01, B02, B03.
    merge_inputs = [
        (prefix, batch_id, extract_results[batch_id])
        for prefix, batch_id, _output_name, _label, _analyzer in agent_steps
    ]

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
