from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from app.db import get_db
from app.main import create_app
from app.ops.ready import ready_view, write_beat


def test_ready_view_shows_orders_and_beat() -> None:
    now = datetime(2026, 10, 12, 4, 0, tzinfo=UTC)
    beat = now - timedelta(minutes=5)
    got = ready_view(3, beat, now)
    assert got["status"] == "ok"
    assert got["orders"] == 3
    assert got["worker_beat"] == beat.isoformat()
    assert got["worker_alive"] is True
    stale = ready_view(0, now - timedelta(hours=4), now)
    assert stale["worker_alive"] is False


class _CountSession:
    async def scalar(self, _stmt) -> int:
        return 4

    async def execute(self, _stmt) -> None:
        return None


async def _db() -> AsyncIterator[_CountSession]:
    yield _CountSession()


def test_write_beat_skips_unwritable_path(tmp_path) -> None:
    parent = tmp_path / "not-a-dir"
    parent.write_text("x")
    blocked = parent / "worker.beat"
    write_beat(datetime(2026, 10, 12, 4, 0, tzinfo=UTC), blocked)
    assert not blocked.exists()


def test_ready_endpoint_exposes_metrics(monkeypatch, tmp_path) -> None:
    beat = datetime(2026, 10, 12, 4, 20, tzinfo=UTC)
    path = tmp_path / "worker.beat"
    write_beat(beat, path)
    monkeypatch.setenv("WORKER_BEAT_PATH", str(path))
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://x")
    app = create_app()
    app.dependency_overrides[get_db] = _db
    client = TestClient(app)
    response = client.get("/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["orders"] == 4
    assert body["worker_beat"] == beat.isoformat()
    assert "worker_alive" in body
