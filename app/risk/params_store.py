"""Сохраняемые риск-параметры (макс. доля на бумагу)."""

from __future__ import annotations

import json
import os
from decimal import Decimal
from pathlib import Path

from app.strategy.size import DEFAULT_NAME_SHARE

DEFAULT_PARAMS_PATH = "/var/www/i_datagon_ru_usr/data/risk_params.json"
MIN_NAME_SHARE = Decimal("0.01")
MAX_NAME_SHARE = Decimal("0.50")


def params_path() -> Path:
    raw = os.environ.get("RISK_PARAMS_PATH")
    if raw:
        return Path(raw)
    weights = os.environ.get("SLEEVE_WEIGHTS_PATH", "")
    if weights:
        return Path(weights).with_name("risk_params.json")
    local = Path("data/risk_params.json")
    if local.parent.exists() or not Path(DEFAULT_PARAMS_PATH).parent.exists():
        return local
    return Path(DEFAULT_PARAMS_PATH)


def _clamp_name_share(value: Decimal) -> Decimal:
    if value < MIN_NAME_SHARE:
        return MIN_NAME_SHARE
    if value > MAX_NAME_SHARE:
        return MAX_NAME_SHARE
    return value


def load_name_share() -> Decimal:
    path = params_path()
    if path.exists():
        try:
            raw = json.loads(path.read_text())
            if isinstance(raw, dict) and raw.get("name_share") is not None:
                return _clamp_name_share(Decimal(str(raw["name_share"])))
        except (OSError, json.JSONDecodeError, ArithmeticError):
            pass
    env = os.environ.get("NAME_SHARE")
    if env:
        try:
            return _clamp_name_share(Decimal(str(env)))
        except ArithmeticError:
            pass
    return Decimal(DEFAULT_NAME_SHARE)


def save_name_share(name_share: Decimal | float | str) -> Path:
    value = _clamp_name_share(Decimal(str(name_share)))
    path = params_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"name_share": float(value)}
    if path.exists():
        try:
            existing = json.loads(path.read_text())
            if isinstance(existing, dict):
                existing["name_share"] = float(value)
                payload = existing
        except (OSError, json.JSONDecodeError):
            pass
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    return path
