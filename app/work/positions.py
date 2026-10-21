"""Карточки позиций рабочей песочницы: P&L, лимит имени и где бумага относительно правил выхода."""

from __future__ import annotations

import os
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from app.advisory.moex_catalog import lookup_name
from app.strategy.abs_mom import AbsMomentum4Strategy

SPARK_PAD_DAYS = 10
SPARK_MIN_BARS = 40
MSK = timedelta(hours=3)


def _dec(value: object, default: str = "0") -> Decimal:
    try:
        return Decimal(str(value if value not in (None, "") else default))
    except Exception:  # noqa: BLE001
        return Decimal(default)


def _f(value: Decimal | None, digits: int = 6) -> float | None:
    if value is None:
        return None
    return round(float(value), digits)


def is_money_row(row: dict) -> bool:
    ticker = str(row.get("ticker") or "").upper()
    kind = str(row.get("instrument_type") or "").lower()
    return kind == "currency" or "UTSTOM" in ticker or ticker.startswith(("RUB", "USD", "EUR"))


def mark_price(row: dict) -> Decimal:
    """Текущая цена брокера; если её нет — средняя (тогда P&L честно ноль)."""
    current = _dec(row.get("current_price"))
    if current > 0:
        return current
    return _dec(row.get("avg_price"))


def equity_at_market(portfolio: dict | None) -> Decimal:
    portfolio = portfolio or {}
    total = _dec(portfolio.get("cash"))
    for row in portfolio.get("positions") or []:
        if is_money_row(row):
            continue
        qty = _dec(row.get("qty"))
        if qty > 0:
            total += qty * mark_price(row)
    return total


def read_daily(ticker: str, root: Path | None = None) -> list[tuple[date, Decimal]]:
    base = root or Path(os.environ.get("CANDLE_DIR", "data/candles"))
    path = base / f"{ticker.upper()}.csv"
    if not path.is_file():
        return []
    out: list[tuple[date, Decimal]] = []
    for line in path.read_text(encoding="utf-8").splitlines()[1:]:
        parts = line.split(",")
        if len(parts) < 5 or not parts[0]:
            continue
        try:
            ts = datetime.fromisoformat(parts[0].replace("Z", "+00:00"))
            day = (ts.astimezone(UTC) + MSK).date() if ts.tzinfo else ts.date()
            out.append((day, Decimal(parts[4])))
        except Exception:  # noqa: BLE001
            continue
    return out


def _holding_trades(trades: list[dict], ticker: str) -> list[dict]:
    """Сделки текущего удержания: всё после последней продажи этой бумаги."""
    rows = [row for row in trades if str(row.get("ticker") or "").upper() == ticker]
    last_sell = -1
    for i, row in enumerate(rows):
        if row.get("side") == "sell":
            last_sell = i
    return rows[last_sell + 1 :]


def _trade_day(row: dict) -> date | None:
    raw = str(row.get("ts") or "")
    if not raw:
        return None
    try:
        ts = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    return (ts.astimezone(UTC) + MSK).date() if ts.tzinfo else ts.date()


def _sma(values: list[Decimal], period: int) -> list[Decimal | None]:
    out: list[Decimal | None] = []
    acc = Decimal("0")
    for i, value in enumerate(values):
        acc += value
        if i >= period:
            acc -= values[i - period]
        out.append(acc / period if i >= period - 1 else None)
    return out


def position_card(
    row: dict,
    *,
    trades: list[dict],
    equity: Decimal,
    name_cap: Decimal,
    names: dict[str, str] | None = None,
    today: date | None = None,
    root: Path | None = None,
    rules: bool = True,
) -> dict:
    strat = AbsMomentum4Strategy()
    ticker = str(row.get("ticker") or "").upper()
    qty = _dec(row.get("qty"))
    avg = _dec(row.get("avg_price"))
    price = mark_price(row)
    value = qty * price
    pnl = (price - avg) * qty if avg > 0 else Decimal("0")
    pnl_pct = (price / avg - 1) if avg > 0 else Decimal("0")
    weight = (value / equity) if equity > 0 else Decimal("0")
    cap_rub = equity * name_cap
    cap_fill = (value / cap_rub) if cap_rub > 0 else Decimal("0")

    held = _holding_trades(trades, ticker)
    buys = [t for t in held if t.get("side") == "buy"]
    entry_day = _trade_day(buys[0]) if buys else None
    today = today or (datetime.now(UTC) + MSK).date()
    days_held = (today - entry_day).days if entry_day else None

    bars = read_daily(ticker, root)
    closes = [c for _, c in bars]
    days = [d for d, _ in bars]

    prev_close: Decimal | None = None
    if bars:
        prev_close = closes[-1] if days[-1] < today else (closes[-2] if len(closes) > 1 else None)
    day_pct = (price / prev_close - 1) if prev_close and prev_close > 0 else None

    sma_all = _sma(closes, strat.sma_period)
    trend_ratio = None
    roc = None
    if len(closes) > max(strat.lookback, strat.sma_period):
        last_sma = sma_all[-1]
        trend_ratio = closes[-1] / last_sma if last_sma else None
        base = closes[-(strat.lookback + 1)]
        roc = closes[-1] / base - 1 if base > 0 else None

    # Слабые дни подряд с конца, только внутри удержания.
    start_idx = 0
    if entry_day:
        for i, d in enumerate(days):
            if d >= entry_day:
                start_idx = i
                break
        else:
            start_idx = len(days)
    weak = 0
    for i in range(len(closes) - 1, max(start_idx, strat.lookback) - 1, -1):
        base = closes[i - strat.lookback]
        r = closes[i] / base - 1 if base > 0 else Decimal("0")
        if r >= strat.exit_roc:
            break
        weak += 1

    entry_ref = avg if avg > 0 else (closes[start_idx] if start_idx < len(closes) else price)
    held_closes = closes[start_idx:] if entry_day else []
    peak = max(held_closes + [price]) if held_closes else max(price, entry_ref)
    armed = entry_ref > 0 and peak / entry_ref >= strat.trail_arm
    trail_pct = strat._trail_base
    exit_price = peak * (1 - trail_pct) if armed else None
    arm_price = entry_ref * strat.trail_arm if entry_ref > 0 else None

    trail_hit = bool(exit_price is not None and closes and closes[-1] <= exit_price)
    if weak >= strat.exit_streak or trail_hit:
        verdict = "exit"
    elif (
        weak > 0
        or (trend_ratio is not None and trend_ratio < 1)
        or (exit_price is not None and price <= exit_price * Decimal("1.01"))
    ):
        verdict = "watch"
    else:
        verdict = "hold"

    # Спарклайн: с даты входа минус запас, либо последние 40 баров.
    if entry_day and start_idx < len(closes):
        s0 = max(0, start_idx - SPARK_PAD_DAYS)
    else:
        s0 = max(0, len(closes) - SPARK_MIN_BARS)
    spark_days = days[s0:]
    spark = {
        "days": [d.isoformat() for d in spark_days],
        "closes": [_f(c) for c in closes[s0:]],
        "sma": [_f(v) if v is not None else None for v in sma_all[s0:]],
        "avg_steps": [
            {"day": d.isoformat(), "avg": _f(_dec(t.get("avg_after") or t.get("price")))}
            for t in buys
            if (d := _trade_day(t))
        ],
        "marks": [
            {
                "day": d.isoformat(),
                "side": t.get("side"),
                "layer": t.get("layer"),
                "price": _f(_dec(t.get("price"))),
            }
            for t in held
            if (d := _trade_day(t))
        ],
        "now": _f(price),
    }

    label = (names or {}).get(ticker) or lookup_name(ticker)
    card = {
        "ticker": ticker,
        "name": label if label and label.upper() != ticker else "",
        "qty": _f(qty, 4),
        "avg_price": _f(avg),
        "price": _f(price),
        "value": _f(value, 2),
        "pnl": _f(pnl, 2),
        "pnl_pct": _f(pnl_pct),
        "day_pct": _f(day_pct),
        "weight": _f(weight),
        "cap_rub": _f(cap_rub, 2),
        "cap_fill": _f(cap_fill),
        "entry_day": entry_day.isoformat() if entry_day else None,
        "days_held": days_held,
        "layers": len(buys),
        "trend": {
            "ratio": _f(trend_ratio),
            "floor": 1.0,
            "stretch": _f(strat.max_stretch),
            "sma_period": strat.sma_period,
        },
        "roc": {"value": _f(roc), "floor": _f(strat.exit_roc), "lookback": strat.lookback},
        "weak": {"count": weak, "limit": strat.exit_streak},
        "trail": {
            "armed": bool(armed),
            "arm_pct": _f(strat.trail_arm - 1),
            "arm_price": _f(arm_price),
            "pct": _f(trail_pct),
            "peak": _f(peak),
            "exit_price": _f(exit_price),
        },
        "verdict": verdict,
        "spark": spark,
    }
    if not rules:
        # Правила выхода посчитаны только для Абс. моментум-4; у других рукавов их не показываем.
        card.update({"trend": None, "roc": None, "weak": None, "trail": None, "verdict": "hold"})
    return card


def position_cards(
    portfolio: dict | None,
    *,
    trades: list[dict],
    name_cap: Decimal,
    names: dict[str, str] | None = None,
    root: Path | None = None,
    rules: bool = True,
) -> list[dict]:
    portfolio = portfolio or {}
    equity = equity_at_market(portfolio)
    cards = []
    for row in portfolio.get("positions") or []:
        if is_money_row(row) or _dec(row.get("qty")) <= 0:
            continue
        cards.append(
            position_card(
                row,
                trades=trades,
                equity=equity,
                name_cap=name_cap,
                names=names,
                root=root,
                rules=rules,
            )
        )
    order = {"exit": 0, "watch": 1, "hold": 2}
    cards.sort(
        key=lambda c: (order.get(c["verdict"], 3), -((c["weak"] or {}).get("count") or 0), c["ticker"])
    )
    return cards
