"""Shared Upstage Studio Agent client with bounded polling."""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from typing import Any

from openai import OpenAI

from config import UPSTAGE_API_KEY


ProgressCallback = Callable[[str], None]


class AgentClient:
    def __init__(self, agent_id: str, config_id: str, *, max_wait_seconds: int = 900):
        if not agent_id or not config_id:
            raise ValueError("Agent ID와 Config ID가 필요합니다.")
        if not UPSTAGE_API_KEY:
            raise ValueError("UPSTAGE_API_KEY가 설정되지 않았습니다.")

        self.agent_id = agent_id
        self.config_id = config_id
        self.max_wait_seconds = max_wait_seconds
        self.client = OpenAI(
            api_key=UPSTAGE_API_KEY,
            base_url="https://api.upstage.ai/v2",
        )

    def create_job(self, file_id: str) -> str:
        response = self.client.responses.create(
            model=self.agent_id,
            include=["last"],
            input=[
                {
                    "role": "user",
                    "content": [{"type": "input_file", "file_id": file_id}],
                }
            ],
            extra_body={"config_id": self.config_id},
        )
        return response.id

    def wait_until_complete(
        self,
        job_id: str,
        *,
        interval_seconds: int = 3,
        progress: ProgressCallback | None = None,
    ) -> Any:
        started = time.monotonic()
        last_status = None

        while True:
            response = self.client.responses.retrieve(job_id, include=["last"])
            status = response.status

            if status != last_status and progress:
                progress(f"Agent 상태: {status} (job={job_id})")
                last_status = status

            if status == "completed":
                return response
            if status == "failed":
                error = getattr(response, "error", None)
                raise RuntimeError(f"Studio Agent 실행 실패: {error or job_id}")
            if status not in {"queued", "in_progress"}:
                raise RuntimeError(f"알 수 없는 Agent 상태: {status}")

            if time.monotonic() - started >= self.max_wait_seconds:
                raise TimeoutError(
                    f"Agent가 {self.max_wait_seconds}초 안에 완료되지 않았습니다. job={job_id}"
                )
            time.sleep(interval_seconds)

    @staticmethod
    def parse_result(response: Any) -> dict:
        output_text = (getattr(response, "output_text", None) or "").strip()
        if not output_text:
            raise ValueError("Agent 응답에 output_text가 없습니다.")
        if output_text.startswith("```"):
            lines = output_text.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            output_text = "\n".join(lines).strip()
        try:
            result = json.loads(output_text)
        except json.JSONDecodeError as exc:
            raise ValueError("Agent output_text가 올바른 JSON이 아닙니다.") from exc
        if not isinstance(result, dict):
            raise ValueError("Agent 결과의 최상위 값은 JSON 객체여야 합니다.")
        return result

    def run(self, file_id: str, *, progress: ProgressCallback | None = None) -> dict:
        job_id = self.create_job(file_id)
        if progress:
            progress(f"Agent 작업 생성: {job_id}")
        response = self.wait_until_complete(job_id, progress=progress)
        return self.parse_result(response)
