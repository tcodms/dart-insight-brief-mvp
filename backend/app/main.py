"""Read-only development API. Authentication and private analysis are not wired yet."""

from fastapi import FastAPI

from backend.app.demo_data import demo_workspace


app = FastAPI(title="DART Insight API", version="0.1.0")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "dart-insight", "mode": "ui-preview"}


@app.get("/api/demo/workspace")
def public_demo_workspace() -> dict:
    """Only fixed fictional fixtures are public; real documents are never loaded."""
    return demo_workspace()


@app.get("/api/auth/session")
def session() -> dict:
    return {"authenticated": False, "googleConfigured": False}
