"""Agent 2: Finance & Management Extract."""

from pipeline.agent_client import AgentClient, ProgressCallback
from pipeline.config import FINANCE_MANAGEMENT_AGENT_ID, FINANCE_MANAGEMENT_CONFIG_ID


def analyze_finance_management(file_id: str, *, progress: ProgressCallback | None = None) -> dict:
    return AgentClient(
        FINANCE_MANAGEMENT_AGENT_ID,
        FINANCE_MANAGEMENT_CONFIG_ID,
    ).run(file_id, progress=progress)
