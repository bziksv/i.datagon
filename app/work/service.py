"""Рабочая песочница: мастер, лента, заявки. Боевой контур не вызывается."""

from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime, time, timedelta
from decimal import Decimal

from app.broker.port import OrderRequest
from app.work.desk_state import (
    SLEEVE,
    already_sent,
    connect_strategy,
    load_state,
    order_key,
    payin_value,
    remember_decision,
    remember_mark,
    remember_order,
    remember_payin,
    save_params,
    save_state,
    set_account,
    set_enabled,
    steps,
)
from app.work.live import live_view
from app.work.positions import equity_at_market, is_money_row, mark_price, position_cards

WORK_TICKERS_LIMIT = 40
# TQBR: решение по закрытому дню в 18:50 МСК = 15:50 UTC.
DECISION_UTC = time(15, 50)
RANGES = {
    "day": (timedelta(days=1), timedelta(minutes=1)),
    "week": (timedelta(days=7), timedelta(minutes=15)),
    "month": (timedelta(days=31), timedelta(hours=1)),
    "all": (None, timedelta(hours=4)),
}


def _public_error(exc: Exception) -> str:
    text = str(exc)
    if "UNAVAILABLE" in text or "connect" in text.lower() or "lookup" in text.lower():
        return "Песочница T-Invest сейчас не отвечает. Токен на сервере есть, до API достучаться не удалось."
    return "Песочница не ответила."


def token_ok() -> bool:
    from app.broker.tinkoff import BrokerTokenError, sandbox_token

    try:
        sandbox_token()
    except BrokerTokenError:
        return False
    return True


def list_accounts() -> list[dict]:
    from app.broker.sandbox_snapshot import normalize_account
    from app.broker.tinkoff import make_client

    with make_client() as client:
        accounts = list(client.sandbox.get_sandbox_accounts().accounts)
    return [normalize_account(item) for item in accounts]


def read_portfolio(account_id: str) -> dict:
    from app.broker.sandbox_snapshot import normalize_portfolio
    from app.broker.tinkoff import make_client

    with make_client() as client:
        portfolio = client.sandbox.get_sandbox_portfolio(account_id=account_id)
    view = normalize_portfolio(portfolio)
    view["account_id"] = account_id
    return view


def next_decision_at(now: datetime | None = None) -> datetime:
    """Следующие 18:50 МСК в будний день."""
    now = (now or datetime.now(UTC)).astimezone(UTC)
    day = now.date()
    candidate = datetime.combine(day, DECISION_UTC, tzinfo=UTC)
    if now >= candidate:
        day = day + timedelta(days=1)
    while day.weekday() >= 5:
        day = day + timedelta(days=1)
    return datetime.combine(day, DECISION_UTC, tzinfo=UTC)


def _parse_ts(raw: str) -> datetime | None:
    try:
        ts = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError:
        return None
    return ts if ts.tzinfo else ts.replace(tzinfo=UTC)


def curve_slice(curve: list[dict], span: str, now: datetime | None = None) -> list[dict]:
    """Срез кривой equity под диапазон и прореживание: не больше ~1 точки на шаг."""
    window, step = RANGES.get(span, RANGES["day"])
    now = now or datetime.now(UTC)
    since = now - window if window else None
    out: list[dict] = []
    last_bucket: int | None = None
    step_s = int(step.total_seconds())
    points = []
    for row in curve:
        ts = _parse_ts(row.get("ts") or "")
        if ts is None:
            continue
        if since and ts < since:
            continue
        points.append((ts, row))
    for i, (ts, row) in enumerate(points):
        bucket = int(ts.timestamp()) // step_s
        is_last = i == len(points) - 1
        if bucket == last_bucket and not is_last:
            out[-1] = {"ts": ts.isoformat(), "equity": row.get("equity")}
            continue
        last_bucket = bucket
        out.append({"ts": ts.isoformat(), "equity": row.get("equity")})
    return out


def _start_of_day_msk(now: datetime) -> datetime:
    msk = now.astimezone(UTC) + timedelta(hours=3)
    start = datetime.combine(msk.date(), time(0, 0), tzinfo=UTC) - timedelta(hours=3)
    return start


def _equity_points(
    curve: list[dict],
) -> tuple[Decimal | None, Decimal | None, datetime | None, datetime | None]:
    """Первая точка вообще и первая точка сегодня (МСК) с их временем."""
    first = None
    day_first = None
    first_ts = None
    day_ts = None
    day_start = _start_of_day_msk(datetime.now(UTC))
    for row in curve:
        ts = _parse_ts(row.get("ts") or "")
        try:
            value = Decimal(str(row.get("equity")))
        except Exception:  # noqa: BLE001
            continue
        if first is None:
            first = value
            first_ts = ts
        if day_first is None and ts is not None and ts >= day_start:
            day_first = value
            day_ts = ts
    return first, day_first, first_ts, day_ts


def payins_after(payins: list[dict], since: datetime | None) -> Decimal:
    """Сколько денег внесено после отметки: эта сумма — не результат стратегии."""
    total = Decimal("0")
    for row in payins:
        ts = _parse_ts(row.get("ts") or "")
        if ts is None or (since is not None and ts <= since):
            continue
        try:
            total += Decimal(str(row.get("amount")))
        except Exception:  # noqa: BLE001
            continue
    return total


def view(
    *,
    span: str = "day",
    names: dict[str, str] | None = None,
    signals: list[dict] | None = None,
) -> dict:
    state = load_state()
    ok = False
    accounts: list[dict] = []
    error = ""
    if token_ok():
        try:
            accounts = list_accounts()
            ok = True
        except Exception as exc:  # noqa: BLE001 — статус мастера, не падение API
            error = _public_error(exc)
    portfolio = state.get("portfolio")
    live_portfolio = False
    if ok and state.get("account_id"):
        try:
            portfolio = read_portfolio(state["account_id"])
            live_portfolio = True
        except Exception as exc:  # noqa: BLE001
            error = error or _public_error(exc)

    sleeve_share = Decimal(str(state.get("sleeve_share") or "0.40"))
    name_cap = Decimal(str(state.get("name_cap") or "0.10"))
    equity = equity_at_market(portfolio)
    cash = Decimal(str((portfolio or {}).get("cash") or "0"))
    invested = equity - cash
    sleeve_rub = equity * sleeve_share
    name_cap_rub = equity * name_cap
    max_names = int(sleeve_share // name_cap) if name_cap > 0 else 0

    curve = state.get("equity_curve") or []
    first, day_first, first_ts, day_ts = _equity_points(curve)
    payins = state.get("payins") or []
    base_total = first + payins_after(payins, first_ts) if first is not None else None
    base_day = day_first + payins_after(payins, day_ts) if day_first is not None else None
    pnl_total = (equity - base_total) if base_total is not None and equity > 0 else None
    pnl_day = (equity - base_day) if base_day is not None and equity > 0 else None

    trades = state.get("trades") or []
    cards = position_cards(portfolio, trades=trades, name_cap=name_cap, names=names)
    trades_view = _trades_view(trades, names or {})

    now = datetime.now(UTC)
    return {
        "sleeve": SLEEVE,
        "steps": steps(state, token_ok=ok),
        "account_id": state.get("account_id") or "",
        "accounts": accounts,
        "sleeve_share": state.get("sleeve_share"),
        "name_cap": state.get("name_cap"),
        "params_saved": bool(state.get("params_saved")),
        "enabled": bool(state.get("enabled")),
        "portfolio": portfolio,
        "portfolio_live": live_portfolio,
        "equity": float(equity),
        "cash": float(cash),
        "invested": float(invested),
        "equity_start": float(first) if first is not None else None,
        "pnl_total": float(pnl_total) if pnl_total is not None else None,
        "pnl_total_pct": float(pnl_total / base_total) if pnl_total is not None and base_total else None,
        "pnl_day": float(pnl_day) if pnl_day is not None else None,
        "pnl_day_pct": float(pnl_day / base_day) if pnl_day is not None and base_day else None,
        "payins": payins[-50:],
        "payins_total": float(payins_after(payins, None)),
        "sleeve_rub": float(sleeve_rub),
        "name_cap_rub": float(name_cap_rub),
        "max_names": max_names,
        "sleeve_fill": float(invested / sleeve_rub) if sleeve_rub > 0 else 0.0,
        "positions": cards,
        "trades": trades_view,
        "range": span if span in RANGES else "day",
        "curve": curve_slice(curve, span, now),
        "curve_day": curve_slice(curve, "day", now),
        "decisions": (state.get("decisions") or [])[-60:],
        "signals": signals or [],
        "next_run_at": next_decision_at(now).isoformat(),
        "server_time": now.isoformat(),
        "live": live_view(),
        "error": error,
    }


def _trades_view(trades: list[dict], names: dict[str, str]) -> list[dict]:
    """Сделки с суммой и зафиксированным P&L продажи против средней на момент выхода."""
    from app.advisory.moex_catalog import lookup_name

    avg_by: dict[str, Decimal] = {}
    out = []
    for row in trades:
        ticker = str(row.get("ticker") or "").upper()
        qty = Decimal(str(row.get("qty") or "0"))
        price = Decimal(str(row.get("price") or "0"))
        item = dict(row)
        label = names.get(ticker) or lookup_name(ticker)
        item["name"] = label if label and label.upper() != ticker else ""
        item["amount"] = float(qty * price)
        if row.get("side") == "buy":
            try:
                avg_by[ticker] = Decimal(str(row.get("avg_after") or price))
            except Exception:  # noqa: BLE001
                avg_by[ticker] = price
        elif row.get("side") == "sell" and ticker in avg_by and avg_by[ticker] > 0:
            item["realized"] = float((price - avg_by[ticker]) * qty)
            item["realized_pct"] = float(price / avg_by[ticker] - 1)
            avg_by.pop(ticker, None)
        out.append(item)
    return out


def probe() -> dict:
    if not token_ok():
        raise ValueError("TINKOFF_SANDBOX_TOKEN пуст на сервере")
    accounts = list_accounts()
    if not accounts:
        raise ValueError("в песочнице нет счетов")
    return {"accounts": accounts}


def open_account() -> dict:
    if not token_ok():
        raise ValueError("TINKOFF_SANDBOX_TOKEN пуст на сервере")
    from app.broker.tinkoff import ensure_sandbox_pay_in, open_sandbox_account_id

    deposit = Decimal(os.environ.get("SANDBOX_DEPOSIT", "1000000"))
    account_id = open_sandbox_account_id()
    ensure_sandbox_pay_in(account_id, deposit)
    return choose_account(account_id)


def pay_in(amount: str) -> dict:
    """Пополнить выбранный счёт песочницы игровыми рублями (SandboxPayIn)."""
    if not token_ok():
        raise ValueError("TINKOFF_SANDBOX_TOKEN пуст на сервере")
    state = load_state()
    account_id = state.get("account_id") or ""
    if not account_id:
        raise ValueError("сначала выберите счёт песочницы")
    value = payin_value(amount)
    from app.broker.tinkoff import sandbox_pay_in_rub

    try:
        sandbox_pay_in_rub(account_id, value)
    except Exception as exc:  # noqa: BLE001
        raise ValueError(_public_error(exc)) from exc
    state = remember_payin(load_state(), value)
    save_state(state)
    return {"ok": True, "amount": format(value, "f")}


def choose_account(account_id: str) -> dict:
    accounts = list_accounts()
    known = {row["broker_account_id"] for row in accounts}
    state = set_account(load_state(), account_id, known)
    save_state(state)
    return {"ok": True}


def attach_strategy() -> dict:
    state = connect_strategy(load_state())
    save_state(state)
    return {"ok": True}


def store_params(*, sleeve_share: str, name_cap: str) -> dict:
    state = save_params(load_state(), sleeve_share=sleeve_share, name_cap=name_cap)
    save_state(state)
    return {
        "ok": True,
        "sleeve_share": state["sleeve_share"],
        "name_cap": state["name_cap"],
    }


def switch(enabled: bool) -> dict:
    state = set_enabled(load_state(), enabled)
    save_state(state)
    return {"ok": True, "enabled": bool(state.get("enabled"))}


def work_tickers(state: dict | None = None) -> list[str]:
    state = state if state is not None else load_state()
    names: list[str] = []
    portfolio = state.get("portfolio") or {}
    for row in portfolio.get("positions") or []:
        if is_money_row(row):
            continue
        ticker = str(row.get("ticker") or "").upper()
        if ticker and ticker not in names:
            names.append(ticker)
    for trade in state.get("trades") or []:
        ticker = str(trade.get("ticker") or "").upper()
        if ticker and ticker not in names:
            names.append(ticker)
    return names[:WORK_TICKERS_LIMIT]


def refresh_tape() -> int:
    """Отметка equity по рынку + короткие дневки рабочих тикеров."""
    from pathlib import Path

    from app.ops.refresh_candles import refresh

    state = load_state()
    if token_ok() and state.get("account_id"):
        try:
            portfolio = read_portfolio(state["account_id"])
            equity = equity_at_market(portfolio)
            state = remember_mark(state, equity=str(equity), portfolio=portfolio)
            save_state(state)
        except Exception:  # noqa: BLE001
            pass
    tickers = work_tickers(state)
    if not tickers:
        return 0
    root = Path(os.environ.get("CANDLE_DIR", "data/candles"))
    written = 0
    for ticker in tickers:
        try:
            refresh([ticker], days=5, tf="1d", root=root)
            written += 1
        except Exception:  # noqa: BLE001
            continue
    return written


def _equity(portfolio: dict) -> Decimal:
    return equity_at_market(portfolio)


def _layers(trades: list[dict], ticker: str) -> list[dict]:
    return [row for row in trades if str(row.get("ticker") or "").upper() == ticker]


def _decision(ticker: str, side: str, day: str, status: str, **extra) -> dict:
    row = {
        "ticker": ticker,
        "side": side,
        "day": day,
        "status": status,
        "ts": datetime.now(UTC).isoformat(),
    }
    row.update(extra)
    return row


def _note(state: dict, decision: dict) -> dict:
    for prev in reversed(state.get("decisions") or []):
        if (
            prev.get("ticker") == decision["ticker"]
            and prev.get("side") == decision["side"]
            and prev.get("day") == decision["day"]
        ):
            if prev.get("status") == decision["status"]:
                return state
            break
    return remember_decision(state, decision)


def place_signals(rows: list) -> int:
    """Заявки только для включённого мастера и abs_momentum_4. Отказы пишем в decisions."""
    state = load_state()
    wanted = []
    for row in rows:
        if getattr(row, "sleeve", "") != SLEEVE:
            continue
        side = "sell" if row.kind in {"sell", "exit"} else "buy" if row.kind == "buy" else ""
        if not side:
            continue
        ticker = str(row.ticker or "").upper()
        day = (
            row.ts.astimezone(UTC).date().isoformat()
            if row.ts
            else datetime.now(UTC).date().isoformat()
        )
        wanted.append((ticker, side, day))
    if not wanted:
        return 0

    account_id = str(state.get("account_id") or "")
    if not state.get("enabled") or not account_id or not token_ok():
        status = "disabled" if not state.get("enabled") else "no_account"
        for ticker, side, day in wanted:
            state = _note(state, _decision(ticker, side, day, status))
        save_state(state)
        return 0

    portfolio = state.get("portfolio") or {}
    if not portfolio:
        try:
            portfolio = read_portfolio(account_id)
        except Exception:  # noqa: BLE001
            return 0
    equity = _equity(portfolio)
    sleeve_share = Decimal(str(state["sleeve_share"]))
    name_cap = Decimal(str(state["name_cap"]))
    if name_cap >= Decimal("1") or sleeve_share >= Decimal("1") or name_cap > sleeve_share:
        return 0
    held = {
        str(row.get("ticker") or "").upper(): row
        for row in (portfolio.get("positions") or [])
        if not is_money_row(row)
    }
    sleeve_notional = Decimal("0")
    for row in held.values():
        qty = Decimal(str(row.get("qty") or "0"))
        if qty > 0:
            sleeve_notional += qty * mark_price(row)
    placed = 0
    from app.broker.tinkoff import find_moex_instrument, post_sandbox_order

    for ticker, side, day in wanted:
        key = order_key(ticker, day, side)
        if already_sent(state, key):
            continue
        position = held.get(ticker) or {}
        price = mark_price(position) if position else Decimal("0")
        if price <= 0:
            price = _last_close(ticker)
        if price <= 0:
            state = _note(state, _decision(ticker, side, day, "no_price"))
            continue
        if side == "sell":
            qty = int(Decimal(str(position.get("qty") or "0")))
            if qty < 1:
                state = _note(state, _decision(ticker, side, day, "nothing_to_sell"))
                continue
        else:
            name_room = equity * name_cap - Decimal(str(position.get("qty") or "0")) * price
            sleeve_room = equity * sleeve_share - sleeve_notional
            room = min(name_room, sleeve_room)
            qty = int(room // price) if room > 0 else 0
            if qty < 1:
                reason = "no_room_name" if name_room <= sleeve_room else "no_room_sleeve"
                state = _note(
                    state,
                    _decision(
                        ticker,
                        side,
                        day,
                        reason,
                        name_room=float(max(name_room, Decimal("0"))),
                        sleeve_room=float(max(sleeve_room, Decimal("0"))),
                        price=float(price),
                    ),
                )
                continue
        try:
            instrument = find_moex_instrument(ticker)
            figi = getattr(instrument, "figi", "") or ""
        except Exception:  # noqa: BLE001
            state = _note(state, _decision(ticker, side, day, "no_instrument"))
            continue
        ack = post_sandbox_order(
            OrderRequest(
                ticker=ticker,
                side=side,
                qty=qty,
                type="market",
                client_order_id=str(uuid.uuid5(uuid.NAMESPACE_OID, key)),
            ),
            account_id=account_id,
            figi=figi,
        )
        prev_layers = [
            item for item in _layers(state.get("trades") or [], ticker) if item.get("side") == "buy"
        ]
        layer = len(prev_layers) + 1 if side == "buy" else 0
        old_qty = Decimal(str(position.get("qty") or "0"))
        old_avg = Decimal(str(position.get("avg_price") or price))
        if side == "buy":
            new_qty = old_qty + Decimal(qty)
            avg_after = (old_avg * old_qty + price * Decimal(qty)) / new_qty if new_qty else price
            sleeve_notional += price * Decimal(qty)
        else:
            avg_after = old_avg
        trade = {
            "ticker": ticker,
            "side": side,
            "qty": qty,
            "price": str(price),
            "ts": datetime.now(UTC).isoformat(),
            "layer": layer,
            "avg_after": str(avg_after),
            "broker_order_id": ack.broker_order_id,
        }
        state = remember_order(state, key, ack.broker_order_id, trade)
        state = _note(state, _decision(ticker, side, day, "sent", qty=qty, price=float(price)))
        save_state(state)
        placed += 1
    save_state(state)
    return placed


def _last_close(ticker: str) -> Decimal:
    from pathlib import Path

    path = Path(os.environ.get("CANDLE_DIR", "data/candles")) / f"{ticker}.csv"
    if not path.is_file():
        return Decimal("0")
    last = ""
    for line in path.read_text(encoding="utf-8").splitlines()[1:]:
        if line.strip():
            last = line
    if not last:
        return Decimal("0")
    parts = last.split(",")
    if len(parts) < 5:
        return Decimal("0")
    return Decimal(parts[4])


def chart(ticker: str) -> dict:
    from pathlib import Path

    state = load_state()
    symbol = ticker.strip().upper()
    path = Path(os.environ.get("CANDLE_DIR", "data/candles")) / f"{symbol}.csv"
    bars = []
    if path.is_file():
        lines = [line for line in path.read_text(encoding="utf-8").splitlines()[1:] if line.strip()]
        for line in lines[-80:]:
            parts = line.split(",")
            if len(parts) < 5:
                continue
            bars.append({"ts": parts[0][:10], "close": parts[4]})
    marks = [
        {"ts": row.get("ts"), "side": row.get("side"), "price": row.get("price"), "layer": row.get("layer")}
        for row in (state.get("trades") or [])
        if str(row.get("ticker") or "").upper() == symbol
    ]
    return {
        "ticker": symbol,
        "bars": bars,
        "marks": marks,
        "equity_curve": state.get("equity_curve") or [],
    }
