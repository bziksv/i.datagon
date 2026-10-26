from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from app.broker.moex_candles import write_candle_csv
from app.broker.port import CandleBar
from app.ops.candle_refresh import interval_sec
from app.ops.refresh_candles import refresh_tail
from app.strategy.backtest import load_bars
from worker.bars import books_for_day, close_moment


def _day_bar(day: date, close: str) -> CandleBar:
    # дневной бар MOEX: полночь МСК = 21:00 UTC предыдущего дня
    ts = datetime(day.year, day.month, day.day, tzinfo=UTC) - timedelta(hours=3)
    price = Decimal(close)
    return CandleBar(ts=ts, o=price, h=price, low=price, c=price, v=Decimal("1"))


def _history(last: date, count: int = 45) -> list[CandleBar]:
    return [_day_bar(last - timedelta(days=count - 1 - i), "90") for i in range(count - 2)] + [
        _day_bar(last - timedelta(days=1), "100"),
        _day_bar(last, "101"),
    ]


def test_tail_merges_and_overwrites_last_day(tmp_path) -> None:
    root = tmp_path
    write_candle_csv(root / "SBER.csv", _history(date(2026, 10, 20)))
    calls = []

    def fetch(symbol, tf, from_day, till_day):
        calls.append((symbol, tf, from_day, till_day))
        return [
            _day_bar(date(2026, 10, 20), "102"),
            _day_bar(date(2026, 10, 21), "103"),
        ]

    refresh_tail(
        "sber",
        tf="1d",
        root=root,
        depth_days=730,
        today=date(2026, 10, 21),
        fetch=fetch,
    )
    bars = load_bars(root / "SBER.csv")
    assert len(bars) == 46
    assert [str(bar.c) for bar in bars[-3:]] == ["100", "102", "103"]
    # тянем только хвост: от последнего дня в файле, а не 730 дней
    assert calls == [("SBER", "1d", date(2026, 10, 19), date(2026, 10, 21))]


def test_tail_refills_truncated_history(tmp_path) -> None:
    write_candle_csv(tmp_path / "GAZP.csv", _history(date(2026, 10, 23), count=4))
    calls = []

    def fetch(symbol, tf, from_day, till_day):
        calls.append(from_day)
        return _history(date(2026, 10, 26), count=60)

    refresh_tail(
        "GAZP", tf="1d", root=tmp_path, depth_days=730, today=date(2026, 10, 26), fetch=fetch
    )
    assert calls == [date(2026, 10, 26) - timedelta(days=730)]
    assert len(load_bars(tmp_path / "GAZP.csv")) == 60


def test_short_refresh_window_keeps_history(tmp_path, monkeypatch) -> None:
    from app.ops import refresh_candles

    write_candle_csv(tmp_path / "PLZL.csv", _history(date(2026, 10, 20), count=50))
    monkeypatch.setattr(
        refresh_candles,
        "_fetch",
        lambda symbol, tf, from_day, till_day: [_day_bar(date(2026, 10, 21), "105")],
    )
    refresh_candles.refresh(["PLZL"], days=5, tf="1d", root=tmp_path)
    bars = load_bars(tmp_path / "PLZL.csv")
    assert len(bars) == 51
    assert str(bars[-1].c) == "105"


def test_tail_keeps_one_daily_bar_per_day_across_sources(tmp_path) -> None:
    broker = _day_bar(date(2026, 10, 20), "101")
    broker = CandleBar(
        ts=datetime(2026, 10, 20, tzinfo=UTC),
        o=broker.o,
        h=broker.h,
        low=broker.low,
        c=broker.c,
        v=broker.v,
    )
    write_candle_csv(
        tmp_path / "SBER.csv", [_day_bar(date(2026, 10, 19), "100"), broker]
    )

    def fetch(symbol, tf, from_day, till_day):
        return [_day_bar(date(2026, 10, 20), "102")]

    refresh_tail(
        "SBER",
        tf="1d",
        root=tmp_path,
        depth_days=730,
        today=date(2026, 10, 20),
        fetch=fetch,
    )
    assert [str(bar.c) for bar in load_bars(tmp_path / "SBER.csv")] == ["100", "102"]


def test_tail_without_file_pulls_full_depth(tmp_path) -> None:
    calls = []

    def fetch(symbol, tf, from_day, till_day):
        calls.append(from_day)
        return [_day_bar(date(2026, 10, 21), "1")]

    refresh_tail(
        "GAZP",
        tf="1d",
        root=tmp_path,
        depth_days=730,
        today=date(2026, 10, 21),
        fetch=fetch,
    )
    assert calls == [date(2026, 10, 21) - timedelta(days=730)]


def test_books_for_day_drops_stale_and_cuts_future() -> None:
    day = date(2026, 10, 21)
    books = {
        "SBER": [_day_bar(date(2026, 10, 20), "1"), _day_bar(day, "2")],
        "GAZP": [_day_bar(date(2026, 10, 20), "1")],
        "LKOH": [_day_bar(day, "1"), _day_bar(date(2026, 10, 22), "2")],
    }
    fresh, stale = books_for_day(books, day)
    assert sorted(fresh) == ["LKOH", "SBER"]
    assert stale == ["GAZP"]
    assert [str(bar.c) for bar in fresh["LKOH"]] == ["1"]


def test_default_interval_is_fifteen_minutes(monkeypatch) -> None:
    monkeypatch.delenv("CANDLE_FULL_REFRESH_INTERVAL_SEC", raising=False)
    monkeypatch.delenv("CANDLE_REFRESH_INTERVAL_SEC", raising=False)
    assert interval_sec() == 900


def test_close_moment_is_1850_msk() -> None:
    assert close_moment(date(2026, 10, 21)) == datetime(
        2026, 10, 21, 15, 50, tzinfo=UTC
    )
