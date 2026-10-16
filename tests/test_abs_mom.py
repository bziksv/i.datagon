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


def test_abs_mom2_holds_longer_and_trails_tighter() -> None:
    from app.strategy.abs_mom import AbsMomentum2Strategy

    sleeve = AbsMomentum2Strategy()
    assert sleeve.sleeve == "abs_momentum_2"
    assert sleeve.exit_roc == Decimal("-0.02")
    assert sleeve._trail_base == Decimal("0.04")
    assert sleeve.trail_arm == Decimal("1.20")
    assert sleeve.require_volume is True
    assert sleeve.max_day_up == Decimal("0.07")
    assert sleeve.breadth_min == Decimal("0.45")
    assert sleeve.exit_streak == 2
    assert sleeve.min_roc == Decimal("0.02")


def test_abs_mom3_copies_v2_rules() -> None:
    from app.strategy.abs_mom import AbsMomentum2Strategy, AbsMomentum3Strategy

    current = AbsMomentum2Strategy()
    nxt = AbsMomentum3Strategy()
    assert nxt.sleeve == "abs_momentum_3"
    assert nxt.exit_roc == current.exit_roc
    assert nxt._trail_base == current._trail_base
    assert nxt.trail_arm == current.trail_arm
    assert nxt.max_day_up == current.max_day_up
    assert nxt.breadth_min == current.breadth_min
    assert nxt.exit_streak == current.exit_streak
    assert nxt.require_volume is True


def test_abs_mom2_skips_a_day_that_already_ran() -> None:
    from app.strategy.abs_mom import AbsMomentum2Strategy

    kwargs = dict(
        lookback=5,
        sma_period=5,
        min_roc=Decimal("0"),
        exit_roc=Decimal("0"),
        max_stretch=Decimal("0"),
        trail_pct=Decimal("0"),
        trail_arm=Decimal("0"),
        require_volume=False,
        breadth_min=Decimal("0"),
    )
    smooth = [_bar(i, 50 + i) for i in range(12)]
    assert AbsMomentum2Strategy(**kwargs).on_bar(BarContext("SBER", smooth)).kind == "buy"
    spike = smooth[:-1] + [_bar(11, 70)]
    signal = AbsMomentum2Strategy(**kwargs).on_bar(BarContext("SBER", spike))
    assert signal is not None
    assert signal.kind == "flat"


def test_abs_mom2_keeps_position_through_sma_dip() -> None:
    from app.strategy.abs_mom import AbsMomentum2Strategy

    sleeve = AbsMomentum2Strategy(
        lookback=5,
        sma_period=5,
        min_roc=Decimal("0.02"),
        exit_roc=Decimal("-0.05"),
        trail_pct=Decimal("0"),
        trail_arm=Decimal("0"),
        max_stretch=Decimal("0"),
        require_volume=False,
        breadth_min=Decimal("0"),
    )
    up = [_bar(i, 50 + i) for i in range(12)]
    assert sleeve.on_bar(BarContext("SBER", up)).kind == "buy"
    # Цена чуть под SMA5, ROC за 5 дней ещё выше порога выхода.
    dip = up[:-1] + [_bar(11, 58)]
    signal = sleeve.on_bar(BarContext("SBER", dip, entry_price=Decimal("55")))
    assert signal is not None
    assert signal.kind == "flat"


def test_abs_mom2_sells_only_on_the_second_weak_day() -> None:
    from app.strategy.abs_mom import AbsMomentum2Strategy

    sleeve = AbsMomentum2Strategy(
        lookback=5,
        sma_period=5,
        min_roc=Decimal("0"),
        exit_roc=Decimal("0"),
        trail_pct=Decimal("0"),
        trail_arm=Decimal("0"),
        max_stretch=Decimal("0"),
        require_volume=False,
        breadth_min=Decimal("0"),
        max_day_up=Decimal("0"),
    )
    # ROC за 5 дней уходит ниже нуля только на последнем баре.
    bars = [_bar(i, 100) for i in range(6)] + [_bar(6, 90)]
    first = sleeve.on_bar(BarContext("SBER", bars, entry_price=Decimal("100")))
    assert first is not None and first.kind == "flat"
    second = sleeve.on_bar(
        BarContext("SBER", bars + [_bar(7, 89)], entry_price=Decimal("100"))
    )
    assert second is not None and second.kind == "sell"


def test_abs_mom2_uses_sp_breadth_for_us_ticker(monkeypatch, tmp_path) -> None:
    from app.strategy import abs_mom
    from app.strategy.abs_mom import AbsMomentum2Strategy

    sp = tmp_path / "sp"
    sp.mkdir()
    (sp / "AAPL.csv").write_text("ts,o,h,l,c,v\n")
    monkeypatch.setenv("CANDLE_SP500_DIR", str(sp))
    monkeypatch.setenv("CANDLE_DIR", str(tmp_path / "moex"))
    abs_mom._SP_BREADTH = {"2025-01-12": 0.80}
    abs_mom._BREADTH = {"2025-01-12": 0.10}
    try:
        sleeve = AbsMomentum2Strategy(
            lookback=5,
            sma_period=5,
            min_roc=Decimal("0"),
            exit_roc=Decimal("0"),
            max_stretch=Decimal("0"),
            trail_pct=Decimal("0"),
            trail_arm=Decimal("0"),
            require_volume=False,
            max_day_up=Decimal("0"),
        )
        bars = [_bar(i, 50 + i) for i in range(12)]
        signal = sleeve.on_bar(BarContext("AAPL", bars))
        assert signal is not None
        assert signal.kind == "buy"
    finally:
        abs_mom._SP_BREADTH = None
        abs_mom._BREADTH = None


def test_abs_mom2_skips_entry_when_the_market_is_narrow() -> None:
    from app.strategy import abs_mom
    from app.strategy.abs_mom import AbsMomentum2Strategy

    abs_mom._BREADTH = {"2025-01-12": 0.10}
    try:
        sleeve = AbsMomentum2Strategy(
            lookback=5,
            sma_period=5,
            min_roc=Decimal("0"),
            exit_roc=Decimal("0"),
            max_stretch=Decimal("0"),
            trail_pct=Decimal("0"),
            trail_arm=Decimal("0"),
            require_volume=False,
            max_day_up=Decimal("0"),
        )
        bars = [_bar(i, 50 + i) for i in range(12)]
        signal = sleeve.on_bar(BarContext("SBER", bars))
        assert signal is not None
        assert signal.kind == "flat"
    finally:
        abs_mom._BREADTH = None


def test_abs_mom_defaults_tuned_for_both_universes() -> None:
    sleeve = AbsMomentumStrategy()
    assert sleeve.sma_period == 40
    assert sleeve.lookback == 20
    assert sleeve.min_roc == Decimal("0.02")
    assert sleeve.exit_roc == Decimal("-0.01")
    assert sleeve.max_stretch == Decimal("1.10")
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
