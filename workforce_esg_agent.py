"""Agent 3: Workforce, Organization & ESG Extract."""

from agent_client import AgentClient, ProgressCallback
from config import WORKFORCE_ESG_AGENT_ID, WORKFORCE_ESG_CONFIG_ID


def analyze_workforce_esg(file_id: str, *, progress: ProgressCallback | None = None) -> dict:
    return AgentClient(
        WORKFORCE_ESG_AGENT_ID,
        WORKFORCE_ESG_CONFIG_ID,
    ).run(file_id, progress=progress)
