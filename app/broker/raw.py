"""Сырой jsonb ответа брокера для orders/fills."""

from collections.abc import Sequence
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from types import SimpleNamespace
from typing import Any

from app.models import Fill, Order


def as_raw(payload: Any) -> dict:
    converted = _jsonable(payload)
    if isinstance(converted, dict):
        return converted
    return {"value": converted}


def attach_order_raw(order: Order, payload: Any) -> Order:
    order.raw = as_raw(payload)
    return order


def attach_fill_raw(fill: Fill, payload: Any) -> Fill:
    fill.raw = as_raw(payload)
    return fill


def last_order_view(orders: Sequence[Order]) -> dict:
    """Последняя заявка: поля + сырой кусок брокера."""
    last = max(orders, key=lambda row: row.created_at)
    return {
        "client_order_id": last.client_order_id,
        "broker_order_id": last.broker_order_id,
        "status": last.status,
        "raw": last.raw or {},
    }


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Enum):
        return value.name
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {key: _jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, SimpleNamespace):
        data = vars(value)
        if list(data) == ["name"] and isinstance(data["name"], str):
            return data["name"]
        return {key: _jsonable(item) for key, item in data.items()}
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    name = getattr(value, "name", None)
    if isinstance(name, str):
        return name
    if hasattr(value, "__dict__"):
        return {
            key: _jsonable(item)
            for key, item in vars(value).items()
            if not key.startswith("_")
        }
    return str(value)
