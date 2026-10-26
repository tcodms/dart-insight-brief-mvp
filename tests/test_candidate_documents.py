from pathlib import Path
from types import SimpleNamespace

import pytest

import config


def test_shared_clients_keep_company_key_by_default(tmp_path, monkeypatch):
    import agent_client
    import upload

    pdf = tmp_path / "report.pdf"
    pdf.write_bytes(b"%PDF-1.4\ntest")
    keys = []

    class FakeOpenAI:
        def __init__(self, *, api_key, base_url):
            keys.append(api_key)
            self.files = SimpleNamespace(create=lambda **kwargs: SimpleNamespace(id="file-test"))

    monkeypatch.setattr(upload, "UPSTAGE_API_KEY", "company-key")
    monkeypatch.setattr(agent_client, "UPSTAGE_API_KEY", "company-key")
    monkeypatch.setattr(upload, "OpenAI", FakeOpenAI)
    monkeypatch.setattr(agent_client, "OpenAI", FakeOpenAI)

    assert upload.upload_file(pdf) == "file-test"
    agent_client.AgentClient("company-agent", "company-config")

    assert keys == ["company-key", "company-key"]


def test_candidate_config_only_requires_selected_agents(monkeypatch):
    monkeypatch.setattr(config, "UPSTAGE_API_KEY", "")
    monkeypatch.setattr(config, "CANDIDATE_UPSTAGE_API_KEY", "candidate-key", raising=False)
    monkeypatch.setattr(config, "CV_AGENT_ID", "cv-agent")
    monkeypatch.setattr(config, "CV_CONFIG_ID", "cv-config")
    monkeypatch.setattr(config, "JD_AGENT_ID", "")
    monkeypatch.setattr(config, "JD_CONFIG_ID", "")

    config.validate_candidate_config(include_cv=True, include_jd=False)

    with pytest.raises(ValueError, match="JD_AGENT_ID"):
        config.validate_candidate_config(include_cv=True, include_jd=True)


def test_cv_and_jd_wrappers_pass_candidate_key(monkeypatch):
    import cv_agent
    import jd_agent

    calls = []

    class FakeAgentClient:
        def __init__(self, agent_id, config_id, **kwargs):
            calls.append((agent_id, config_id, kwargs))

        def run(self, file_id, **kwargs):
            return {"file_id": file_id}

    monkeypatch.setattr(cv_agent, "AgentClient", FakeAgentClient)
    monkeypatch.setattr(jd_agent, "AgentClient", FakeAgentClient)
    monkeypatch.setattr(cv_agent, "CANDIDATE_UPSTAGE_API_KEY", "candidate-key", raising=False)
    monkeypatch.setattr(jd_agent, "CANDIDATE_UPSTAGE_API_KEY", "candidate-key", raising=False)

    cv_agent.analyze_cv("cv-file")
    jd_agent.analyze_jd("jd-file")

    assert [call[2]["api_key"] for call in calls] == ["candidate-key", "candidate-key"]


def test_cv_and_jd_pdfs_are_uploaded_and_saved_separately(tmp_path, monkeypatch):
    import candidate_document_service as service

    cv_pdf = tmp_path / "cv.pdf"
    jd_pdf = tmp_path / "jd.pdf"
    cv_pdf.write_bytes(b"%PDF-1.4\ncv")
    jd_pdf.write_bytes(b"%PDF-1.4\njd")
    uploaded = []

    monkeypatch.setattr(service, "CANDIDATE_RUNS_DIR", tmp_path / "runs")
    monkeypatch.setattr(service, "validate_candidate_config", lambda **kwargs: None)
    monkeypatch.setattr(service, "CANDIDATE_UPSTAGE_API_KEY", "candidate-key", raising=False)
    monkeypatch.setattr(service, "upload_file", lambda path, *, api_key: uploaded.append((Path(path), api_key)) or Path(path).stem)
    monkeypatch.setattr(service, "analyze_cv", lambda file_id, **kwargs: {"candidate": file_id})
    monkeypatch.setattr(service, "analyze_jd", lambda file_id, **kwargs: {"position": file_id})

    result = service.run_candidate_document_analysis(cv_pdf, jd_pdf)

    assert uploaded == [(cv_pdf, "candidate-key"), (jd_pdf, "candidate-key")]
    assert result["cv"] == {"candidate": "cv"}
    assert result["jd"] == {"position": "jd"}
    assert Path(result["paths"]["cv_json"]).read_text(encoding="utf-8").find('"candidate": "cv"') != -1
    assert Path(result["paths"]["jd_json"]).read_text(encoding="utf-8").find('"position": "jd"') != -1
    assert Path(result["paths"]["cv_json"]).parent == Path(result["paths"]["jd_json"]).parent


def test_missing_input_fails_before_agent_call(tmp_path, monkeypatch):
    import candidate_document_service as service

    monkeypatch.setattr(service, "upload_file", lambda *args, **kwargs: pytest.fail("should not upload"))

    with pytest.raises(FileNotFoundError):
        service.run_candidate_document_analysis(cv_path=tmp_path / "missing.pdf")
