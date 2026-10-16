from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.broker.port import CandleBar
from app.strategy.backtest import BacktestConfig, run_backtest
from app.strategy.base import BarContext
from app.strategy.vol_scalp import VolScalpStrategy


def _bar(
    minute: int,
    *,
    o: float,
    h: float,
    low: float,
    c: float,
) -> CandleBar:
    return CandleBar(
        ts=datetime(2026, 1, 5, 10, 0, tzinfo=UTC) + timedelta(minutes=15 * minute),
        o=Decimal(str(o)),
        h=Decimal(str(h)),
        low=Decimal(str(low)),
        c=Decimal(str(c)),
        v=Decimal("1000"),
    )


def _volatile_setup() -> list[CandleBar]:
    """Спокойные бары → всплеск ATR, слабый бар, импульсный зелёный."""
    bars: list[CandleBar] = []
    price = 100.0
    for index in range(30):
        o = price
        c = price + (0.05 if index % 2 == 0 else -0.05)
        bars.append(
            _bar(index, o=o, h=max(o, c) + 0.08, low=min(o, c) - 0.08, c=c)
        )
        price = c
    for index in range(30, 40):
        o = price
        c = price - 0.4 if index % 2 == 0 else price + 0.4
        bars.append(
            _bar(index, o=o, h=max(o, c) + 0.8, low=min(o, c) - 0.8, c=c)
        )
        price = c
    o = price
    c = price - 0.7
    bars.append(_bar(40, o=o, h=o + 0.1, low=c - 0.3, c=c))
    price = c
    o = price
    c = price + 1.2
    bars.append(_bar(41, o=o, h=c + 0.05, low=o - 0.05, c=c))
    return bars


def _loose(**overrides) -> VolScalpStrategy:
    params = dict(
        min_atr_pct=Decimal("0.001"),
        atr_expand=Decimal("1.05"),
        atr_norm_bars=10,
        atr_period=8,
        soft_loss_pct=Decimal("0"),
        cooldown_bars=0,
        max_layers=6,
        max_hold_bars=0,
        max_layer_hold_bars=0,
        trend_bars=0,
        stop_pct=Decimal("0"),
        average_trigger_pct=Decimal("0.005"),
        take_profit_pct=Decimal("0.012"),
        session_start_utc=(0, 0),
        session_end_utc=(23, 59),
    )
    params.update(overrides)
    return VolScalpStrategy(**params)


def test_vol_scalp_buys_on_volatile_impulse() -> None:
    sleeve = _loose()
    bars = _volatile_setup()
    signal = sleeve.on_bar(BarContext("SBER", bars))
    assert signal is not None
    assert signal.kind == "buy"
    assert sleeve.max_layers == 6
    assert sleeve.stop_pct == Decimal("0")


def test_vol_scalp_skips_chase_when_pullback_required() -> None:
    sleeve = _loose(require_pullback=True)
    bars = _volatile_setup()
    prev = bars[-2]
    bars[-2] = _bar(
        40,
        o=float(prev.o),
        h=float(prev.o) + 1.0,
        low=float(prev.o) - 0.1,
        c=float(prev.o) + 0.8,
    )
    signal = sleeve.on_bar(BarContext("SBER", bars))
    assert signal is not None
    assert signal.kind == "flat"


def test_vol_scalp_skips_quiet_market() -> None:
    sleeve = _loose(min_atr_pct=Decimal("0.05"))
    bars = _volatile_setup()
    signal = sleeve.on_bar(BarContext("SBER", bars))
    assert signal is not None
    assert signal.kind == "flat"


def test_vol_scalp_hard_averages_on_drawdown() -> None:
    sleeve = _loose(
        average_trigger_pct=Decimal("0.005"),
        max_layers=6,
        take_profit_pct=Decimal("0.05"),
    )
    bars = _volatile_setup()
    assert sleeve.on_bar(BarContext("SBER", bars)).kind == "buy"
    entry = Decimal(bars[-1].c)
    # красный минус — всё равно докуп (жёсткое усреднение)
    dump = _bar(
        42,
        o=float(entry),
        h=float(entry),
        low=float(entry) * 0.99,
        c=float(entry) * 0.992,
    )
    signal = sleeve.on_bar(BarContext("SBER", bars + [dump], entry_price=entry))
    assert signal is not None
    assert signal.kind == "buy"
    assert sleeve._layers == 2


def test_vol_scalp_keeps_averaging_until_max_layers() -> None:
    sleeve = _loose(max_layers=4, average_trigger_pct=Decimal("0.005"))
    bars = _volatile_setup()
    assert sleeve.on_bar(BarContext("SBER", bars)).kind == "buy"
    entry = Decimal(bars[-1].c)
    history = bars
    price = float(entry)
    for offset in range(1, 6):
        price *= 0.992
        bar = _bar(
            41 + offset,
            o=price * 1.001,
            h=price * 1.002,
            low=price * 0.998,
            c=price,
        )
        history = history + [bar]
        signal = sleeve.on_bar(
            BarContext("SBER", history, entry_price=Decimal(str(price / 0.992)))
        )
        # entry_price в ctx должен быть «текущая средняя»; для теста
        # передаём цену чуть выше close, чтобы drawdown держался
        signal = sleeve.on_bar(
            BarContext("SBER", history, entry_price=Decimal(str(price * 1.01)))
        )
        if sleeve._layers >= 4:
            assert signal.kind == "flat"
            break
    assert sleeve._layers == 4


def test_vol_scalp_unlocks_at_breakeven_after_max_layers() -> None:
    sleeve = _loose(max_layers=2, take_profit_pct=Decimal("0.05"))
    bars = _volatile_setup()
    assert sleeve.on_bar(BarContext("SBER", bars)).kind == "buy"
    entry = Decimal(bars[-1].c)
    dump = _bar(
        42,
        o=float(entry),
        h=float(entry),
        low=float(entry) * 0.99,
        c=float(entry) * 0.992,
    )
    assert (
        sleeve.on_bar(BarContext("SBER", bars + [dump], entry_price=entry)).kind
        == "buy"
    )
    assert sleeve._layers == 2
    avg = entry  # ctx average for unlock check
    flat = _bar(
        43,
        o=float(avg),
        h=float(avg) * 1.001,
        low=float(avg) * 0.999,
        c=float(avg),
    )
    signal = sleeve.on_bar(
        BarContext("SBER", bars + [dump, flat], entry_price=avg)
    )
    assert signal is not None
    assert signal.kind == "exit"


def test_vol_scalp_no_time_exit_by_default() -> None:
    sleeve = _loose(
        max_hold_bars=0,
        max_layer_hold_bars=0,
        take_profit_pct=Decimal("0.05"),
    )
    bars = _volatile_setup()
    assert sleeve.on_bar(BarContext("SBER", bars)).kind == "buy"
    history = bars
    last = None
    for offset in range(1, 12):
        hold = _bar(41 + offset, o=110, h=111, low=109, c=110.5)
        history = history + [hold]
        last = sleeve.on_bar(
            BarContext("SBER", history, entry_price=Decimal("110"))
        )
    assert last is not None
    assert last.kind == "flat"


def test_vol_scalp_max_layer_timeout_exits() -> None:
    sleeve = _loose(max_layers=1, max_layer_hold_bars=3, take_profit_pct=Decimal("0.05"))
    bars = _volatile_setup()
    assert sleeve.on_bar(BarContext("SBER", bars)).kind == "buy"
    history = bars
    last = None
    for offset in range(1, 5):
        hold = _bar(41 + offset, o=110, h=111, low=109, c=109.5)
        history = history + [hold]
        last = sleeve.on_bar(
            BarContext("SBER", history, entry_price=Decimal("110"))
        )
    assert last is not None
    assert last.kind == "exit"


def test_vol_scalp_backtest_take_profit() -> None:
    sleeve = _loose(
        take_profit_pct=Decimal("0.01"),
        average_trigger_pct=Decimal("0.50"),
        max_layers=1,
        stop_pct=Decimal("0"),
        max_hold_bars=0,
    )
    bars = _volatile_setup()
    entry_close = float(bars[-1].c)
    bars.append(
        _bar(
            42,
            o=entry_close,
            h=entry_close * 1.02,
            low=entry_close * 0.995,
            c=entry_close * 1.015,
        )
    )
    result = run_backtest(
        sleeve,
        "SBER",
        bars,
        config=BacktestConfig(
            initial_cash=Decimal("100000"),
            position_share=Decimal("1"),
            lot=1,
            commission_bps=Decimal("0"),
            slippage_bps=Decimal("0"),
        ),
    )
    assert any(trade["exit_reason"] == "take_profit" for trade in result["trades"])
