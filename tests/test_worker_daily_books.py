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


def test_empty_daily_close_is_not_silent():
    source = WORKER.read_text(encoding="utf-8")
    assert "daily close waiting" in source
    assert "alert_data(" in source
