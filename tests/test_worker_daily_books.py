from __future__ import annotations

from pathlib import Path

from app.ops.candle_coverage import candle_root

WORKER = Path(__file__).resolve().parents[1] / "worker" / "__main__.py"


def test_daily_books_default_to_candle_root_without_env(monkeypatch):
    monkeypatch.delenv("CANDLE_DIR", raising=False)
    assert candle_root("1d") == Path("data/candles")
    source = WORKER.read_text(encoding="utf-8")
    assert 'load_daily_books(candle_root("1d"))' in source
    assert 'load_daily_books(os.environ.get("CANDLE_DIR"))' not in source


def test_close_day_survives_restart(tmp_path, monkeypatch):
    from datetime import UTC, date, datetime

    from worker.bars import daily_close_due, read_close_day, write_close_day

    stamp = tmp_path / "logs" / "daily-close.day"
    monkeypatch.setenv("DAILY_CLOSE_STAMP", str(stamp))
    assert read_close_day() is None
    write_close_day(date(2026, 10, 21))
    assert read_close_day() == date(2026, 10, 21)
    midday = datetime(2026, 10, 22, 9, 0, tzinfo=UTC)
    assert not daily_close_due(read_close_day(), midday)
    assert daily_close_due(read_close_day(), datetime(2026, 10, 22, 16, 0, tzinfo=UTC))
    stamp.write_text("garbage")
    assert read_close_day() is None


def test_empty_daily_close_is_not_silent():
    source = WORKER.read_text(encoding="utf-8")
    assert "daily close waiting" in source
    assert "alert_data(" in source
