"""Сохранённые веса рукавов (бюджеты). Equal-weight, если файла нет."""

from __future__ import annotations

import json
import os
from collections.abc import Sequence
from decimal import Decimal
from pathlib import Path

from app.alloc.capital import allocate

DEFAULT_WEIGHTS_PATH = "/var/www/i_datagon_ru_usr/data/sleeve_weights.json"


def weights_path() -> Path:
    raw = os.environ.get("SLEEVE_WEIGHTS_PATH")
    if raw:
        return Path(raw)
    proposals = os.environ.get("PROPOSALS_PATH", "")
    if proposals:
        return Path(proposals).with_name("sleeve_weights.json")
    local = Path("data/sleeve_weights.json")
    if local.parent.exists() or not Path(DEFAULT_WEIGHTS_PATH).parent.exists():
        return local
    return Path(DEFAULT_WEIGHTS_PATH)


def load_weights(sleeves: Sequence[str]) -> dict[str, Decimal]:
    names = list(sleeves)
    fallback = allocate(names)
    path = weights_path()
    if not path.exists():
        return fallback
    try:
        raw = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return fallback
    if not isinstance(raw, dict):
        return fallback
    out: dict[str, Decimal] = {}
    for name in names:
        value = raw.get(name)
        if value is None:
            return fallback
        out[name] = Decimal(str(value))
    total = sum(out.values(), Decimal("0"))
    if total <= 0:
        return fallback
    if "cash" in raw:
        if total > 1:
            return fallback
        return out
    # нормализуем на случай округления
    return {name: (weight / total) for name, weight in out.items()}


def save_weights(weights: dict[str, Decimal | float | str]) -> Path:
    path = weights_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {name: float(Decimal(str(value))) for name, value in weights.items()}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    return path
