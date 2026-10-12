"""Сохраняемые риск-параметры (макс. доля на бумагу)."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from app.risk.daily import DEFAULT_DAILY_LOSS
from app.risk.portfolio import DEFAULT_GROSS_LIMIT, DEFAULT_MAX_DRAWDOWN
from app.risk.size import DEFAULT_TRADE_RISK_SHARE
from app.strategy.size import DEFAULT_NAME_SHARE

DEFAULT_PARAMS_PATH = "/var/www/i_datagon_ru_usr/data/risk_params.json"
MIN_NAME_SHARE = Decimal("0.01")
MAX_NAME_SHARE = Decimal("0.50")


@dataclass(frozen=True)
class RiskPolicy:
    version: int = 1
    name_share: Decimal = DEFAULT_NAME_SHARE
    trade_risk_share: Decimal = DEFAULT_TRADE_RISK_SHARE
    gross_limit: Decimal = DEFAULT_GROSS_LIMIT
    max_drawdown: Decimal = DEFAULT_MAX_DRAWDOWN
    daily_loss: Decimal = DEFAULT_DAILY_LOSS

    def snapshot(self) -> dict:
        return {
            key: float(value) if isinstance(value, Decimal) else value
            for key, value in asdict(self).items()
        }


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


def load_risk_policy() -> RiskPolicy:
    path = params_path()
    if path.exists():
        try:
            raw = json.loads(path.read_text())
            if isinstance(raw, dict):
                return RiskPolicy(
                    version=max(int(raw.get("version", 1)), 1),
                    name_share=_clamp_name_share(
                        Decimal(str(raw.get("name_share", DEFAULT_NAME_SHARE)))
                    ),
                    trade_risk_share=Decimal(
                        str(raw.get("trade_risk_share", DEFAULT_TRADE_RISK_SHARE))
                    ),
                    gross_limit=Decimal(
                        str(raw.get("gross_limit", DEFAULT_GROSS_LIMIT))
                    ),
                    max_drawdown=Decimal(
                        str(raw.get("max_drawdown", DEFAULT_MAX_DRAWDOWN))
                    ),
                    daily_loss=Decimal(
                        str(raw.get("daily_loss", DEFAULT_DAILY_LOSS))
                    ),
                )
        except (OSError, json.JSONDecodeError, ArithmeticError):
            pass
    env = os.environ.get("NAME_SHARE")
    if env:
        try:
            return RiskPolicy(name_share=_clamp_name_share(Decimal(str(env))))
        except ArithmeticError:
            pass
    return RiskPolicy()


def load_name_share() -> Decimal:
    return load_risk_policy().name_share


def load_risk_policy_history() -> list[dict]:
    path = params_path()
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return []
    history = raw.get("history") if isinstance(raw, dict) else None
    return list(history) if isinstance(history, list) else []


def save_risk_policy(
    policy: RiskPolicy,
    *,
    expected_version: int | None = None,
) -> RiskPolicy:
    current = load_risk_policy()
    if expected_version is not None and current.version != expected_version:
        raise ValueError("risk_policy_version_conflict")
    if not MIN_NAME_SHARE <= policy.name_share <= MAX_NAME_SHARE:
        raise ValueError("name_share")
    for name in (
        "trade_risk_share",
        "gross_limit",
        "max_drawdown",
        "daily_loss",
    ):
        value = Decimal(getattr(policy, name))
        if value <= 0 or value > 1:
            raise ValueError(name)
    saved = replace(policy, version=current.version + 1)
    path = params_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    changed_at = datetime.now(UTC).isoformat()
    history = load_risk_policy_history()
    history.append(
        {
            "version": saved.version,
            "previous_version": current.version,
            "changed_at": changed_at,
            "policy": saved.snapshot(),
        }
    )
    payload = {
        **saved.snapshot(),
        "updated_at": changed_at,
        "history": history,
    }
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)
    return saved


def save_name_share(name_share: Decimal | float | str) -> Path:
    current = load_risk_policy()
    save_risk_policy(
        replace(current, name_share=_clamp_name_share(Decimal(str(name_share)))),
        expected_version=current.version,
    )
    return params_path()
