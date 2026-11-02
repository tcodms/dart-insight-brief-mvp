"""Analyze a JD PDF already uploaded to Upstage Files API."""

from agent_client import AgentClient, ProgressCallback
from config import UPSTAGE_API_KEY, JD_AGENT_ID, JD_CONFIG_ID


def analyze_jd(file_id: str, *, progress: ProgressCallback | None = None) -> dict:
    return AgentClient(
        JD_AGENT_ID, JD_CONFIG_ID, api_key=UPSTAGE_API_KEY
    ).run(file_id, progress=progress)
