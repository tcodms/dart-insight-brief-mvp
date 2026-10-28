from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_health_distinguishes_preview_from_live_analysis():
    assert client.get("/api/health").json() == {
        "status": "ok", "service": "dart-insight", "mode": "service"
    }


def test_demo_references_resolve_and_missing_jd_stays_missing():
    response = client.get("/api/demo/workspace")
    assert response.status_code == 200
    workspace = response.json()
    assert workspace["dataType"] == "fictional_demo"
    material_ids = {item["id"] for item in workspace["materials"]}
    for company in workspace["companies"]:
        assert company["cvId"] in material_ids
        if company["jdId"]:
            assert company["jdId"] in material_ids
        else:
            assert company["requirements"] is None
        for evidence in company["evidence"]:
            assert 1 <= evidence["page"] <= company["pages"]


def test_google_login_is_not_simulated_and_private_mutation_is_unavailable():
    assert client.get("/api/auth/session").json()["authenticated"] is False
    assert client.post("/api/analyze").status_code == 404
    assert client.post("/api/uploads").status_code == 404
