from pathlib import Path

import pytest

import config


def test_candidate_config_only_requires_selected_agents(monkeypatch):
    monkeypatch.setattr(config, "UPSTAGE_API_KEY", "test-key")
    monkeypatch.setattr(config, "CV_AGENT_ID", "cv-agent")
    monkeypatch.setattr(config, "CV_CONFIG_ID", "cv-config")
    monkeypatch.setattr(config, "JD_AGENT_ID", "")
    monkeypatch.setattr(config, "JD_CONFIG_ID", "")

    config.validate_candidate_config(include_cv=True, include_jd=False)

    with pytest.raises(ValueError, match="JD_AGENT_ID"):
        config.validate_candidate_config(include_cv=True, include_jd=True)


def test_cv_and_jd_pdfs_are_uploaded_and_saved_separately(tmp_path, monkeypatch):
    import candidate_document_service as service

    cv_pdf = tmp_path / "cv.pdf"
    jd_pdf = tmp_path / "jd.pdf"
    cv_pdf.write_bytes(b"%PDF-1.4\ncv")
    jd_pdf.write_bytes(b"%PDF-1.4\njd")
    uploaded = []

    monkeypatch.setattr(service, "CANDIDATE_RUNS_DIR", tmp_path / "runs")
    monkeypatch.setattr(service, "validate_candidate_config", lambda **kwargs: None)
    monkeypatch.setattr(service, "upload_file", lambda path: uploaded.append(Path(path)) or Path(path).stem)
    monkeypatch.setattr(service, "analyze_cv", lambda file_id, **kwargs: {"candidate": file_id})
    monkeypatch.setattr(service, "analyze_jd", lambda file_id, **kwargs: {"position": file_id})

    result = service.run_candidate_document_analysis(cv_pdf, jd_pdf)

    assert uploaded == [cv_pdf, jd_pdf]
    assert result["cv"] == {"candidate": "cv"}
    assert result["jd"] == {"position": "jd"}
    assert Path(result["paths"]["cv_json"]).read_text(encoding="utf-8").find('"candidate": "cv"') != -1
    assert Path(result["paths"]["jd_json"]).read_text(encoding="utf-8").find('"position": "jd"') != -1
    assert Path(result["paths"]["cv_json"]).parent == Path(result["paths"]["jd_json"]).parent


def test_missing_input_fails_before_agent_call(tmp_path, monkeypatch):
    import candidate_document_service as service

    monkeypatch.setattr(service, "upload_file", lambda path: pytest.fail("should not upload"))

    with pytest.raises(FileNotFoundError):
        service.run_candidate_document_analysis(cv_path=tmp_path / "missing.pdf")
