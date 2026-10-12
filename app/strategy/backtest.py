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


def replay(
    strategy: Strategy,
    ticker: str,
    bars: Sequence[CandleBar],
) -> list[Signal]:
    signals: list[Signal] = []
    for end in range(1, len(bars) + 1):
        got = strategy.on_bar(BarContext(ticker, bars[:end]))
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


def _bps(value: Decimal) -> Decimal:
    return Decimal(value) / Decimal("10000")


def _execution_price(price: Decimal, side: str, slippage_bps: Decimal) -> Decimal:
    slip = _bps(slippage_bps)
    return Decimal(price) * (
        Decimal("1") + slip if side == "buy" else Decimal("1") - slip
    )


def _commission(notional: Decimal, commission_bps: Decimal) -> Decimal:
    return abs(Decimal(notional)) * _bps(commission_bps)


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
    """Long-only simulation.

    Cross/indicator decisions are made after bar close and executed no earlier
    than the next bar open. A fixed strategy stop may execute intrabar; a gap
    through the stop executes at the worse opening price.
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
    entry_ts: datetime | None = None
    entry_cost = Decimal("0")
    pending: str | None = None
    pending_reason = ""
    fills: list[BacktestFill] = []
    trades: list[BacktestTrade] = []
    equity_curve: list[dict] = []
    turnover = Decimal("0")
    exposed_bars = 0

    def buy(bar: CandleBar, reason: str) -> None:
        nonlocal cash, qty, entry_price, entry_ts, entry_cost, turnover
        raw_price = Decimal(bar.o)
        price = _execution_price(raw_price, "buy", cfg.slippage_bps)
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
        qty = wanted
        entry_price = price
        entry_ts = bar.ts
        entry_cost = fee
        turnover += notional
        fills.append(BacktestFill(bar.ts, "buy", wanted, price, fee, reason))

    def sell(bar: CandleBar, reason: str, raw_price: Decimal | None = None) -> None:
        nonlocal cash, qty, entry_price, entry_ts, entry_cost, turnover
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
            )
        )
        cash += notional - fee
        turnover += notional
        fills.append(BacktestFill(bar.ts, "sell", qty, price, fee, reason))
        qty = 0
        entry_price = None
        entry_ts = None
        entry_cost = Decimal("0")

    for index, bar in enumerate(bars):
        evaluating = index >= evaluation_start
        if evaluating:
            if pending == "buy" and qty == 0:
                buy(bar, pending_reason)
            elif pending in {"sell", "exit"} and qty > 0:
                sell(bar, pending_reason)
        pending = None
        pending_reason = ""

        stop_pct = Decimal(str(getattr(strategy, "stop_pct", 0) or 0))
        if evaluating and qty > 0 and entry_price is not None and stop_pct > 0:
            stop_price = entry_price * (Decimal("1") - stop_pct)
            if Decimal(bar.low) <= stop_price:
                raw_fill = min(Decimal(bar.o), stop_price)
                sell(bar, "stop", raw_fill)

        if evaluating:
            if qty > 0:
                exposed_bars += 1
            equity = cash + Decimal(qty) * Decimal(bar.c)
            equity_curve.append({"ts": bar.ts, "equity": equity})

        signal = strategy.on_bar(
            BarContext(
                ticker=ticker,
                bars=bars[: index + 1],
                entry_price=entry_price,
            )
        )
        can_execute_next = index + 1 >= evaluation_start
        if (
            can_execute_next
            and signal is not None
            and signal.kind in {"buy", "sell", "exit"}
        ):
            if signal.kind == "buy" and qty == 0:
                pending = "buy"
                pending_reason = f"signal:{signal.kind}"
            elif signal.kind in {"sell", "exit"} and qty > 0:
                pending = signal.kind
                pending_reason = f"signal:{signal.kind}"

    final_equity = cash + Decimal(qty) * Decimal(bars[-1].c)
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
            "costs": _money(costs),
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
