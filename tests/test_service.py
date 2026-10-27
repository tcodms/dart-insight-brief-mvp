from __future__ import annotations

import threading
from pathlib import Path

import pytest

import service


def test_sanitize_progress_message_removes_internal_job_ids() -> None:
    assert service.sanitize_progress_message(
        "Agent 작업 생성: job_GoPvMbd6ki4iVQ69sts2Cm"
    ) == "Agent 작업 생성"
    assert service.sanitize_progress_message(
        "Agent 상태: in_progress (job=job_GoPvMbd6ki4iVQ69sts2Cm)"
    ) == "Agent 상태: in_progress"
    assert service.sanitize_progress_message(
        "2/6 Agent 1 사업·전략 추출: Agent 작업 생성: job_secret"
    ) == "2/6 Agent 1 사업·전략 추출: Agent 작업 생성"


def _configure_pipeline(monkeypatch, tmp_path: Path) -> None:
    run_root = tmp_path / "runs"
    result_root = tmp_path / "result"
    run_root.mkdir()
    result_root.mkdir()
    monkeypatch.setattr(service, "RUNS_DIR", run_root)
    monkeypatch.setattr(service, "RESULT_DIR", result_root)
    monkeypatch.setattr(service, "validate_config", lambda: None)
    monkeypatch.setattr(service, "create_directories", lambda: None)
    monkeypatch.setattr(
        service,
        "preprocess_report",
        lambda *_args, **_kwargs: {
            "batches": {
                batch_id: {
                    "output_pdf": str(tmp_path / f"{batch_id}.pdf"),
                    "selected_pages": [1],
                }
                for batch_id in (
                    "01_business_strategy",
                    "02_finance_management",
                    "03_workforce_esg",
                )
            }
        },
    )
    monkeypatch.setattr(service, "upload_file", lambda path: Path(path).stem)
    monkeypatch.setattr(
        service,
        "reconcile_evidence_pages",
        lambda result, *_args, **_kwargs: (result, []),
    )
    monkeypatch.setattr(
        service,
        "merge_extract_results",
        lambda inputs: {"order": [batch_id for _, batch_id, _ in inputs]},
    )
    monkeypatch.setattr(service, "analyze_company_brief", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(service, "render_company_brief", lambda _brief: "brief")


def test_extract_agents_run_in_parallel_and_merge_in_fixed_order(
    monkeypatch, tmp_path: Path
) -> None:
    _configure_pipeline(monkeypatch, tmp_path)
    barrier = threading.Barrier(3, timeout=3)

    def analyzer(name: str):
        def run(_file_id: str, *, progress=None) -> dict:
            if progress:
                progress("running")
            barrier.wait()
            return {"agent": name}

        return run

    monkeypatch.setattr(service, "analyze_business_strategy", analyzer("one"))
    monkeypatch.setattr(service, "analyze_finance_management", analyzer("two"))
    monkeypatch.setattr(service, "analyze_workforce_esg", analyzer("three"))

    main_thread = threading.get_ident()
    callback_threads: list[int] = []
    result = service.run_company_brief_pipeline(
        tmp_path / "report.pdf",
        progress=lambda _message: callback_threads.append(threading.get_ident()),
    )

    assert result["merged_company_data"]["order"] == [
        "01_business_strategy",
        "02_finance_management",
        "03_workforce_esg",
    ]
    assert set(result["extract_results"]) == {
        "01_business_strategy",
        "02_finance_management",
        "03_workforce_esg",
    }
    assert set(callback_threads) == {main_thread}


def test_parallel_failure_preserves_successful_results_and_blocks_agent_4(
    monkeypatch, tmp_path: Path
) -> None:
    _configure_pipeline(monkeypatch, tmp_path)
    agent_4_called = False

    def success(name: str):
        return lambda _file_id, *, progress=None: {"agent": name}

    def fail(_file_id: str, *, progress=None) -> dict:
        raise RuntimeError("finance failed")

    def agent_4(*_args, **_kwargs) -> dict:
        nonlocal agent_4_called
        agent_4_called = True
        return {}

    monkeypatch.setattr(service, "analyze_business_strategy", success("one"))
    monkeypatch.setattr(service, "analyze_finance_management", fail)
    monkeypatch.setattr(service, "analyze_workforce_esg", success("three"))
    monkeypatch.setattr(service, "analyze_company_brief", agent_4)

    with pytest.raises(RuntimeError, match="일부 작업이 실패"):
        service.run_company_brief_pipeline(tmp_path / "report.pdf")

    run_dirs = list((tmp_path / "runs").iterdir())
    assert len(run_dirs) == 1
    assert (run_dirs[0] / "01_business_strategy_result.json").exists()
    assert not (run_dirs[0] / "02_finance_management_result.json").exists()
    assert (run_dirs[0] / "03_workforce_esg_result.json").exists()
    assert agent_4_called is False
