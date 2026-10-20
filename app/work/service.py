"""Рабочая песочница: мастер, лента, заявки. Боевой контур не вызывается."""

from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime
from decimal import Decimal

from app.broker.port import OrderRequest
from app.work.desk_state import (
    SLEEVE,
    already_sent,
    connect_strategy,
    load_state,
    order_key,
    remember_mark,
    remember_order,
    save_state,
    set_account,
    set_enabled,
    save_params,
    steps,
)

WORK_TICKERS_LIMIT = 40


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
    from app.broker.tinkoff import make_client
    from app.broker.sandbox_snapshot import normalize_account

    with make_client() as client:
        accounts = list(client.sandbox.get_sandbox_accounts().accounts)
    return [normalize_account(item) for item in accounts]


def read_portfolio(account_id: str) -> dict:
    from app.broker.tinkoff import make_client
    from app.broker.sandbox_snapshot import normalize_portfolio

    with make_client() as client:
        portfolio = client.sandbox.get_sandbox_portfolio(account_id=account_id)
    view = normalize_portfolio(portfolio)
    view["account_id"] = account_id
    return view


def view() -> dict:
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
    if ok and state.get("account_id"):
        try:
            portfolio = read_portfolio(state["account_id"])
        except Exception as exc:  # noqa: BLE001
            error = error or _public_error(exc)
    return {
        "sleeve": SLEEVE,
        "steps": steps(state, token_ok=ok),
        "account_id": state.get("account_id") or "",
        "accounts": accounts,
        "sleeve_share": state.get("sleeve_share"),
        "name_cap": state.get("name_cap"),
        "enabled": bool(state.get("enabled")),
        "portfolio": portfolio,
        "trades": state.get("trades") or [],
        "equity_curve": state.get("equity_curve") or [],
        "error": error,
    }


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


def choose_account(account_id: str) -> dict:
    accounts = list_accounts()
    known = {row["broker_account_id"] for row in accounts}
    state = set_account(load_state(), account_id, known)
    save_state(state)
    return view()


def attach_strategy() -> dict:
    state = connect_strategy(load_state())
    save_state(state)
    return view()


def store_params(*, sleeve_share: str, name_cap: str) -> dict:
    state = save_params(load_state(), sleeve_share=sleeve_share, name_cap=name_cap)
    save_state(state)
    return view()


def switch(enabled: bool) -> dict:
    state = set_enabled(load_state(), enabled)
    save_state(state)
    return view()


def work_tickers(state: dict | None = None) -> list[str]:
    state = state if state is not None else load_state()
    names: list[str] = []
    portfolio = state.get("portfolio") or {}
    for row in portfolio.get("positions") or []:
        ticker = str(row.get("ticker") or "").upper()
        if ticker and ticker not in names:
            names.append(ticker)
    for trade in state.get("trades") or []:
        ticker = str(trade.get("ticker") or "").upper()
        if ticker and ticker not in names:
            names.append(ticker)
    return names[:WORK_TICKERS_LIMIT]


def refresh_tape() -> int:
    """Дописать короткие дневки рабочих тикеров. Полные 730 дней сюда не входят."""
    from app.ops.refresh_candles import refresh

    state = load_state()
    if token_ok() and state.get("account_id"):
        try:
            portfolio = read_portfolio(state["account_id"])
            equity = _equity(portfolio)
            state = remember_mark(state, equity=str(equity), portfolio=portfolio)
            save_state(state)
        except Exception:
            portfolio = state.get("portfolio") or {}
    tickers = work_tickers(state)
    if not tickers:
        return 0
    root = __import__("os").environ.get("CANDLE_DIR", "data/candles")
    from pathlib import Path

    written = 0
    for ticker in tickers:
        try:
            refresh([ticker], days=5, tf="1d", root=Path(root))
            written += 1
        except Exception:
            continue
    return written


def _equity(portfolio: dict) -> Decimal:
    cash = Decimal(str(portfolio.get("cash") or "0"))
    total = cash
    for row in portfolio.get("positions") or []:
        qty = Decimal(str(row.get("qty") or "0"))
        avg = Decimal(str(row.get("avg_price") or "0"))
        if qty > 0 and avg > 0:
            total += qty * avg
    return total


def _layers(trades: list[dict], ticker: str) -> list[dict]:
    return [row for row in trades if str(row.get("ticker") or "").upper() == ticker]


def place_signals(rows: list) -> int:
    """Заявки только для включённого мастера и abs_momentum_4."""
    state = load_state()
    if not state.get("enabled"):
        return 0
    account_id = str(state.get("account_id") or "")
    if not account_id or not token_ok():
        return 0
    portfolio = state.get("portfolio") or {}
    if not portfolio:
        try:
            portfolio = read_portfolio(account_id)
        except Exception:
            return 0
    equity = _equity(portfolio)
    sleeve_share = Decimal(str(state["sleeve_share"]))
    name_cap = Decimal(str(state["name_cap"]))
    if name_cap >= Decimal("1") or sleeve_share >= Decimal("1") or name_cap > sleeve_share:
        return 0
    held = {
        str(row.get("ticker") or "").upper(): row
        for row in (portfolio.get("positions") or [])
    }
    sleeve_notional = Decimal("0")
    for row in held.values():
        qty = Decimal(str(row.get("qty") or "0"))
        avg = Decimal(str(row.get("avg_price") or "0"))
        if qty > 0 and avg > 0:
            sleeve_notional += qty * avg
    placed = 0
    from app.broker.tinkoff import find_moex_instrument, post_sandbox_order

    for row in rows:
        if getattr(row, "sleeve", "") != SLEEVE:
            continue
        side = "sell" if row.kind in {"sell", "exit"} else "buy" if row.kind == "buy" else ""
        if not side:
            continue
        ticker = str(row.ticker or "").upper()
        day = row.ts.astimezone(UTC).date().isoformat() if row.ts else datetime.now(UTC).date().isoformat()
        key = order_key(ticker, day, side)
        if already_sent(state, key):
            continue
        position = held.get(ticker) or {}
        price = Decimal(str(position.get("avg_price") or "0"))
        if price <= 0:
            price = _last_close(ticker)
        if price <= 0:
            continue
        if side == "sell":
            qty = int(Decimal(str(position.get("qty") or "0")))
        else:
            name_room = equity * name_cap - Decimal(str(position.get("qty") or "0")) * price
            sleeve_room = equity * sleeve_share - sleeve_notional
            room = min(name_room, sleeve_room)
            qty = int(room // price) if room > 0 else 0
        if qty < 1:
            continue
        try:
            instrument = find_moex_instrument(ticker)
            figi = getattr(instrument, "figi", "") or ""
        except Exception:
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
        prev_layers = [item for item in _layers(state.get("trades") or [], ticker) if item.get("side") == "buy"]
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
        save_state(state)
        placed += 1
    return placed


def _last_close(ticker: str) -> Decimal:
    import os
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
    import os
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
