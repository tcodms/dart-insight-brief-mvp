"""Agent 1: Business & Strategy Extract."""

from agent_client import AgentClient, ProgressCallback
from config import BUSINESS_STRATEGY_AGENT_ID, BUSINESS_STRATEGY_CONFIG_ID


def analyze_business_strategy(file_id: str, *, progress: ProgressCallback | None = None) -> dict:
    return AgentClient(
        BUSINESS_STRATEGY_AGENT_ID,
        BUSINESS_STRATEGY_CONFIG_ID,
    ).run(file_id, progress=progress)
