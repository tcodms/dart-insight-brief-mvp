"""Analyze a CV PDF already uploaded to Upstage Files API."""

from agent_client import AgentClient, ProgressCallback
from config import CV_AGENT_ID, CV_CONFIG_ID


def analyze_cv(file_id: str, *, progress: ProgressCallback | None = None) -> dict:
    return AgentClient(CV_AGENT_ID, CV_CONFIG_ID).run(file_id, progress=progress)
