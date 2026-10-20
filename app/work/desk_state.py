"""Состояние рабочей песочницы. Токена брокера здесь нет."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

SLEEVE = "abs_momentum_4"


def desk_path() -> Path:
    raw = os.environ.get("WORK_DESK_PATH", "").strip()
    if raw:
        return Path(raw)
    return Path("data/work_desk.json")


def empty_state() -> dict:
    return {
        "account_id": "",
        "strategy_connected": False,
        "sleeve_share": "0.40",
        "name_cap": "0.10",
        "params_saved": False,
        "enabled": False,
        "sent": {},
        "trades": [],
        "equity_curve": [],
        "portfolio": None,
    }


def load_state() -> dict:
    path = desk_path()
    if not path.is_file():
        return empty_state()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return empty_state()
    if not isinstance(raw, dict):
        return empty_state()
    state = empty_state()
    state.update({key: raw.get(key, state[key]) for key in state})
    if not isinstance(state["sent"], dict):
        state["sent"] = {}
    if not isinstance(state["trades"], list):
        state["trades"] = []
    if not isinstance(state["equity_curve"], list):
        state["equity_curve"] = []
    return state


def save_state(state: dict) -> None:
    path = desk_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _share(raw: str | float | Decimal) -> Decimal:
    value = Decimal(str(raw))
    if not Decimal("0") < value < Decimal("1"):
        raise ValueError("доля должна быть между 0 и 100%, не включая 100%")
    return value


def set_account(state: dict, account_id: str, known: set[str]) -> dict:
    account = account_id.strip()
    if account not in known:
        raise ValueError("счёта нет в песочнице")
    state = dict(state)
    if state.get("account_id") != account:
        state["strategy_connected"] = False
        state["params_saved"] = False
        state["enabled"] = False
    state["account_id"] = account
    return state


def connect_strategy(state: dict) -> dict:
    if not state.get("account_id"):
        raise ValueError("сначала выберите счёт")
    state = dict(state)
    state["strategy_connected"] = True
    return state


def save_params(state: dict, *, sleeve_share: str, name_cap: str) -> dict:
    if not state.get("strategy_connected"):
        raise ValueError("сначала подключите Абс. моментум-4")
    sleeve = _share(sleeve_share)
    cap = _share(name_cap)
    if cap > sleeve:
        raise ValueError("потолок на бумагу не больше доли рукава")
    state = dict(state)
    state["sleeve_share"] = format(sleeve, "f")
    state["name_cap"] = format(cap, "f")
    state["params_saved"] = True
    return state


def set_enabled(state: dict, enabled: bool) -> dict:
    if enabled and not ready_to_enable(state):
        raise ValueError("сначала сохраните долю счёта")
    state = dict(state)
    state["enabled"] = bool(enabled)
    return state


def ready_to_enable(state: dict) -> bool:
    return bool(
        state.get("account_id")
        and state.get("strategy_connected")
        and state.get("params_saved")
    )


def steps(state: dict, *, token_ok: bool) -> list[dict]:
    account_ok = token_ok and bool(state.get("account_id"))
    strategy_ok = account_ok and bool(state.get("strategy_connected"))
    params_ok = strategy_ok and bool(state.get("params_saved"))
    enabled_ok = params_ok and bool(state.get("enabled"))
    return [
        {"id": "token", "title": "Токен на сервере", "ok": token_ok},
        {"id": "account", "title": "Счёт выбран", "ok": account_ok},
        {"id": "strategy", "title": "Абс. моментум-4", "ok": strategy_ok},
        {"id": "params", "title": "Проценты заданы", "ok": params_ok},
        {"id": "enabled", "title": "Заявки включены", "ok": enabled_ok},
    ]


def order_key(ticker: str, day: str, side: str) -> str:
    return f"{SLEEVE}|{ticker.strip().upper()}|{day}|{side}"


def already_sent(state: dict, key: str) -> bool:
    return key in (state.get("sent") or {})


def remember_order(state: dict, key: str, broker_order_id: str, trade: dict) -> dict:
    state = dict(state)
    sent = dict(state.get("sent") or {})
    sent[key] = broker_order_id
    trades = list(state.get("trades") or [])
    trades.append(trade)
    state["sent"] = sent
    state["trades"] = trades[-400:]
    return state


def remember_mark(state: dict, *, equity: str, portfolio: dict) -> dict:
    state = dict(state)
    curve = list(state.get("equity_curve") or [])
    curve.append({"ts": datetime.now(UTC).isoformat(), "equity": equity})
    state["equity_curve"] = curve[-500:]
    state["portfolio"] = portfolio
    return state
