"""Analyze a CV PDF already uploaded to Upstage Files API."""

from agent_client import AgentClient, ProgressCallback
from config import CANDIDATE_UPSTAGE_API_KEY, CV_AGENT_ID, CV_CONFIG_ID


def analyze_cv(file_id: str, *, progress: ProgressCallback | None = None) -> dict:
    return AgentClient(
        CV_AGENT_ID, CV_CONFIG_ID, api_key=CANDIDATE_UPSTAGE_API_KEY
    ).run(file_id, progress=progress)
