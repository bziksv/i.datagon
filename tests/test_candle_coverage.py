from pathlib import Path

from app.ops.candle_coverage import coverage_view


def test_coverage_view_reports_strategy_formats(tmp_path, monkeypatch) -> None:
    daily = tmp_path / "candles"
    m15 = tmp_path / "m15"
    daily.mkdir()
    m15.mkdir()
    (daily / "SBER.csv").write_text(
        "ts,o,h,l,c,v\n"
        + "\n".join(
            f"2026-01-{(i % 28) + 1:02d}T21:00:00+00:00,1,1,1,1,1" for i in range(320)
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("CANDLE_DIR", str(daily))
    monkeypatch.setenv("CANDLE_M15_DIR", str(m15))
    monkeypatch.setenv("CANDLE_M10_DIR", str(tmp_path / "m10"))

    day = coverage_view(tf="1d", tickers=["SBER", "HHRU"], names={"SBER": "Сбербанк"})
    assert day["tf"] == "1d"
    assert day["formats"][0]["id"] == "1d"
    by_ticker = {row["ticker"]: row for row in day["items"]}
    assert by_ticker["HHRU"]["status"] == "missing"
    assert by_ticker["SBER"]["bars"] == 320

    m15_view = coverage_view(tf="15m", tickers=["SBER"], names={"SBER": "Сбербанк"})
    assert m15_view["tf"] == "15m"
    assert m15_view["items"][0]["status"] == "missing"
