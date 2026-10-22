"""Рабочая песочница: мастер, лента, заявки. Боевой контур не вызывается."""

from __future__ import annotations

import logging
import os
import uuid
from datetime import UTC, datetime, time, timedelta
from decimal import Decimal
from time import monotonic, sleep

from app.broker.port import OrderRequest
from app.work.desk_state import (
    MAIN_DESK,
    SLEEVE,
    WORK_SLEEVES,
    already_sent,
    connect_strategy,
    desk_ids,
    empty_state,
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

log = logging.getLogger(__name__)

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


def sleeve_info(sleeve: str) -> dict:
    from app.alloc.plan import SLEEVE_HOWTO

    howto = SLEEVE_HOWTO.get(sleeve) or {}
    return {
        "id": sleeve,
        "title": howto.get("title") or sleeve,
        "signal": howto.get("signal") or "",
        "holds": howto.get("holds") or "",
        "rules": sleeve == SLEEVE,
    }


def desk_meta(state: dict) -> dict:
    info = sleeve_info(state.get("sleeve") or SLEEVE)
    return {
        "id": state.get("id") or MAIN_DESK,
        "name": state.get("name") or info["title"],
        "sleeve": info["id"],
        "strategy": info,
        "archived": bool(state.get("archived")),
    }


def _ranked_signals(signals: list[dict], state: dict) -> list[dict]:
    """Покупки — в том порядке, в каком их возьмёт песочница: по росту за 15 дней."""
    from datetime import date as _date

    from app.work.exits import day_bars, roc, strategy_for

    strategy = strategy_for(state.get("sleeve") or SLEEVE)
    lookback = int(getattr(strategy, "lookback", 15) or 15)
    out = []
    for row in signals:
        item = dict(row)
        if item.get("kind") == "buy" and item.get("day"):
            try:
                value = roc(day_bars(item["ticker"], _date.fromisoformat(item["day"])), lookback)
            except Exception:  # noqa: BLE001 — без силы покажем как есть
                value = None
            item["roc"] = float(value) if value is not None else None
        out.append(item)
    buys = [item for item in out if item.get("kind") == "buy"]
    buys.sort(key=lambda item: (item.get("roc") is None, -(item.get("roc") or 0), item["ticker"]))
    return buys + [item for item in out if item.get("kind") != "buy"]


def view(
    *,
    desk_id: str = MAIN_DESK,
    span: str = "day",
    names: dict[str, str] | None = None,
    signals: list[dict] | None = None,
) -> dict:
    state = load_state(desk_id)
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
    cards = position_cards(
        portfolio,
        trades=trades,
        name_cap=name_cap,
        names=names,
        rules=state.get("sleeve") == SLEEVE,
    )
    trades_view = _trades_view(trades, names or {})
    signals = _ranked_signals(signals or [], state)
    try:
        from app.work.exits import stale_holdings

        data_alerts = stale_holdings(_held(portfolio or {}).keys())
    except Exception:  # noqa: BLE001 — экран живёт и без проверки свечей
        log.exception("work view: stale check failed")
        data_alerts = []

    now = datetime.now(UTC)
    return {
        "sleeve": state.get("sleeve") or SLEEVE,
        "desk": desk_meta(state),
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
        "data_alerts": data_alerts,
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


def open_account(desk_id: str = MAIN_DESK) -> dict:
    if not token_ok():
        raise ValueError("TINKOFF_SANDBOX_TOKEN пуст на сервере")
    from app.broker.tinkoff import ensure_sandbox_pay_in, open_sandbox_account_id

    deposit = Decimal(os.environ.get("SANDBOX_DEPOSIT", "1000000"))
    account_id = open_sandbox_account_id()
    ensure_sandbox_pay_in(account_id, deposit)
    return choose_account(account_id, desk_id)


def pay_in(amount: str, desk_id: str = MAIN_DESK) -> dict:
    """Пополнить выбранный счёт песочницы игровыми рублями (SandboxPayIn)."""
    if not token_ok():
        raise ValueError("TINKOFF_SANDBOX_TOKEN пуст на сервере")
    state = load_state(desk_id)
    account_id = state.get("account_id") or ""
    if not account_id:
        raise ValueError("сначала выберите счёт песочницы")
    value = payin_value(amount)
    from app.broker.tinkoff import sandbox_pay_in_rub

    try:
        sandbox_pay_in_rub(account_id, value)
    except Exception as exc:  # noqa: BLE001
        raise ValueError(_public_error(exc)) from exc
    state = remember_payin(load_state(desk_id), value)
    save_state(state)
    return {"ok": True, "amount": format(value, "f")}


def _all_states(include_archived: bool = False) -> list[dict]:
    out = []
    for desk_id in desk_ids():
        try:
            state = load_state(desk_id)
        except ValueError:
            continue
        if state.get("archived") and not include_archived:
            continue
        out.append(state)
    return out


def _account_owner(account_id: str, *, skip: str) -> str:
    for state in _all_states():
        if state.get("id") != skip and state.get("account_id") == account_id:
            return desk_meta(state)["name"]
    return ""


def choose_account(account_id: str, desk_id: str = MAIN_DESK) -> dict:
    owner = _account_owner(account_id.strip(), skip=desk_id)
    if owner:
        raise ValueError(f"этот счёт уже занят песочницей «{owner}»")
    accounts = list_accounts()
    known = {row["broker_account_id"] for row in accounts}
    state = set_account(load_state(desk_id), account_id, known)
    save_state(state)
    return {"ok": True}


def attach_strategy(desk_id: str = MAIN_DESK) -> dict:
    state = connect_strategy(load_state(desk_id))
    save_state(state)
    return {"ok": True}


def create_desk(*, sleeve: str, name: str = "", deposit: str = "1000000") -> dict:
    """Новая песочница = новый счёт брокера + один дневной рукав."""
    if sleeve not in WORK_SLEEVES:
        raise ValueError("эту стратегию в песочницу пока не подключить")
    for state in _all_states():
        if state.get("sleeve") == sleeve:
            raise ValueError(f"«{desk_meta(state)['name']}» уже торгует этой стратегией")
    amount = payin_value(deposit)
    if not token_ok():
        raise ValueError("TINKOFF_SANDBOX_TOKEN пуст на сервере")
    from app.broker.tinkoff import open_sandbox_account_id, sandbox_pay_in_rub

    try:
        account_id = open_sandbox_account_id()
        sandbox_pay_in_rub(account_id, amount)
    except Exception as exc:  # noqa: BLE001
        raise ValueError(_public_error(exc)) from exc
    desk_id = f"{sleeve.replace('_', '-')}-{uuid.uuid4().hex[:6]}"
    title = (name or "").strip()[:60] or sleeve_info(sleeve)["title"]
    state = empty_state(desk_id, sleeve=sleeve, name=title)
    state.update(
        {
            "account_id": account_id,
            "strategy_connected": True,
            "created_at": datetime.now(UTC).isoformat(),
        }
    )
    save_state(state)
    return {"ok": True, "desk": desk_id}


def archive_desk(desk_id: str) -> dict:
    if desk_id == MAIN_DESK:
        raise ValueError("основную песочницу убрать нельзя")
    state = load_state(desk_id)
    state["archived"] = True
    state["enabled"] = False
    save_state(state)
    return {"ok": True}


def _drawdown(values: list[Decimal]) -> Decimal:
    peak = Decimal("0")
    worst = Decimal("0")
    for value in values:
        peak = max(peak, value)
        if peak > 0:
            worst = min(worst, value / peak - 1)
    return worst


def overview() -> dict:
    """Все песочницы рядом: результат без пополнений, просадка, сделки, кривая в % от старта."""
    now = datetime.now(UTC)
    desks = []
    used = set()
    for state in _all_states():
        meta = desk_meta(state)
        used.add(meta["sleeve"])
        portfolio = state.get("portfolio") or {}
        curve = state.get("equity_curve") or []
        equity = equity_at_market(portfolio) if portfolio else Decimal("0")
        if equity <= 0 and curve:
            try:
                equity = Decimal(str(curve[-1].get("equity")))
            except Exception:  # noqa: BLE001
                equity = Decimal("0")
        first, _day_first, first_ts, _day_ts = _equity_points(curve)
        payins = state.get("payins") or []
        base = first + payins_after(payins, first_ts) if first is not None else None
        pnl = equity - base if base is not None and equity > 0 else None
        values = []
        points = []
        for row in curve_slice(curve, "all", now):
            try:
                value = Decimal(str(row.get("equity")))
            except Exception:  # noqa: BLE001
                continue
            ts = _parse_ts(row.get("ts") or "")
            flow = payins_after(payins, first_ts) - payins_after(payins, ts)
            values.append(value - flow)
            if first:
                points.append({"ts": row.get("ts"), "pct": float((value - flow) / first - 1)})
        sleeve_share = Decimal(str(state.get("sleeve_share") or "0.40"))
        invested = equity - Decimal(str(portfolio.get("cash") or "0")) if portfolio else Decimal("0")
        sleeve_rub = equity * sleeve_share
        desks.append(
            {
                **meta,
                "account_id": state.get("account_id") or "",
                "enabled": bool(state.get("enabled")),
                "ready": all(step["ok"] for step in steps(state, token_ok=True)[:-1]),
                "equity": float(equity),
                "pnl": float(pnl) if pnl is not None else None,
                "pnl_pct": float(pnl / base) if pnl is not None and base else None,
                "drawdown": float(_drawdown(values)) if values else None,
                "trades": len(state.get("trades") or []),
                "positions": sum(
                    1
                    for row in (portfolio.get("positions") or [])
                    if not is_money_row(row) and Decimal(str(row.get("qty") or "0")) > 0
                ),
                "sleeve_fill": float(invested / sleeve_rub) if sleeve_rub > 0 else 0.0,
                "curve": points,
            }
        )
    return {
        "desks": desks,
        "strategies": [
            {**sleeve_info(sleeve), "used": sleeve in used} for sleeve in WORK_SLEEVES
        ],
        "live": live_view(),
        "server_time": now.isoformat(),
    }


def store_params(*, sleeve_share: str, name_cap: str, desk_id: str = MAIN_DESK) -> dict:
    state = save_params(load_state(desk_id), sleeve_share=sleeve_share, name_cap=name_cap)
    save_state(state)
    return {
        "ok": True,
        "sleeve_share": state["sleeve_share"],
        "name_cap": state["name_cap"],
    }


def switch(enabled: bool, desk_id: str = MAIN_DESK) -> dict:
    state = set_enabled(load_state(desk_id), enabled)
    save_state(state)
    return {"ok": True, "enabled": bool(state.get("enabled"))}


def work_tickers(state: dict | None = None) -> list[str]:
    states = [state] if state is not None else _all_states()
    names: list[str] = []
    for item in states:
        portfolio = item.get("portfolio") or {}
        for row in portfolio.get("positions") or []:
            if is_money_row(row):
                continue
            ticker = str(row.get("ticker") or "").upper()
            if ticker and ticker not in names:
                names.append(ticker)
        for trade in item.get("trades") or []:
            ticker = str(trade.get("ticker") or "").upper()
            if ticker and ticker not in names:
                names.append(ticker)
    return names[:WORK_TICKERS_LIMIT]


def refresh_tape() -> int:
    """Отметка equity по рынку + короткие дневки рабочих тикеров."""
    from pathlib import Path

    from app.ops.refresh_candles import refresh

    if token_ok():
        for state in _all_states():
            if not state.get("account_id"):
                continue
            try:
                portfolio = read_portfolio(state["account_id"])
                equity = equity_at_market(portfolio)
                save_state(remember_mark(state, equity=str(equity), portfolio=portfolio))
            except Exception:  # noqa: BLE001
                continue
    tickers = work_tickers()
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
    """Каждая песочница торгует только сигналами своего рукава. Отказы пишем в decisions."""
    placed = 0
    for state in _all_states():
        try:
            placed += _place_for_desk(state, rows)
        except Exception:  # noqa: BLE001 — одна песочница не роняет остальные
            log.exception("work desk %s orders failed", state.get("id"))
    return placed


def _held(portfolio: dict) -> dict[str, dict]:
    return {
        str(row.get("ticker") or "").upper(): row
        for row in (portfolio.get("positions") or [])
        if not is_money_row(row) and Decimal(str(row.get("qty") or "0")) > 0
    }


def plan_orders(
    state: dict, rows: list, held: dict[str, dict]
) -> list[tuple[str, str, str, Decimal | None]]:
    """Заявки дня как в бэктесте: (ticker, side, day, roc).

    Держимые бумаги — только выход, без доливок (у стратегий дня их нет).
    Новые входы — по убыванию роста за 15 дней: мест меньше, чем кандидатов.
    Продажи первыми: освобождают место рукава под покупки.
    """
    from app.broker.moex_candles import MOSCOW
    from app.ops.refresh_candles import bar_day
    from app.work.exits import day_bars, entry_day, held_exit, roc, strategy_for

    sleeve = state.get("sleeve") or SLEEVE
    mine = [row for row in rows if getattr(row, "sleeve", "") == sleeve and row.ts]
    if not mine:
        return []
    day = max(bar_day(row) for row in mine)
    day_key = day.isoformat()
    strategy = strategy_for(sleeve)
    lookback = int(getattr(strategy, "lookback", 15) or 15)
    seen = {str(row.ticker or "").upper(): row for row in mine if bar_day(row) == day}
    sells: list[tuple[str, str, str, Decimal | None]] = []
    for ticker, position in held.items():
        if ticker not in seen:
            continue
        bars = day_bars(ticker, day)
        kind = seen[ticker].kind
        if strategy is not None and kind not in {"sell", "exit"}:
            entry = Decimal(str(position.get("avg_price") or "0")) or mark_price(position)
            kind = held_exit(
                strategy,
                ticker,
                bars,
                entry_price=entry,
                entry_day=entry_day(state.get("trades") or [], ticker, MOSCOW),
            ) or ""
        if kind in {"sell", "exit"}:
            sells.append((ticker, "sell", day_key, roc(bars, lookback)))
    buys = []
    for ticker, row in seen.items():
        if row.kind != "buy" or ticker in held:
            continue
        buys.append((ticker, "buy", day_key, roc(day_bars(ticker, day), lookback)))
    buys.sort(key=lambda item: (item[3] is None, -(item[3] or 0), item[0]))
    return sells + buys


def _note_stale(state: dict, rows: list, held: dict[str, dict]) -> dict:
    """Держим бумагу, а свечи за день решения нет: продажу не решаем, поднимаем тревогу."""
    from app.ops.refresh_candles import bar_day
    from app.work.exits import stale_holdings

    sleeve = state.get("sleeve") or SLEEVE
    mine = [row for row in rows if getattr(row, "sleeve", "") == sleeve and row.ts]
    if not mine or not held:
        return state
    day = max(bar_day(row) for row in mine)
    stale = stale_holdings(held.keys(), day)
    for item in stale:
        state = _note(
            state,
            _decision(
                item["ticker"],
                "sell",
                day.isoformat(),
                "stale_data",
                last_day=item["last_day"],
                days_behind=item["days_behind"],
            ),
        )
    if stale:
        names = ", ".join(
            f"{item['ticker']} (последняя {item['last_day'] or 'нет'})" for item in stale
        )
        log.warning("work desk %s stale holdings: %s", state.get("id"), names)
        try:
            from app.ops.telegram import alert_data, send_telegram

            alert_data(
                f"Песочница «{state.get('name') or state.get('id')}»: нет свечей "
                f"за {day.isoformat()} по бумагам в портфеле — {names}. "
                "Продажа по ним не проверена.",
                send=send_telegram,
            )
        except Exception:  # noqa: BLE001 — уведомление не мешает заявкам
            log.exception("stale holdings alert failed")
    return state


# Вход меньше половины доли на бумагу — «крошка» на остатке бюджета: не покупаем.
MIN_BUY_OF_CAP = Decimal("0.5")
ORDER_PACE_SEC = 0.6
ORDER_RETRIES = 5
_last_order_at = 0.0


def _too_small(ticker, day, price, qty, min_buy, strength) -> dict:
    return _decision(
        ticker,
        "buy",
        day,
        "too_small",
        price=float(price),
        amount=float(price * qty),
        min_amount=float(min_buy),
        roc=float(strength) if strength is not None else None,
    )


def _rate_limited(exc: Exception) -> float | None:
    """Секунды до сброса лимита брокера или None, если ошибка не про лимит."""
    if "RESOURCE_EXHAUSTED" not in repr(exc):
        return None
    meta = exc.args[2] if len(exc.args) > 2 else None
    try:
        return max(1.0, float(getattr(meta, "ratelimit_reset", 1) or 1))
    except (TypeError, ValueError):
        return 1.0


def _post_paced(post, order, **kwargs):
    """Песочница брокера пускает 2 заявки в секунду; client_order_id делает повтор безопасным."""
    global _last_order_at
    for attempt in range(ORDER_RETRIES):
        wait = _last_order_at + ORDER_PACE_SEC - monotonic()
        if wait > 0:
            sleep(wait)
        _last_order_at = monotonic()
        try:
            return post(order, **kwargs)
        except Exception as exc:  # noqa: BLE001
            reset = _rate_limited(exc)
            if reset is None or attempt == ORDER_RETRIES - 1:
                raise
            sleep(reset)
    raise RuntimeError("unreachable")


def _place_for_desk(state: dict, rows: list) -> int:
    sleeve = state.get("sleeve") or SLEEVE
    account_id = str(state.get("account_id") or "")
    live = bool(state.get("enabled") and account_id and token_ok())
    portfolio = state.get("portfolio") or {}
    if live and not portfolio:
        try:
            portfolio = read_portfolio(account_id)
        except Exception:  # noqa: BLE001
            return 0
    held = _held(portfolio)
    state = _note_stale(state, rows, held)
    wanted = plan_orders(state, rows, held)
    if not wanted:
        save_state(state)
        return 0

    if not live:
        status = "disabled" if not state.get("enabled") else "no_account"
        for ticker, side, day, _roc in wanted:
            state = _note(state, _decision(ticker, side, day, status))
        save_state(state)
        return 0

    equity = _equity(portfolio)
    sleeve_share = Decimal(str(state["sleeve_share"]))
    name_cap = Decimal(str(state["name_cap"]))
    if name_cap >= Decimal("1") or sleeve_share >= Decimal("1") or name_cap > sleeve_share:
        return 0
    sleeve_notional = Decimal("0")
    for row in held.values():
        sleeve_notional += Decimal(str(row.get("qty") or "0")) * mark_price(row)
    placed = 0
    min_buy = equity * name_cap * MIN_BUY_OF_CAP
    from app.broker.tinkoff import find_moex_instrument, post_sandbox_order

    for ticker, side, day, strength in wanted:
        key = order_key(ticker, day, side, sleeve)
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
                        roc=float(strength) if strength is not None else None,
                    ),
                )
                continue
            if price * qty < min_buy:
                state = _note(state, _too_small(ticker, day, price, qty, min_buy, strength))
                continue
        try:
            instrument = find_moex_instrument(ticker)
            figi = getattr(instrument, "figi", "") or ""
        except Exception:  # noqa: BLE001
            state = _note(state, _decision(ticker, side, day, "no_instrument"))
            continue
        lot = max(int(getattr(instrument, "lot", 1) or 1), 1)
        lots = qty // lot
        if lots < 1:
            state = _note(
                state, _decision(ticker, side, day, "below_lot", lot=lot, price=float(price))
            )
            continue
        qty = lots * lot
        if side == "buy" and price * qty < min_buy:
            state = _note(state, _too_small(ticker, day, price, qty, min_buy, strength))
            continue
        try:
            ack = _post_paced(
                post_sandbox_order,
                OrderRequest(
                    ticker=ticker,
                    side=side,
                    qty=lots,
                    type="market",
                    client_order_id=str(uuid.uuid5(uuid.NAMESPACE_OID, key)),
                ),
                account_id=account_id,
                figi=figi,
            )
        except Exception as exc:  # noqa: BLE001 — одна бумага не роняет остальные
            log.warning("work desk %s order %s failed: %s", state.get("id"), key, exc)
            state = _note(state, _decision(ticker, side, day, "broker_error"))
            continue
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
            sleeve_notional -= old_qty * price
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
        state = _note(
            state,
            _decision(
                ticker,
                side,
                day,
                "sent",
                qty=qty,
                price=float(price),
                roc=float(strength) if strength is not None else None,
            ),
        )
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


def chart(ticker: str, desk_id: str = MAIN_DESK) -> dict:
    from pathlib import Path

    state = load_state(desk_id)
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
