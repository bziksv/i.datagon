from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.broker.port import CandleBar
from app.strategy.backtest import BacktestConfig, run_backtest
from app.strategy.base import BarContext
from app.strategy.overnight import OvernightBounceStrategy


def _bar(
    day: int,
    *,
    o: float,
    h: float,
    low: float,
    c: float,
) -> CandleBar:
    return CandleBar(
        ts=datetime(2026, 1, 1, 18, 0, tzinfo=UTC) + timedelta(days=day),
        o=Decimal(str(o)),
        h=Decimal(str(h)),
        low=Decimal(str(low)),
        c=Decimal(str(c)),
        v=Decimal("1000"),
    )


def _loose(**overrides) -> OvernightBounceStrategy:
    params = dict(
        take_profit_pct=Decimal("0.03"),
        average_trigger_pct=Decimal("0.20"),
        max_layers=1,
        stop_pct=Decimal("0.50"),
        max_hold_bars=5,
        cooldown_bars=0,
        min_day_drop_pct=Decimal("0"),
        rsi_max=Decimal("100"),
        close_range_max=Decimal("1"),
        sma_period=2,
    )
    params.update(overrides)
    return OvernightBounceStrategy(**params)


def _downtrend_then_setup() -> list[CandleBar]:
    bars: list[CandleBar] = []
    price = 120.0
    for day in range(16):
        o = price
        c = price - 1.2
        bars.append(_bar(day, o=o, h=o + 0.3, low=c - 0.2, c=c))
        price = c
    bars.append(_bar(16, o=price, h=price + 2.5, low=price - 0.2, c=price + 2.0))
    price = price + 2.0
    o = price
    c = price * 0.98
    bars.append(_bar(17, o=o, h=o + 0.1, low=c - 0.05, c=c))
    return bars


def test_overnight_skips_green_day() -> None:
    sleeve = OvernightBounceStrategy()
    bars = _downtrend_then_setup()
    last = bars[-1]
    bars[-1] = _bar(
        17,
        o=float(last.o),
        h=float(last.o) + 3,
        low=float(last.o) - 0.1,
        c=float(last.o) + 2,
    )
    signal = sleeve.on_bar(BarContext("SBER", bars))
    assert signal is not None
    assert signal.kind == "flat"


def test_overnight_buys_filtered_weak_setup() -> None:
    sleeve = OvernightBounceStrategy()
    bars = _downtrend_then_setup()
    signal = sleeve.on_bar(BarContext("SBER", bars))
    assert signal is not None
    assert signal.kind == "buy"
    assert sleeve.stop_from_first is True
    assert sleeve.fill_at == "close"


def test_overnight_time_exit_on_second_bar() -> None:
    sleeve = _loose(max_hold_bars=2, take_profit_pct=Decimal("0.50"))
    bars = [
        _bar(0, o=100, h=101, low=99, c=101),  # green
        _bar(1, o=101, h=101, low=97, c=97),  # entry
        _bar(2, o=97, h=98, low=96, c=97),  # hold=2 → exit
    ]
    assert sleeve.on_bar(BarContext("SBER", bars[:2])).kind == "buy"
    signal = sleeve.on_bar(
        BarContext("SBER", bars, entry_price=Decimal("97"))
    )
    assert signal is not None
    assert signal.kind == "exit"


def test_overnight_backtest_no_same_day_reentry_after_tp() -> None:
    sleeve = _loose()
    bars = [
        _bar(0, o=100, h=101, low=99, c=101),  # green
        _bar(1, o=101, h=101, low=97, c=97),  # buy
        _bar(2, o=97, h=102, low=97, c=101),  # TP, green evening
        _bar(3, o=101, h=103, low=101, c=102),
    ]
    report = run_backtest(
        sleeve,
        "SBER",
        bars,
        config=BacktestConfig(
            initial_cash=Decimal("100000"),
            position_share=Decimal("0.30"),
            commission_bps=Decimal("0"),
            slippage_bps=Decimal("0"),
        ),
        evaluation_start=0,
    )
    assert [trade["exit_reason"] for trade in report["trades"]] == ["take_profit"]
    buys = [fill for fill in report["fills"] if fill["side"] == "buy"]
    assert len(buys) == 1


def test_overnight_backtest_stop_from_first_entry() -> None:
    sleeve = _loose(
        take_profit_pct=Decimal("0.50"),
        average_trigger_pct=Decimal("0.02"),
        max_layers=2,
        stop_pct=Decimal("0.05"),
        max_hold_bars=20,
        cooldown_bars=1,
    )
    bars = [
        _bar(0, o=100, h=101, low=99, c=101),
        _bar(1, o=101, h=101, low=97, c=97),
        _bar(2, o=97, h=97, low=94, c=94),
        _bar(3, o=94, h=94, low=90, c=91),
    ]
    report = run_backtest(
        sleeve,
        "SBER",
        bars,
        config=BacktestConfig(
            initial_cash=Decimal("100000"),
            position_share=Decimal("0.30"),
            commission_bps=Decimal("0"),
            slippage_bps=Decimal("0"),
        ),
        evaluation_start=0,
    )
    assert any(trade["exit_reason"] == "stop" for trade in report["trades"])
