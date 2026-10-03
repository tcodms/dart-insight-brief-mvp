"""Project configuration for the DART Insight Brief MVP."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY", "").strip()

BUSINESS_STRATEGY_AGENT_ID = os.getenv("BUSINESS_STRATEGY_AGENT_ID", "").strip()
BUSINESS_STRATEGY_CONFIG_ID = os.getenv("BUSINESS_STRATEGY_CONFIG_ID", "").strip()

FINANCE_MANAGEMENT_AGENT_ID = os.getenv("FINANCE_MANAGEMENT_AGENT_ID", "").strip()
FINANCE_MANAGEMENT_CONFIG_ID = os.getenv("FINANCE_MANAGEMENT_CONFIG_ID", "").strip()

WORKFORCE_ESG_AGENT_ID = os.getenv("WORKFORCE_ESG_AGENT_ID", "").strip()
WORKFORCE_ESG_CONFIG_ID = os.getenv("WORKFORCE_ESG_CONFIG_ID", "").strip()

COMPANY_BRIEF_AGENT_ID = os.getenv("COMPANY_BRIEF_AGENT_ID", "").strip()
COMPANY_BRIEF_CONFIG_ID = os.getenv("COMPANY_BRIEF_CONFIG_ID", "").strip()

DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
RESULT_DIR = BASE_DIR / "result"
RUNS_DIR = OUTPUT_DIR / "runs"

FONT_NAME = "NanumGothic"
FONT_PATH = BASE_DIR / "fonts" / "NanumGothic-Regular.ttf"

REQUIRED_ENV = {
    "UPSTAGE_API_KEY": UPSTAGE_API_KEY,
    "BUSINESS_STRATEGY_AGENT_ID": BUSINESS_STRATEGY_AGENT_ID,
    "BUSINESS_STRATEGY_CONFIG_ID": BUSINESS_STRATEGY_CONFIG_ID,
    "FINANCE_MANAGEMENT_AGENT_ID": FINANCE_MANAGEMENT_AGENT_ID,
    "FINANCE_MANAGEMENT_CONFIG_ID": FINANCE_MANAGEMENT_CONFIG_ID,
    "WORKFORCE_ESG_AGENT_ID": WORKFORCE_ESG_AGENT_ID,
    "WORKFORCE_ESG_CONFIG_ID": WORKFORCE_ESG_CONFIG_ID,
    "COMPANY_BRIEF_AGENT_ID": COMPANY_BRIEF_AGENT_ID,
    "COMPANY_BRIEF_CONFIG_ID": COMPANY_BRIEF_CONFIG_ID,
}


def create_directories() -> None:
    for path in (DATA_DIR, OUTPUT_DIR, RESULT_DIR, RUNS_DIR):
        path.mkdir(parents=True, exist_ok=True)


def missing_config() -> list[str]:
    return [name for name, value in REQUIRED_ENV.items() if not value]


def validate_config() -> None:
    missing = missing_config()
    if missing:
        joined = "\n".join(f"- {name}" for name in missing)
        raise ValueError(f"다음 환경변수를 .env에 설정하세요:\n{joined}")
    create_directories()


def print_config() -> None:
    print(f"Project Directory: {BASE_DIR}")
    print(f"Output Directory : {OUTPUT_DIR}")
    for name, value in REQUIRED_ENV.items():
        if name == "UPSTAGE_API_KEY":
            print(f"{name}: {'set' if value else 'missing'}")
        else:
            print(f"{name}: {value or 'missing'}")
