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


def test_overnight_buys_when_flat() -> None:
    sleeve = OvernightBounceStrategy()
    bars = [_bar(0, o=100, h=101, low=99, c=100)]
    signal = sleeve.on_bar(BarContext("SBER", bars))
    assert signal is not None
    assert signal.kind == "buy"
    assert sleeve.fill_at == "close"
    assert sleeve.allow_add is True
    assert sleeve.take_profit_pct == Decimal("0.045")


def test_overnight_averages_on_drawdown() -> None:
    sleeve = OvernightBounceStrategy(
        average_trigger_pct=Decimal("0.02"),
        max_layers=3,
    )
    bars = [
        _bar(0, o=100, h=100, low=100, c=100),
        _bar(1, o=98, h=99, low=96, c=97),
    ]
    first = sleeve.on_bar(BarContext("SBER", bars[:1]))
    assert first is not None and first.kind == "buy"
    second = sleeve.on_bar(
        BarContext("SBER", bars, entry_price=Decimal("100"))
    )
    assert second is not None
    assert second.kind == "buy"


def test_overnight_backtest_take_profit_and_reeentry() -> None:
    sleeve = OvernightBounceStrategy(
        take_profit_pct=Decimal("0.05"),
        average_trigger_pct=Decimal("0.02"),
        max_layers=3,
        stop_pct=Decimal("0.20"),
    )
    bars = [
        _bar(0, o=100, h=100, low=100, c=100),  # buy close 100
        _bar(1, o=101, h=106, low=100, c=105),  # TP 105, then re-buy close 105
        _bar(2, o=105, h=106, low=104, c=105),
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
    reasons = [trade["exit_reason"] for trade in report["trades"]]
    assert "take_profit" in reasons
    buys = [fill for fill in report["fills"] if fill["side"] == "buy"]
    assert len(buys) >= 2


def test_overnight_backtest_averages_layers() -> None:
    sleeve = OvernightBounceStrategy(
        take_profit_pct=Decimal("0.50"),  # unreachable
        average_trigger_pct=Decimal("0.02"),
        max_layers=3,
        stop_pct=Decimal("0.50"),
    )
    bars = [
        _bar(0, o=100, h=100, low=100, c=100),
        _bar(1, o=98, h=99, low=96, c=97),
        _bar(2, o=96, h=97, low=94, c=95),
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
    assert len(buys) == 3
    assert report["summary"]["open_qty"] > 0
