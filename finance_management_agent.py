"""Agent 2: Finance & Management Extract."""

from agent_client import AgentClient, ProgressCallback
from config import FINANCE_MANAGEMENT_AGENT_ID, FINANCE_MANAGEMENT_CONFIG_ID


def analyze_finance_management(file_id: str, *, progress: ProgressCallback | None = None) -> dict:
    return AgentClient(
        FINANCE_MANAGEMENT_AGENT_ID,
        FINANCE_MANAGEMENT_CONFIG_ID,
    ).run(file_id, progress=progress)
