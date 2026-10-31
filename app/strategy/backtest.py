"""Детерминированный paper-бэктест: next-bar execution, расходы и PnL."""

from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from datetime import datetime
from decimal import Decimal
from math import sqrt
from pathlib import Path
from statistics import fmean, pstdev

from app.broker.port import CandleBar
from app.strategy.base import BarContext, Signal, Strategy


def load_bars(path: Path) -> list[CandleBar]:
    lines = path.read_text().splitlines()
    bars: list[CandleBar] = []
    for line in lines[1:]:
        if not line.strip():
            continue
        ts, o, h, low, c, v = line.split(",")
        bars.append(
            CandleBar(
                ts=datetime.fromisoformat(ts),
                o=Decimal(o),
                h=Decimal(h),
                low=Decimal(low),
                c=Decimal(c),
                v=Decimal(v),
            )
        )
    return bars


class _BarPrefix:
    """Вид bars[:end] без копии списка на каждом баре."""

    __slots__ = ("_bars", "_end")

    def __init__(self, bars: Sequence[CandleBar], end: int) -> None:
        self._bars = bars
        self._end = end

    def __len__(self) -> int:
        return self._end

    def __iter__(self):
        bars = self._bars
        for index in range(self._end):
            yield bars[index]

    def __getitem__(self, item: int | slice):
        if isinstance(item, slice):
            start, stop, step = item.indices(self._end)
            return self._bars[start:stop:step]
        if not isinstance(item, int):
            raise TypeError(type(item))
        index = item + self._end if item < 0 else item
        if index < 0 or index >= self._end:
            raise IndexError(item)
        return self._bars[index]


def replay(
    strategy: Strategy,
    ticker: str,
    bars: Sequence[CandleBar],
) -> list[Signal]:
    signals: list[Signal] = []
    for end in range(1, len(bars) + 1):
        got = strategy.on_bar(BarContext(ticker, _BarPrefix(bars, end)))
        if got is not None:
            signals.append(got)
    return signals


@dataclass(frozen=True)
class BacktestConfig:
    initial_cash: Decimal = Decimal("1000000")
    position_share: Decimal = Decimal("0.10")
    commission_bps: Decimal = Decimal("5")
    slippage_bps: Decimal = Decimal("5")
    lot: int = 1
    periods_per_year: int = 252


@dataclass(frozen=True)
class BacktestFill:
    ts: datetime
    side: str
    qty: int
    price: Decimal
    commission: Decimal
    reason: str


@dataclass(frozen=True)
class BacktestTrade:
    entry_ts: datetime
    exit_ts: datetime
    qty: int
    entry_price: Decimal
    exit_price: Decimal
    gross_pnl: Decimal
    costs: Decimal
    net_pnl: Decimal
    exit_reason: str
    layers: int = 1
    added_qty: int = 0
    buy_notional: Decimal = Decimal("0")
    sell_notional: Decimal = Decimal("0")
    commission: Decimal = Decimal("0")
    carry: Decimal = Decimal("0")
    position_side: str = "long"


def _bps(value: Decimal) -> Decimal:
    return Decimal(value) / Decimal("10000")


def _execution_price(price: Decimal, side: str, slippage_bps: Decimal) -> Decimal:
    slip = _bps(slippage_bps)
    return Decimal(price) * (
        Decimal("1") + slip if side == "buy" else Decimal("1") - slip
    )


def _commission(notional: Decimal, commission_bps: Decimal) -> Decimal:
    return abs(Decimal(notional)) * _bps(commission_bps)


# Плата Т-Банка за перенос короткой позиции на ночь. Ступень — фикс за весь объём,
# выше последней ступени — доля от стоимости позиции в день.
DEFAULT_SHORT_CARRY_TIERS: tuple[tuple[Decimal, Decimal], ...] = (
    (Decimal("5000"), Decimal("0")),
    (Decimal("50000"), Decimal("40")),
    (Decimal("250000"), Decimal("190")),
    (Decimal("1000000"), Decimal("750")),
)
DEFAULT_SHORT_CARRY_RATE = Decimal("0.00075")


def short_carry_rub(
    notional: Decimal,
    tiers: Sequence[tuple[Decimal, Decimal]] | None = None,
    rate: Decimal | None = None,
) -> Decimal:
    """Плата за одну ночь по модулю стоимости короткой позиции."""
    size = abs(Decimal(notional))
    steps = tiers if tiers is not None else DEFAULT_SHORT_CARRY_TIERS
    for limit, fee in steps:
        if size <= Decimal(limit):
            return Decimal(fee)
    return size * (DEFAULT_SHORT_CARRY_RATE if rate is None else Decimal(rate))


def _max_drawdown(values: Sequence[Decimal]) -> Decimal:
    if not values:
        return Decimal("0")
    peak = values[0]
    worst = Decimal("0")
    for value in values:
        peak = max(peak, value)
        if peak > 0:
            worst = min(worst, (value - peak) / peak)
    return abs(worst)


def _returns(values: Sequence[Decimal]) -> list[float]:
    out: list[float] = []
    for previous, current in zip(values, values[1:], strict=False):
        if previous > 0:
            out.append(float(current / previous - Decimal("1")))
    return out


def _ratio(
    returns: Sequence[float],
    *,
    periods_per_year: int,
    downside_only: bool = False,
) -> float | None:
    if len(returns) < 2:
        return None
    sample = [min(value, 0.0) for value in returns] if downside_only else list(returns)
    volatility = pstdev(sample)
    if volatility == 0:
        return None
    return fmean(returns) / volatility * sqrt(periods_per_year)


def _money(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.01")))


def _number(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.000001")))


def run_backtest(
    strategy: Strategy,
    ticker: str,
    bars: Sequence[CandleBar],
    *,
    config: BacktestConfig | None = None,
    evaluation_start: int = 0,
) -> dict:
    """Long simulation; shorts only if the strategy sets allow_short.

    Decisions are made after bar close and executed no earlier than the next
    bar open. A fixed stop may execute intrabar; a gap through the stop fills
    at the worse opening price. A long-only strategy never enters the short
    branch, so its result stays the same.
    """
    cfg = config or BacktestConfig()
    if cfg.initial_cash <= 0:
        raise ValueError("initial_cash must be > 0")
    if not Decimal("0") < cfg.position_share <= Decimal("1"):
        raise ValueError("position_share must be in (0, 1]")
    if cfg.lot < 1:
        raise ValueError("lot must be >= 1")
    if not bars:
        raise ValueError("bars")
    if not 0 <= evaluation_start < len(bars):
        raise ValueError("evaluation_start must point inside bars")

    cash = Decimal(cfg.initial_cash)
    qty = 0
    entry_price: Decimal | None = None
    first_entry_price: Decimal | None = None
    entry_ts: datetime | None = None
    entry_cost = Decimal("0")
    buy_notional = Decimal("0")
    layers = 0
    added_qty = 0
    pending: str | None = None
    pending_reason = ""
    pending_add = False
    fills: list[BacktestFill] = []
    trades: list[BacktestTrade] = []
    equity_curve: list[dict] = []
    turnover = Decimal("0")
    exposed_bars = 0
    fill_at = str(getattr(strategy, "fill_at", "next_open") or "next_open")
    allow_add = bool(getattr(strategy, "allow_add", False))
    max_layers = max(int(getattr(strategy, "max_layers", 1) or 1), 1)
    take_profit_pct = Decimal(str(getattr(strategy, "take_profit_pct", 0) or 0))
    stop_from_first = bool(getattr(strategy, "stop_from_first", False))
    allow_short = bool(getattr(strategy, "allow_short", False))
    raw_short_share = getattr(strategy, "max_short_exposure", None)
    short_share = (
        Decimal(str(raw_short_share))
        if raw_short_share is not None
        else cfg.position_share
    )
    short_stop_pct = Decimal(str(getattr(strategy, "short_stop_pct", 0) or 0))
    carry_tiers = getattr(strategy, "short_carry_tiers", None)
    carry_rate = getattr(strategy, "short_carry_rate", None)
    short_qty = 0
    short_entry: Decimal | None = None
    short_entry_ts: datetime | None = None
    short_entry_fee = Decimal("0")
    short_entry_notional = Decimal("0")
    trade_carry = Decimal("0")
    total_carry = Decimal("0")

    def buy(
        bar: CandleBar,
        reason: str,
        raw_price: Decimal | None = None,
        *,
        add: bool = False,
    ) -> None:
        nonlocal cash, qty, entry_price, first_entry_price, entry_ts, entry_cost
        nonlocal turnover, buy_notional, layers, added_qty
        if add and (qty <= 0 or entry_price is None):
            add = False
        if not add and qty > 0:
            return
        raw = Decimal(raw_price) if raw_price is not None else Decimal(bar.o)
        price = _execution_price(raw, "buy", cfg.slippage_bps)
        if max_layers > 1:
            layer_cap = (
                cfg.initial_cash * cfg.position_share / Decimal(max_layers)
            )
            budget = min(cash, layer_cap)
        else:
            budget = min(cash, cash * cfg.position_share)
        lot_cost = price * Decimal(cfg.lot)
        lots = int(budget // lot_cost) if lot_cost > 0 else 0
        wanted = lots * cfg.lot
        if wanted <= 0:
            return
        notional = price * Decimal(wanted)
        fee = _commission(notional, cfg.commission_bps)
        while wanted > 0 and notional + fee > cash:
            wanted -= cfg.lot
            notional = price * Decimal(wanted)
            fee = _commission(notional, cfg.commission_bps)
        if wanted <= 0:
            return
        cash -= notional + fee
        turnover += notional
        buy_notional += notional
        fill_reason = "average" if add else reason
        fills.append(BacktestFill(bar.ts, "buy", wanted, price, fee, fill_reason))
        if add and entry_price is not None and qty > 0:
            total_qty = qty + wanted
            entry_price = (
                entry_price * Decimal(qty) + price * Decimal(wanted)
            ) / Decimal(total_qty)
            entry_cost += fee
            qty = total_qty
            layers += 1
            added_qty += wanted
            return
        qty = wanted
        entry_price = price
        first_entry_price = price
        entry_ts = bar.ts
        entry_cost = fee
        layers = 1
        added_qty = 0

    def sell(bar: CandleBar, reason: str, raw_price: Decimal | None = None) -> None:
        nonlocal cash, qty, entry_price, first_entry_price, entry_ts, entry_cost
        nonlocal turnover, buy_notional, layers, added_qty
        if qty <= 0 or entry_price is None or entry_ts is None:
            return
        price = _execution_price(
            Decimal(raw_price) if raw_price is not None else Decimal(bar.o),
            "sell",
            cfg.slippage_bps,
        )
        notional = price * Decimal(qty)
        fee = _commission(notional, cfg.commission_bps)
        gross = (price - entry_price) * Decimal(qty)
        costs = entry_cost + fee
        trades.append(
            BacktestTrade(
                entry_ts=entry_ts,
                exit_ts=bar.ts,
                qty=qty,
                entry_price=entry_price,
                exit_price=price,
                gross_pnl=gross,
                costs=costs,
                net_pnl=gross - costs,
                exit_reason=reason,
                layers=max(layers, 1),
                added_qty=added_qty,
                buy_notional=buy_notional,
                sell_notional=notional,
            )
        )
        cash += notional - fee
        turnover += notional
        fills.append(BacktestFill(bar.ts, "sell", qty, price, fee, reason))
        qty = 0
        entry_price = None
        first_entry_price = None
        entry_ts = None
        entry_cost = Decimal("0")
        buy_notional = Decimal("0")
        layers = 0
        added_qty = 0

    def open_short(
        bar: CandleBar,
        reason: str,
        raw_price: Decimal | None = None,
    ) -> None:
        nonlocal cash, short_qty, short_entry, short_entry_ts, short_entry_fee
        nonlocal short_entry_notional, turnover, trade_carry
        if qty > 0 or short_qty > 0:
            return
        raw = Decimal(raw_price) if raw_price is not None else Decimal(bar.o)
        # Шорт — это продажа: проскальзывание уменьшает выручку.
        price = _execution_price(raw, "sell", cfg.slippage_bps)
        budget = cash * short_share
        lot_cost = price * Decimal(cfg.lot)
        lots = int(budget // lot_cost) if lot_cost > 0 else 0
        wanted = lots * cfg.lot
        if wanted <= 0:
            return
        notional = price * Decimal(wanted)
        fee = _commission(notional, cfg.commission_bps)
        cash += notional - fee
        turnover += notional
        fills.append(BacktestFill(bar.ts, "short", wanted, price, fee, reason))
        short_qty = wanted
        short_entry = price
        short_entry_ts = bar.ts
        short_entry_fee = fee
        short_entry_notional = notional
        trade_carry = Decimal("0")

    def cover_short(
        bar: CandleBar,
        reason: str,
        raw_price: Decimal | None = None,
    ) -> None:
        nonlocal cash, short_qty, short_entry, short_entry_ts, short_entry_fee
        nonlocal short_entry_notional, turnover, trade_carry
        if short_qty <= 0 or short_entry is None or short_entry_ts is None:
            return
        raw = Decimal(raw_price) if raw_price is not None else Decimal(bar.o)
        # Покрытие — покупка: проскальзывание увеличивает цену.
        price = _execution_price(raw, "buy", cfg.slippage_bps)
        notional = price * Decimal(short_qty)
        fee = _commission(notional, cfg.commission_bps)
        gross = (short_entry - price) * Decimal(short_qty)
        commission = short_entry_fee + fee
        costs = commission + trade_carry
        trades.append(
            BacktestTrade(
                entry_ts=short_entry_ts,
                exit_ts=bar.ts,
                qty=short_qty,
                entry_price=short_entry,
                exit_price=price,
                gross_pnl=gross,
                costs=costs,
                net_pnl=gross - costs,
                exit_reason=reason,
                buy_notional=notional,
                sell_notional=short_entry_notional,
                commission=commission,
                carry=trade_carry,
                position_side="short",
            )
        )
        cash -= notional + fee
        turnover += notional
        fills.append(BacktestFill(bar.ts, "cover", short_qty, price, fee, reason))
        short_qty = 0
        short_entry = None
        short_entry_ts = None
        short_entry_fee = Decimal("0")
        short_entry_notional = Decimal("0")
        trade_carry = Decimal("0")

    for index, bar in enumerate(bars):
        evaluating = index >= evaluation_start
        if evaluating and fill_at == "morning":
            if pending == "buy" and (qty == 0 or (pending_add and allow_add)):
                buy(bar, pending_reason, add=pending_add and qty > 0)
                note_entry = getattr(strategy, "note_entry", None)
                if callable(note_entry):
                    note_entry()
        elif evaluating and fill_at != "close":
            if pending == "buy" and (qty == 0 or (pending_add and allow_add)):
                buy(bar, pending_reason, add=pending_add and qty > 0)
            elif pending in {"sell", "exit"} and qty > 0:
                sell(bar, pending_reason)
            elif (
                allow_short
                and pending == "short"
                and qty == 0
                and short_qty == 0
            ):
                open_short(bar, pending_reason)
            elif (
                allow_short
                and pending in {"sell", "exit", "cover"}
                and short_qty > 0
            ):
                cover_short(bar, pending_reason)
        pending = None
        pending_reason = ""
        pending_add = False

        blocked_reentry = False
        stop_pct = Decimal(str(getattr(strategy, "stop_pct", 0) or 0))
        if evaluating and qty > 0 and entry_price is not None and stop_pct > 0:
            stop_ref = (
                first_entry_price
                if stop_from_first and first_entry_price is not None
                else entry_price
            )
            stop_price = stop_ref * (Decimal("1") - stop_pct)
            if Decimal(bar.low) <= stop_price:
                raw_fill = min(Decimal(bar.o), stop_price)
                sell(bar, "stop", raw_fill)
                blocked_reentry = True
                note_stop = getattr(strategy, "note_stop", None)
                if callable(note_stop):
                    note_stop()
        if (
            allow_short
            and evaluating
            and short_qty > 0
            and short_entry is not None
            and short_stop_pct > 0
        ):
            stop_price = short_entry * (Decimal("1") + short_stop_pct)
            if Decimal(bar.h) >= stop_price:
                raw_fill = max(Decimal(bar.o), stop_price)
                cover_short(bar, "stop", raw_fill)
                blocked_reentry = True

        if (
            evaluating
            and qty > 0
            and entry_price is not None
            and take_profit_pct > 0
        ):
            tp_price = entry_price * (Decimal("1") + take_profit_pct)
            if Decimal(bar.h) >= tp_price:
                raw_fill = (
                    Decimal(bar.o)
                    if Decimal(bar.o) >= tp_price
                    else tp_price
                )
                sell(bar, "take_profit", raw_fill)
                blocked_reentry = True

        if (
            allow_short
            and evaluating
            and short_qty > 0
            and short_entry is not None
        ):
            overnight = short_carry_rub(
                Decimal(bar.c) * Decimal(short_qty),
                carry_tiers,
                carry_rate,
            )
            if overnight > 0:
                cash -= overnight
                total_carry += overnight
                trade_carry += overnight
        if evaluating:
            if qty > 0 or short_qty > 0:
                exposed_bars += 1
            equity = cash + Decimal(qty) * Decimal(bar.c)
            if short_qty > 0:
                equity -= Decimal(short_qty) * Decimal(bar.c)
            equity_curve.append({"ts": bar.ts, "equity": equity})

        signal = strategy.on_bar(
            BarContext(
                ticker=ticker,
                bars=_BarPrefix(bars, index + 1),
                entry_price=short_entry if short_qty > 0 else entry_price,
                side="short" if short_qty > 0 else "buy",
            )
        )
        allowed = {"buy", "sell", "exit"}
        if allow_short:
            allowed.update({"short", "cover"})
        if signal is None or signal.kind not in allowed:
            continue
        if fill_at == "close":
            if not evaluating:
                continue
            # После стопа/тейка не входим в тот же вечер — ждём слабость на новом дне.
            if (
                signal.kind == "buy"
                and not blocked_reentry
                and (qty == 0 or allow_add)
            ):
                buy(
                    bar,
                    f"signal:{signal.kind}",
                    raw_price=Decimal(bar.c),
                    add=qty > 0,
                )
            elif signal.kind in {"sell", "exit"} and qty > 0:
                sell(bar, f"signal:{signal.kind}", raw_price=Decimal(bar.c))
            continue
        if fill_at == "morning":
            if not evaluating:
                continue
            # Утро: buy в pending на следующий open; вечер: sell/exit по close.
            if signal.kind in {"sell", "exit"} and qty > 0:
                sell(bar, f"signal:{signal.kind}", raw_price=Decimal(bar.c))
            elif (
                signal.kind == "buy"
                and not blocked_reentry
                and (qty == 0 or allow_add)
            ):
                pending = "buy"
                pending_reason = f"signal:{signal.kind}"
                pending_add = qty > 0
            continue
        can_execute_next = index + 1 >= evaluation_start
        if not can_execute_next:
            continue
        if signal.kind == "buy" and (qty == 0 or allow_add) and short_qty == 0:
            pending = "buy"
            pending_reason = f"signal:{signal.kind}"
            pending_add = qty > 0
        elif signal.kind in {"sell", "exit"} and qty > 0:
            pending = signal.kind
            pending_reason = f"signal:{signal.kind}"
        elif (
            allow_short
            and signal.kind == "short"
            and qty == 0
            and short_qty == 0
            and not blocked_reentry
        ):
            pending = "short"
            pending_reason = f"signal:{signal.kind}"
        elif (
            allow_short
            and signal.kind in {"sell", "exit", "cover"}
            and short_qty > 0
        ):
            pending = "cover"
            pending_reason = f"signal:{signal.kind}"

    final_equity = cash + Decimal(qty) * Decimal(bars[-1].c)
    if short_qty > 0:
        final_equity -= Decimal(short_qty) * Decimal(bars[-1].c)
    curve_values = [Decimal(str(row["equity"])) for row in equity_curve]
    period_returns = _returns(curve_values)
    total_return = final_equity / cfg.initial_cash - Decimal("1")
    elapsed_days = max(
        (bars[-1].ts - bars[evaluation_start].ts).total_seconds() / 86400,
        1,
    )
    years = Decimal(str(elapsed_days)) / Decimal("365.25")
    cagr: Decimal | None = None
    if elapsed_days >= 30 and final_equity > 0:
        cagr = (
            Decimal(
                str(float(final_equity / cfg.initial_cash) ** (1 / float(years)))
            )
            - Decimal("1")
        )
    wins = [trade for trade in trades if trade.net_pnl > 0]
    losses = [trade for trade in trades if trade.net_pnl < 0]
    gross_profit = sum((trade.net_pnl for trade in wins), Decimal("0"))
    gross_loss = abs(sum((trade.net_pnl for trade in losses), Decimal("0")))
    trade_net = sum((trade.net_pnl for trade in trades), Decimal("0"))
    costs = sum((fill.commission for fill in fills), Decimal("0"))

    benchmark_entry = _execution_price(
        Decimal(bars[evaluation_start].o), "buy", cfg.slippage_bps
    )
    benchmark_exit = _execution_price(
        Decimal(bars[-1].c), "sell", cfg.slippage_bps
    )
    benchmark_return = benchmark_exit / benchmark_entry - Decimal("1")
    benchmark_return -= _bps(cfg.commission_bps) * Decimal("2")

    return {
        "config": {
            "initial_cash": _money(cfg.initial_cash),
            "position_share": _number(cfg.position_share),
            "commission_bps": _number(cfg.commission_bps),
            "slippage_bps": _number(cfg.slippage_bps),
            "lot": cfg.lot,
            "execution": "next_bar_open",
            "evaluation_start": bars[evaluation_start].ts.isoformat(),
            "warmup_bars": evaluation_start,
        },
        "summary": {
            "initial_cash": _money(cfg.initial_cash),
            "final_equity": _money(final_equity),
            "net_pnl": _money(final_equity - cfg.initial_cash),
            "closed_trade_pnl": _money(trade_net),
            "costs": _money(costs + total_carry),
            "commissions": _money(costs),
            "short_carry": _money(total_carry),
            "total_return": _number(total_return),
            "cagr": _number(cagr) if cagr is not None else None,
            "max_drawdown": _number(_max_drawdown(curve_values)),
            "sharpe": _ratio(
                period_returns, periods_per_year=cfg.periods_per_year
            ),
            "sortino": _ratio(
                period_returns,
                periods_per_year=cfg.periods_per_year,
                downside_only=True,
            ),
            "trades": len(trades),
            "win_rate": len(wins) / len(trades) if trades else None,
            "profit_factor": (
                float(gross_profit / gross_loss) if gross_loss > 0 else None
            ),
            "expectancy": _money(trade_net / len(trades)) if trades else None,
            "turnover": _number(turnover / cfg.initial_cash),
            "exposure": _number(
                Decimal(exposed_bars)
                / Decimal(len(bars) - evaluation_start)
            ),
            "benchmark_return": _number(benchmark_return),
            "excess_return": _number(total_return - benchmark_return),
            "open_qty": qty,
            "insufficient_statistics": len(trades) < 5,
        },
        "fills": [
            {
                **asdict(fill),
                "ts": fill.ts.isoformat(),
                "price": _number(fill.price),
                "commission": _money(fill.commission),
            }
            for fill in fills
        ],
        "trades": [
            {
                **asdict(trade),
                "entry_ts": trade.entry_ts.isoformat(),
                "exit_ts": trade.exit_ts.isoformat(),
                "entry_price": _number(trade.entry_price),
                "exit_price": _number(trade.exit_price),
                "gross_pnl": _money(trade.gross_pnl),
                "costs": _money(trade.costs),
                "net_pnl": _money(trade.net_pnl),
                "buy_notional": _money(trade.buy_notional),
                "sell_notional": _money(trade.sell_notional),
                "buy_qty": trade.qty,
                "sell_qty": trade.qty,
                "averaged": trade.layers > 1,
            }
            for trade in trades
        ],
        "equity_curve": [
            {"ts": row["ts"].isoformat(), "equity": _money(row["equity"])}
            for row in equity_curve
        ],
    }


def run_walk_forward(
    strategy_factory: Callable[[], Strategy],
    ticker: str,
    bars: Sequence[CandleBar],
    *,
    train_bars: int,
    test_bars: int,
    config: BacktestConfig | None = None,
) -> dict:
    """Anchored walk-forward evaluation with isolated strategy instances."""
    if train_bars < 1:
        raise ValueError("train_bars must be >= 1")
    if test_bars < 1:
        raise ValueError("test_bars must be >= 1")
    if len(bars) <= train_bars:
        raise ValueError("not enough bars for an out-of-sample window")

    folds: list[dict] = []
    oos_start = train_bars
    while oos_start < len(bars):
        oos_end = min(oos_start + test_bars, len(bars))
        result = run_backtest(
            strategy_factory(),
            ticker,
            bars[:oos_end],
            config=config,
            evaluation_start=oos_start,
        )
        folds.append(
            {
                "train_start": bars[0].ts.isoformat(),
                "train_end": bars[oos_start - 1].ts.isoformat(),
                "test_start": bars[oos_start].ts.isoformat(),
                "test_end": bars[oos_end - 1].ts.isoformat(),
                "result": result,
            }
        )
        oos_start = oos_end

    compounded = Decimal("1")
    benchmark = Decimal("1")
    trades = 0
    worst_drawdown = Decimal("0")
    for fold in folds:
        summary = fold["result"]["summary"]
        compounded *= Decimal("1") + Decimal(str(summary["total_return"]))
        benchmark *= Decimal("1") + Decimal(str(summary["benchmark_return"]))
        trades += int(summary["trades"])
        worst_drawdown = max(
            worst_drawdown,
            Decimal(str(summary["max_drawdown"])),
        )
    total_return = compounded - Decimal("1")
    benchmark_return = benchmark - Decimal("1")
    return {
        "method": "anchored_walk_forward",
        "train_bars": train_bars,
        "test_bars": test_bars,
        "folds": folds,
        "oos_summary": {
            "folds": len(folds),
            "trades": trades,
            "total_return": _number(total_return),
            "benchmark_return": _number(benchmark_return),
            "excess_return": _number(total_return - benchmark_return),
            "max_drawdown": _number(worst_drawdown),
            "insufficient_statistics": trades < 5,
        },
    }
