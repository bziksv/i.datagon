from datetime import UTC, datetime, timedelta

from app.ops.fundamentals_refresh import schedule_view, write_stamp


def test_fundamentals_schedule_default_hourly(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("FUNDAMENTALS_INTERVAL_SEC", raising=False)
    monkeypatch.setenv("FUNDAMENTALS_REFRESH_BEAT_PATH", str(tmp_path / "beat"))
    got = schedule_view()
    assert got["enabled"] is True
    assert got["interval_sec"] == 3600


def test_fundamentals_schedule_shows_last_and_next(monkeypatch, tmp_path) -> None:
    beat = tmp_path / "beat"
    monkeypatch.setenv("FUNDAMENTALS_INTERVAL_SEC", "3600")
    monkeypatch.setenv("FUNDAMENTALS_REFRESH_BEAT_PATH", str(beat))
    now = datetime(2026, 10, 20, 16, 0, tzinfo=UTC)
    write_stamp(now - timedelta(minutes=20), path=beat)
    got = schedule_view(now=now)
    assert got["last_at"]
    assert got["next_at"]
