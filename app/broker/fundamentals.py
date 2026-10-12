"""Снимок GetAssetFundamentals: одна строка на тикер в `fundamentals`."""

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from app.models import Fundamental

def _metric(stat: Any, name: str) -> float | None:
    value = getattr(stat, name, None)
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def stat_payload(stat: Any) -> dict:
    payload: dict[str, Any] = {}
    for name in (
        "asset_uid",
        "currency",
        "market_capitalization",
        "pe_ratio_ttm",
        "price_to_book_ttm",
        "eps_ttm",
        "roe",
        "free_float",
        "dividend_yield_daily_ttm",
    ):
        value = getattr(stat, name, None)
        if isinstance(value, datetime):
            payload[name] = value.isoformat()
        elif value is not None:
            payload[name] = value
    return payload


def snapshot_ticker(
    ticker: str,
    stat: Any,
    *,
    ts: datetime | None = None,
) -> Fundamental:
    return Fundamental(
        ticker=ticker.strip().upper(),
        asset_uid=getattr(stat, "asset_uid", "") or "",
        ts=ts or datetime.now(UTC),
        pe_ratio_ttm=_metric(stat, "pe_ratio_ttm"),
        price_to_book_ttm=_metric(stat, "price_to_book_ttm"),
        eps_ttm=_metric(stat, "eps_ttm"),
        market_capitalization=_metric(stat, "market_capitalization"),
        raw=stat_payload(stat),
    )


def merge_fundamental(
    existing: Fundamental | None, incoming: Fundamental
) -> Fundamental:
    if existing is None:
        return incoming
    existing.asset_uid = incoming.asset_uid
    existing.ts = incoming.ts
    existing.pe_ratio_ttm = incoming.pe_ratio_ttm
    existing.price_to_book_ttm = incoming.price_to_book_ttm
    existing.eps_ttm = incoming.eps_ttm
    existing.market_capitalization = incoming.market_capitalization
    existing.raw = incoming.raw
    return existing


def pair_stats(
    stats: Sequence[Any],
    ticker_by_asset: dict[str, str],
) -> list[tuple[str, Any]]:
    paired: list[tuple[str, Any]] = []
    for stat in stats:
        ticker = ticker_by_asset.get(getattr(stat, "asset_uid", "") or "")
        if ticker:
            paired.append((ticker, stat))
    return paired


def apply_snapshots(
    existing: Sequence[Fundamental],
    items: Sequence[tuple[str, Any]],
    *,
    ts: datetime | None = None,
) -> list[Fundamental]:
    by_ticker = {row.ticker: row for row in existing}
    for ticker, stat in items:
        snap = snapshot_ticker(ticker, stat, ts=ts)
        by_ticker[snap.ticker] = merge_fundamental(by_ticker.get(snap.ticker), snap)
    return list(by_ticker.values())
