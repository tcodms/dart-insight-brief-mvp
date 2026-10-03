"""Agent 4: Job Seeker Company Brief."""

from agent_client import AgentClient, ProgressCallback
from config import COMPANY_BRIEF_AGENT_ID, COMPANY_BRIEF_CONFIG_ID


def analyze_company_brief(file_id: str, *, progress: ProgressCallback | None = None) -> dict:
    return AgentClient(
        COMPANY_BRIEF_AGENT_ID,
        COMPANY_BRIEF_CONFIG_ID,
    ).run(file_id, progress=progress)
