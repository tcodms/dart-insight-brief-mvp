"""Small UTF-8 file helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def save_json(data: Any, file_path: str | Path) -> Path:
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def load_json(file_path: str | Path) -> Any:
    return json.loads(Path(file_path).read_text(encoding="utf-8"))


def save_text(text: str, file_path: str | Path) -> Path:
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path
