from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

from app.broker.moex_candles import (
    aggregate_candles,
    fetch_moex_candles,
    missing_session_ranges,
    write_candle_csv,
)
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


def test_minute_candles_aggregate_to_15m_ohlcv() -> None:
    bars = [
        load_bars(Path("tests/fixtures/sber_m15.csv"))[0],
        load_bars(Path("tests/fixtures/sber_m15.csv"))[1],
    ]
    start = datetime(2026, 10, 12, 7, 1, tzinfo=UTC)
    bars[0] = bars[0].__class__(
        ts=start,
        o=Decimal("100"),
        h=Decimal("103"),
        low=Decimal("99"),
        c=Decimal("102"),
        v=Decimal("10"),
    )
    bars[1] = bars[1].__class__(
        ts=start.replace(minute=14),
        o=Decimal("102"),
        h=Decimal("106"),
        low=Decimal("101"),
        c=Decimal("105"),
        v=Decimal("20"),
    )
    aggregated = aggregate_candles(bars, minutes=15)
    assert len(aggregated) == 1
    assert aggregated[0].ts == start.replace(minute=0)
    assert aggregated[0].o == Decimal("100")
    assert aggregated[0].h == Decimal("106")
    assert aggregated[0].low == Decimal("99")
    assert aggregated[0].c == Decimal("105")
    assert aggregated[0].v == Decimal("30")


def test_missing_session_ranges_groups_weekdays_through_the_weekend() -> None:
    days = [date(2026, 1, 5), date(2026, 1, 6)]
    assert missing_session_ranges(days, until=date(2026, 1, 12)) == [
        (date(2026, 1, 7), date(2026, 1, 12)),
    ]
    assert missing_session_ranges(
        [date(2026, 1, 5), date(2026, 1, 6), date(2026, 1, 9)],
        until=date(2026, 1, 9),
    ) == [(date(2026, 1, 7), date(2026, 1, 8))]
