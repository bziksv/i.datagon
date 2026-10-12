from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.broker.port import CandleBar
from app.strategy.backtest import BacktestConfig, run_backtest
from app.strategy.base import BarContext
from app.strategy.morning import MorningBounceStrategy


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


def _loose(**overrides) -> MorningBounceStrategy:
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
    return MorningBounceStrategy(**params)


def test_morning_signals_buy_after_weak_day() -> None:
    sleeve = _loose()
    bars = [
        _bar(0, o=100, h=101, low=99, c=101),
        _bar(1, o=101, h=101, low=97, c=97),
    ]
    signal = sleeve.on_bar(BarContext("SBER", bars))
    assert signal is not None
    assert signal.kind == "buy"
    assert sleeve.fill_at == "morning"


def test_morning_evening_exit_when_in_position() -> None:
    sleeve = _loose()
    bars = [
        _bar(0, o=100, h=101, low=99, c=101),
        _bar(1, o=101, h=101, low=97, c=97),
        _bar(2, o=97, h=99, low=96, c=98),
    ]
    sleeve.on_bar(BarContext("SBER", bars[:2]))
    signal = sleeve.on_bar(
        BarContext("SBER", bars, entry_price=Decimal("97"))
    )
    assert signal is not None
    assert signal.kind == "exit"


def test_morning_backtest_buy_open_sell_close() -> None:
    sleeve = _loose(take_profit_pct=Decimal("0.50"))
    bars = [
        _bar(0, o=100, h=101, low=99, c=101),  # setup
        _bar(1, o=101, h=101, low=97, c=97),  # signal buy next open
        _bar(2, o=96, h=98, low=95, c=97),  # buy open 96, sell close 97
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
    assert report["trades"]
    trade = report["trades"][0]
    assert trade["exit_reason"] == "signal:exit"
    buys = [fill for fill in report["fills"] if fill["side"] == "buy"]
    sells = [fill for fill in report["fills"] if fill["side"] == "sell"]
    assert len(buys) == 1
    assert len(sells) == 1
    assert buys[0]["price"] == 96.0
    assert sells[0]["price"] == 97.0


def test_morning_averages_next_open_when_red_close() -> None:
    sleeve = _loose(
        average_trigger_pct=Decimal("0.02"),
        max_layers=2,
        take_profit_pct=Decimal("0.50"),
        max_hold_bars=3,
    )
    bars = [
        _bar(0, o=100, h=101, low=99, c=101),
        _bar(1, o=101, h=101, low=97, c=97),  # signal
        _bar(2, o=100, h=100, low=96, c=96),  # buy 100, red close → average signal
        _bar(3, o=95, h=96, low=94, c=95),  # add 95, then time/exit
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
    buys = [fill for fill in report["fills"] if fill["side"] == "buy"]
    assert len(buys) >= 2
