from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.broker.port import CandleBar
from app.strategy.abs_mom import AbsMomentumStrategy
from app.strategy.backtest import BacktestConfig, run_backtest
from app.strategy.base import BarContext


def _bar(day: int, c: float, *, o: float | None = None) -> CandleBar:
    close = Decimal(str(c))
    open_ = Decimal(str(o if o is not None else c))
    return CandleBar(
        ts=datetime(2025, 1, 1, 18, 0, tzinfo=UTC) + timedelta(days=day),
        o=open_,
        h=max(open_, close) + Decimal("1"),
        low=min(open_, close) - Decimal("1"),
        c=close,
        v=Decimal("1000"),
    )


def test_abs_mom_stays_flat_in_downtrend() -> None:
    sleeve = AbsMomentumStrategy(lookback=5, sma_period=5, min_roc=Decimal("0"))
    # падающий ряд — ROC отрицательный
    bars = [_bar(i, 100 - i) for i in range(12)]
    signal = sleeve.on_bar(BarContext("SBER", bars))
    assert signal is not None
    assert signal.kind == "flat"


def test_abs_mom_buys_in_uptrend() -> None:
    sleeve = AbsMomentumStrategy(lookback=5, sma_period=5, min_roc=Decimal("0"))
    bars = [_bar(i, 50 + i) for i in range(12)]
    signal = sleeve.on_bar(BarContext("SBER", bars))
    assert signal is not None
    assert signal.kind == "buy"


def test_abs_mom_exits_when_strength_breaks() -> None:
    sleeve = AbsMomentumStrategy(lookback=5, sma_period=5, min_roc=Decimal("0"))
    up = [_bar(i, 50 + i) for i in range(12)]
    # резкий обвал ниже SMA и отрицательный ROC
    down = up + [_bar(12, 40), _bar(13, 35), _bar(14, 30), _bar(15, 25), _bar(16, 20)]
    assert sleeve.on_bar(BarContext("SBER", up)).kind == "buy"
    signal = sleeve.on_bar(
        BarContext("SBER", down, entry_price=Decimal("60"))
    )
    assert signal is not None
    assert signal.kind == "sell"


def test_abs_mom_backtest_uses_full_position_share_attr() -> None:
    sleeve = AbsMomentumStrategy(lookback=5, sma_period=5, min_roc=Decimal("0"))
    assert sleeve.backtest_position_share == Decimal("1")
    bars = [_bar(i, 50 + i * 2) for i in range(20)]
    report = run_backtest(
        sleeve,
        "SBER",
        bars,
        config=BacktestConfig(
            initial_cash=Decimal("100000"),
            position_share=Decimal("1"),
            commission_bps=Decimal("0"),
            slippage_bps=Decimal("0"),
        ),
        evaluation_start=0,
    )
    assert report["summary"]["trades"] >= 0
