"""Last prices пачкой → dict ticker→price."""

from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import Any

from tinkoff.invest.utils import quotation_to_decimal


def last_price_map(
    raw: Sequence[Any],
    *,
    ticker_by_figi: Mapping[str, str] | None = None,
    ticker_by_uid: Mapping[str, str] | None = None,
) -> dict[str, Decimal]:
    by_figi = ticker_by_figi or {}
    by_uid = ticker_by_uid or {}
    out: dict[str, Decimal] = {}
    for item in raw:
        figi = getattr(item, "figi", "") or ""
        uid = getattr(item, "instrument_uid", "") or ""
        ticker = by_figi.get(figi) or by_uid.get(uid)
        if not ticker or getattr(item, "price", None) is None:
            continue
        out[ticker] = quotation_to_decimal(item.price)
    return out
