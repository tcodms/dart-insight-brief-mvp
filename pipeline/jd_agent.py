"""Analyze a JD PDF already uploaded to Upstage Files API."""

from pipeline.agent_client import AgentClient, ProgressCallback
from pipeline.config import CANDIDATE_UPSTAGE_API_KEY, JD_AGENT_ID, JD_CONFIG_ID


def analyze_jd(file_id: str, *, progress: ProgressCallback | None = None) -> dict:
    return AgentClient(
        JD_AGENT_ID, JD_CONFIG_ID, api_key=CANDIDATE_UPSTAGE_API_KEY
    ).run(file_id, progress=progress)
