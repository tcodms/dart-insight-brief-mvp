from __future__ import annotations

from types import SimpleNamespace

from agent_client import AgentClient


def test_progress_messages_do_not_expose_job_id(monkeypatch) -> None:
    client = AgentClient.__new__(AgentClient)
    client.max_wait_seconds = 10
    responses = iter(
        [
            SimpleNamespace(status="queued"),
            SimpleNamespace(status="completed"),
        ]
    )
    client.client = SimpleNamespace(
        responses=SimpleNamespace(retrieve=lambda *_args, **_kwargs: next(responses))
    )
    messages: list[str] = []

    client.wait_until_complete(
        "job_secret_identifier",
        interval_seconds=0,
        progress=messages.append,
    )

    assert messages == ["Agent 상태: queued", "Agent 상태: completed"]
    assert all("job_secret_identifier" not in message for message in messages)


def test_job_creation_progress_uses_generic_message(monkeypatch) -> None:
    client = AgentClient.__new__(AgentClient)
    monkeypatch.setattr(client, "create_job", lambda _file_id: "job_secret_identifier")
    monkeypatch.setattr(
        client,
        "wait_until_complete",
        lambda _job_id, *, progress=None: SimpleNamespace(output_text="{}"),
    )
    messages: list[str] = []

    assert client.run("file_id", progress=messages.append) == {}
    assert messages == ["Agent 작업 생성"]
