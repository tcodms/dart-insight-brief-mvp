import json
from pathlib import Path
from types import SimpleNamespace

from pypdf import PdfReader


def test_contribution_pipeline_uses_extracted_results_and_company_facts(tmp_path, monkeypatch):
    import contribution_service as service

    merged_path = tmp_path / "merged_company_data.json"
    merged_path.write_text(
        json.dumps(
            {
                "company_name": "예시 회사",
                "report_type": "사업보고서",
                "facts": [
                    {
                        "id": "B01-001",
                        "category": "제품",
                        "statement": "미생물 품질관리 수행",
                        "source_batch": "business",
                        "evidence": {
                            "original_page": 12,
                            "section": "사업 내용",
                            "quote": "품질관리 근거 문장",
                        },
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    cv_path = tmp_path / "cv.pdf"
    jd_path = tmp_path / "jd.pdf"
    cv_path.write_bytes(b"%PDF-1.4")
    jd_path.write_bytes(b"%PDF-1.4")
    calls = []

    monkeypatch.setattr(service, "validate_candidate_config", lambda **kwargs: calls.append(kwargs))
    monkeypatch.setattr(
        service,
        "validate_contribution_config",
        lambda: {
            "CANDIDATE_UPSTAGE_API_KEY": "candidate-key",
            "CONTRIBUTION_AGENT_ID": "contribution-agent",
            "CONTRIBUTION_CONFIG_ID": "contribution-config",
        },
    )
    monkeypatch.setattr(
        service,
        "run_candidate_document_analysis",
        lambda cv, jd, **kwargs: {
            "run_dir": str(tmp_path / "run"),
            "cv": {"project_experiences": ["미생물 시험 수행"]},
            "jd": {"responsibilities": ["미생물 QC 업무"]},
            "paths": {"cv_json": "cv_result.json", "jd_json": "jd_result.json"},
        },
    )

    def fake_upload(path, *, api_key):
        assert api_key == "candidate-key"
        text = "\n".join(page.extract_text() for page in PdfReader(path).pages)
        for expected in (
            "[기업 fact 병합결과]", "B01-001", "품질관리 근거 문장",
            "[CV Agent 추출 결과]", "미생물 시험 수행",
            "[JD Agent 추출 결과]", "미생물 QC 업무",
        ):
            assert expected in text
        calls.append("uploaded")
        return "input-file"

    class FakeAgentClient:
        def __init__(self, agent_id, config_id, *, api_key, max_wait_seconds):
            assert (agent_id, config_id, api_key) == (
                "contribution-agent", "contribution-config", "candidate-key"
            )

        def create_job(self, file_id):
            assert file_id == "input-file"
            return "job-test"

        def wait_until_complete(self, job_id, *, progress):
            assert job_id == "job-test"
            return SimpleNamespace(output_text=json.dumps("# 개인 경험 연결\n근거【†3】 문장", ensure_ascii=False))

    monkeypatch.setattr(service, "upload_file", fake_upload)
    monkeypatch.setattr(service, "AgentClient", FakeAgentClient)

    result = service.run_contribution_pipeline(cv_path, jd_path, merged_path)

    assert calls == [{"include_cv": True, "include_jd": True}, "uploaded"]
    assert result["report"] == "# 개인 경험 연결\n근거 문장"
    assert Path(result["paths"]["report_markdown"]).read_text(encoding="utf-8") == result["report"]
    assert Path(result["paths"]["raw"]).read_text(encoding="utf-8").startswith('"# 개인')


def test_contribution_config_reads_updated_env_without_process_restart(tmp_path, monkeypatch):
    import config

    monkeypatch.setattr(config, "BASE_DIR", tmp_path)
    monkeypatch.setattr(config, "CONTRIBUTION_AGENT_ID", "")
    monkeypatch.setattr(config, "CONTRIBUTION_CONFIG_ID", "")
    (tmp_path / ".env").write_text(
        "CANDIDATE_UPSTAGE_API_KEY=candidate-key\n"
        "CONTRIBUTION_AGENT_ID=contribution-agent\n"
        "CONTRIBUTION_CONFIG_ID=contribution-config\n",
        encoding="utf-8",
    )

    assert config.validate_contribution_config() == {
        "CANDIDATE_UPSTAGE_API_KEY": "candidate-key",
        "CONTRIBUTION_AGENT_ID": "contribution-agent",
        "CONTRIBUTION_CONFIG_ID": "contribution-config",
    }
