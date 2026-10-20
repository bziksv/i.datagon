from datetime import UTC, datetime, timedelta

from app.ops.candle_refresh import schedule_view, write_stamp


def test_schedule_view_shows_manual_when_interval_zero(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("CANDLE_FULL_REFRESH_INTERVAL_SEC", "0")
    monkeypatch.setenv("CANDLE_REFRESH_BEAT_PATH", str(tmp_path / "beat"))
    got = schedule_view()
    assert got["enabled"] is False
    assert got["interval_sec"] == 0
    assert got["m10"] == "manual"
    assert got["daily"] == "manual"


def test_schedule_view_shows_period_and_last_run(monkeypatch, tmp_path) -> None:
    beat = tmp_path / "beat"
    monkeypatch.setenv("CANDLE_FULL_REFRESH_INTERVAL_SEC", "3600")
    monkeypatch.setenv("CANDLE_REFRESH_BEAT_PATH", str(beat))
    monkeypatch.setenv("PAPER_FORWARD_TICKERS", "SBER,GAZP")
    now = datetime(2026, 10, 20, 12, 0, tzinfo=UTC)
    write_stamp(now - timedelta(minutes=20), path=beat)
    got = schedule_view(now=now)
    assert got["enabled"] is True
    assert got["interval_sec"] == 3600
    assert got["daily"] == "all"
    assert got["m15"] == "all"
    assert got["m10"] == "all"
    assert got["paper_tickers"] == ["SBER", "GAZP"]
    assert got["last_at"]
    assert got["next_at"]
