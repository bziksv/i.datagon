from collections.abc import AsyncIterator
from datetime import UTC, datetime

from app.db import get_db
from app.main import create_app
from app.ops.ready import write_beat
from fastapi.testclient import TestClient


class _StatusSession:
    async def scalar(self, _stmt) -> int:
        return 2

    async def execute(self, _stmt) -> None:
        return None

    async def scalars(self, stmt):
        class _Result:
            def __iter__(self_inner):
                return iter([])

        return _Result()


async def _db() -> AsyncIterator[_StatusSession]:
    yield _StatusSession()


def test_status_endpoint_for_cabin(monkeypatch, tmp_path) -> None:
    beat = datetime(2026, 10, 12, 6, 0, tzinfo=UTC)
    path = tmp_path / "worker.beat"
    write_beat(beat, path)
    monkeypatch.setenv("WORKER_BEAT_PATH", str(path))
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://x")
    monkeypatch.setenv("APP_AUTH_TOKEN", "secret")
    monkeypatch.setenv("AGENTS_ENABLED", "0")
    app = create_app()
    app.dependency_overrides[get_db] = _db
    client = TestClient(app)
    assert client.get("/status").status_code == 401
    response = client.get("/status", headers={"X-App-Token": "secret"})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["orders"] == 2
    assert body["killed"] is False
    assert body["agents_enabled"] is False
    assert "portfolio" in body
    assert "vault" in body
    assert body["worker_beat"] == beat.isoformat()
