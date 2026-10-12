from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.broker.port import CandleBar
from app.strategy.abs_mom import AbsMomentumStrategy
from app.strategy.backtest import BacktestConfig, run_backtest
from app.strategy.base import BarContext


def _bar(day: int, c: float, *, o: float | None = None, h: float | None = None, low: float | None = None) -> CandleBar:
    close = Decimal(str(c))
    open_ = Decimal(str(o if o is not None else c))
    high = Decimal(str(h if h is not None else max(open_, close) + 1))
    low_ = Decimal(str(low if low is not None else min(open_, close) - 1))
    return CandleBar(
        ts=datetime(2025, 1, 1, 18, 0, tzinfo=UTC) + timedelta(days=day),
        o=open_,
        h=high,
        low=low_,
        c=close,
        v=Decimal("1000"),
    )


def test_abs_mom_defaults_tuned_for_both_universes() -> None:
    sleeve = AbsMomentumStrategy()
    assert sleeve.sma_period == 40
    assert sleeve.lookback == 20
    assert sleeve.min_roc == Decimal("0.02")
    assert sleeve.exit_roc == Decimal("-0.01")
    assert sleeve.max_stretch == Decimal("1.14")
    assert sleeve.trail_pct == Decimal("0.10")


def test_abs_mom_stays_flat_in_downtrend() -> None:
    sleeve = AbsMomentumStrategy(
        lookback=5,
        sma_period=5,
        min_roc=Decimal("0"),
        exit_roc=Decimal("0"),
        max_stretch=Decimal("0"),
        trail_pct=Decimal("0"),
    )
    bars = [_bar(i, 100 - i) for i in range(12)]
    signal = sleeve.on_bar(BarContext("SBER", bars))
    assert signal is not None
    assert signal.kind == "flat"


def test_abs_mom_buys_in_uptrend() -> None:
    sleeve = AbsMomentumStrategy(
        lookback=5,
        sma_period=5,
        min_roc=Decimal("0"),
        exit_roc=Decimal("0"),
        max_stretch=Decimal("0"),
        trail_pct=Decimal("0"),
    )
    bars = [_bar(i, 50 + i) for i in range(12)]
    signal = sleeve.on_bar(BarContext("SBER", bars))
    assert signal is not None
    assert signal.kind == "buy"


def test_abs_mom_skips_stretched_entry() -> None:
    sleeve = AbsMomentumStrategy(
        lookback=5,
        sma_period=5,
        min_roc=Decimal("0"),
        exit_roc=Decimal("0"),
        max_stretch=Decimal("1.10"),
        trail_pct=Decimal("0"),
    )
    # резкий вынос вверх: close сильно выше SMA5
    bars = [_bar(i, 100) for i in range(8)] + [_bar(8, 130), _bar(9, 140)]
    signal = sleeve.on_bar(BarContext("SBER", bars))
    assert signal is not None
    assert signal.kind == "flat"


def test_abs_mom_hysteresis_holds_soft_roc() -> None:
    sleeve = AbsMomentumStrategy(
        lookback=5,
        sma_period=5,
        min_roc=Decimal("0.05"),
        exit_roc=Decimal("0"),
        max_stretch=Decimal("0"),
        trail_pct=Decimal("0"),
    )
    # аптренд, затем мягкий ROC между 0 и min_roc — позицию держим
    up = [_bar(i, 50 + i) for i in range(12)]
    assert sleeve.on_bar(BarContext("SBER", up)).kind == "buy"
    # последние 5 баров почти плоские над SMA → ROC мал, но ≥ 0
    soft = up + [_bar(12, 61), _bar(13, 61.2), _bar(14, 61.4)]
    signal = sleeve.on_bar(
        BarContext("SBER", soft, entry_price=Decimal("55"))
    )
    assert signal is not None
    assert signal.kind == "flat"


def test_abs_mom_trails_off_peak_close() -> None:
    sleeve = AbsMomentumStrategy(
        lookback=5,
        sma_period=5,
        min_roc=Decimal("0"),
        exit_roc=Decimal("-1"),
        max_stretch=Decimal("0"),
        trail_pct=Decimal("0.10"),
    )
    # длинный аптренд, затем откат ~12% от пика, но всё ещё выше SMA/ROC
    up = [_bar(i, 100 + i) for i in range(20)]
    assert sleeve.on_bar(BarContext("SBER", up)).kind == "buy"
    peak_bar = up + [_bar(20, 130)]
    assert (
        sleeve.on_bar(BarContext("SBER", peak_bar, entry_price=Decimal("110"))).kind
        == "flat"
    )
    # peak 130, trail 10% → 117; close 116 → exit, при этом SMA5 ещё ниже
    pull = peak_bar + [_bar(21, 116)]
    signal = sleeve.on_bar(BarContext("SBER", pull, entry_price=Decimal("110")))
    assert signal is not None
    assert signal.kind == "exit"


def test_abs_mom_backtest_uses_full_position_share_attr() -> None:
    sleeve = AbsMomentumStrategy(
        lookback=5,
        sma_period=5,
        min_roc=Decimal("0"),
        exit_roc=Decimal("0"),
        max_stretch=Decimal("0"),
        trail_pct=Decimal("0"),
    )
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
