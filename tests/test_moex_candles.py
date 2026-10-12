from datetime import UTC, date, datetime
from decimal import Decimal

from app.broker.moex_candles import fetch_moex_candles, write_candle_csv
from app.strategy.backtest import load_bars


def test_fetch_moex_candles_paginates_and_converts_moscow_time() -> None:
    urls = []

    def request(url: str) -> dict:
        urls.append(url)
        if "start=0" in url:
            return {
                "candles": {
                    "columns": [
                        "open",
                        "close",
                        "high",
                        "low",
                        "volume",
                        "begin",
                    ],
                    "data": [
                        [100, 103, 105, 99, 12345, "2026-10-12 10:00:00"],
                    ],
                }
            }
        return {"candles": {"columns": [], "data": []}}

    bars = fetch_moex_candles(
        "sber",
        from_day=date(2026, 10, 1),
        till_day=date(2026, 10, 12),
        request_json=request,
    )
    assert len(bars) == 1
    assert bars[0].ts == datetime(2026, 10, 12, 7, tzinfo=UTC)
    assert bars[0].c == Decimal("103")
    assert len(urls) == 2
    assert "SBER" in urls[0]
    assert "start=1" in urls[1]


def test_write_moex_csv_is_compatible_with_backtest_loader(tmp_path) -> None:
    bars = fetch_moex_candles(
        "SBER",
        from_day=date(2026, 10, 12),
        till_day=date(2026, 10, 12),
        request_json=lambda _: {
            "candles": {
                "columns": [
                    "open",
                    "close",
                    "high",
                    "low",
                    "volume",
                    "begin",
                ],
                "data": [[100, 103, 105, 99, 12345, "2026-10-12 10:00:00"]],
            }
        },
    )
    path = write_candle_csv(tmp_path / "SBER.csv", bars)
    loaded = load_bars(path)
    assert loaded == bars
