"""Upstage Files API helper."""

from __future__ import annotations

from pathlib import Path

from openai import OpenAI

from config import UPSTAGE_API_KEY


def upload_file(file_path: str | Path) -> str:
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"업로드할 파일이 없습니다: {path}")
    if not UPSTAGE_API_KEY:
        raise ValueError("UPSTAGE_API_KEY가 설정되지 않았습니다.")

    client = OpenAI(api_key=UPSTAGE_API_KEY, base_url="https://api.upstage.ai/v2")
    with path.open("rb") as file_obj:
        uploaded = client.files.create(file=file_obj, purpose="user_data")
    return uploaded.id
