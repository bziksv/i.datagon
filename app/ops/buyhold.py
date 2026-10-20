"""Buy & hold «если бы»: бюджет и дата покупки → PnL по дневкам CSV. Без заявок."""

from __future__ import annotations

import os
from datetime import date, datetime
from decimal import Decimal, ROUND_DOWN
from pathlib import Path

from app.advisory.moex_catalog import lookup_name
from app.broker.moex_candles import moscow_calendar_day
from app.broker.port import CandleBar
from app.strategy.backtest import load_bars
from app.strategy.desk import candle_dir, candle_sp500_dir

DEFAULT_COMMISSION_BPS = Decimal("5")


def _daily_csv(symbol: str) -> Path | None:
    name = symbol.strip().upper()
    if not name:
        return None
    daily = candle_dir() / f"{name}.csv"
    if daily.is_file() and daily.stat().st_size > 0:
        return daily
    sp = candle_sp500_dir() / f"{name}.csv"
    if sp.is_file() and sp.stat().st_size > 0:
        return sp
    return None


def _as_date(raw: str | date) -> date:
    if isinstance(raw, date) and not isinstance(raw, datetime):
        return raw
    text = str(raw).strip()[:10]
    return date.fromisoformat(text)


def _num(value: Decimal | int | float) -> float:
    return float(value)


def close_on_or_after(bars: list[CandleBar], day: date) -> tuple[CandleBar, date] | None:
    for bar in bars:
        session = moscow_calendar_day(bar.ts)
        if session is None:
            continue
        if session >= day:
            return bar, session
    return None


def last_close(bars: list[CandleBar]) -> tuple[CandleBar, date] | None:
    for bar in reversed(bars):
        session = moscow_calendar_day(bar.ts)
        if session is None:
            continue
        return bar, session
    return None


def _bps(commission_bps: Decimal) -> Decimal:
    return commission_bps / Decimal("10000")


def _commission(notional: Decimal, commission_bps: Decimal) -> Decimal:
    return abs(notional) * _bps(commission_bps)


def _equal_allocations(tickers: list[str], capital: Decimal) -> dict[str, Decimal]:
    if not tickers:
        return {}
    n = len(tickers)
    base = (capital / Decimal(n)).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
    out = {ticker: base for ticker in tickers}
    leftover = capital - base * n
    if leftover > 0 and tickers:
        out[tickers[0]] = (out[tickers[0]] + leftover).quantize(Decimal("0.01"))
    return out


def run_buyhold(
    *,
    start: str | date,
    capital: Decimal | float | int | None = None,
    allocations: dict[str, float | int | str | Decimal] | None = None,
    tickers: list[str] | None = None,
    commission_bps: Decimal | float | int | None = None,
) -> dict:
    start_day = _as_date(start)
    bps = (
        Decimal(str(commission_bps))
        if commission_bps is not None
        else Decimal(os.environ.get("BACKTEST_COMMISSION_BPS", str(DEFAULT_COMMISSION_BPS)))
    )
    if bps < 0:
        raise ValueError("commission_bps must be >= 0")

    alloc_map: dict[str, Decimal] = {}
    if allocations:
        for raw_ticker, raw_amt in allocations.items():
            ticker = str(raw_ticker).strip().upper()
            if not ticker:
                continue
            amt = Decimal(str(raw_amt))
            if amt <= 0:
                continue
            alloc_map[ticker] = amt
    elif capital is not None and tickers:
        names = [str(t).strip().upper() for t in tickers if str(t).strip()]
        cap = Decimal(str(capital))
        if cap <= 0:
            raise ValueError("capital must be > 0")
        alloc_map = _equal_allocations(names, cap)
    else:
        raise ValueError("нужны allocations или capital+tickers")

    if not alloc_map:
        raise ValueError("нет бумаг с положительной суммой")

    legs: list[dict] = []
    skipped: list[dict] = []
    total_allocated = Decimal("0")
    total_invested = Decimal("0")
    total_cash_left = Decimal("0")
    total_exit = Decimal("0")
    total_fees = Decimal("0")
    end_used: date | None = None
    start_used: date | None = None

    for ticker, budget in sorted(alloc_map.items()):
        total_allocated += budget
        path = _daily_csv(ticker)
        if path is None:
            skipped.append({"ticker": ticker, "reason": "no_csv"})
            total_cash_left += budget
            continue
        try:
            bars = load_bars(path)
        except OSError:
            skipped.append({"ticker": ticker, "reason": "read_error"})
            total_cash_left += budget
            continue
        if not bars:
            skipped.append({"ticker": ticker, "reason": "empty_csv"})
            total_cash_left += budget
            continue
        entry_hit = close_on_or_after(bars, start_day)
        if entry_hit is None:
            skipped.append({"ticker": ticker, "reason": "no_bar_on_or_after_start"})
            total_cash_left += budget
            continue
        entry_bar, entry_day = entry_hit
        exit_hit = last_close(bars)
        if exit_hit is None:
            skipped.append({"ticker": ticker, "reason": "no_exit_bar"})
            total_cash_left += budget
            continue
        exit_bar, exit_day = exit_hit
        if exit_day < entry_day:
            skipped.append({"ticker": ticker, "reason": "exit_before_entry"})
            total_cash_left += budget
            continue
        entry = Decimal(entry_bar.c)
        exit_px = Decimal(exit_bar.c)
        if entry <= 0 or exit_px <= 0:
            skipped.append({"ticker": ticker, "reason": "bad_price"})
            total_cash_left += budget
            continue
        # Сначала комиссия с полного бюджета на вход: сколько лотов влезет.
        fee_rate = _bps(bps)
        # shares * entry * (1 + fee_rate) <= budget
        denom = entry * (Decimal("1") + fee_rate)
        shares = (budget / denom).to_integral_value(rounding=ROUND_DOWN)
        if shares < 1:
            skipped.append({"ticker": ticker, "reason": "budget_too_small"})
            total_cash_left += budget
            continue
        entry_notional = shares * entry
        entry_fee = _commission(entry_notional, bps)
        exit_notional = shares * exit_px
        exit_fee = _commission(exit_notional, bps)
        invested = entry_notional + entry_fee
        cash_left = budget - invested
        if cash_left < 0:
            cash_left = Decimal("0")
        final_value = exit_notional - exit_fee
        pnl = final_value + cash_left - budget
        pnl_pct = (final_value / entry_notional - Decimal("1")) if entry_notional else Decimal("0")

        total_invested += invested
        total_cash_left += cash_left
        total_exit += final_value
        total_fees += entry_fee + exit_fee
        if start_used is None or entry_day < start_used:
            start_used = entry_day
        if end_used is None or exit_day > end_used:
            end_used = exit_day

        legs.append(
            {
                "ticker": ticker,
                "name": lookup_name(ticker),
                "status": "ok",
                "budget": _num(budget),
                "shares": int(shares),
                "entry_close": _num(entry),
                "exit_close": _num(exit_px),
                "entry_day": entry_day.isoformat(),
                "exit_day": exit_day.isoformat(),
                "invested": _num(invested),
                "cash_left": _num(cash_left),
                "final_value": _num(final_value),
                "fees": _num(entry_fee + exit_fee),
                "pnl": _num(pnl),
                "pnl_pct": _num(pnl_pct),
            }
        )

    legs.sort(key=lambda row: row.get("pnl_pct") or 0, reverse=True)
    final_equity = total_exit + total_cash_left
    pnl_total = final_equity - total_allocated
    pnl_pct_total = (
        (final_equity / total_allocated - Decimal("1"))
        if total_allocated > 0
        else Decimal("0")
    )
    days = 0
    if start_used and end_used:
        days = (end_used - start_used).days

    return {
        "start": start_day.isoformat(),
        "start_used": start_used.isoformat() if start_used else None,
        "end_used": end_used.isoformat() if end_used else None,
        "days": days,
        "capital": _num(total_allocated),
        "invested": _num(total_invested),
        "cash_left": _num(total_cash_left),
        "fees": _num(total_fees),
        "commission_bps": _num(bps),
        "final_equity": _num(final_equity),
        "pnl": _num(pnl_total),
        "pnl_pct": _num(pnl_pct_total),
        "legs": legs,
        "skipped": skipped,
        "ok": len(legs),
        "skipped_n": len(skipped),
    }
