"""Джоба: обновить снимки GetAssetFundamentals по инструментам вселенной."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable, Sequence
from datetime import UTC, datetime

from app.broker.fundamentals import apply_snapshots, pair_stats
from app.db import get_sessionmaker
from app.models import Fundamental, Instrument
from sqlalchemy import select

log = logging.getLogger("worker.fundamentals")

FetchFn = Callable[[list[str]], list]


def refresh_snapshots(
    instruments: Sequence[Instrument],
    existing: Sequence[Fundamental],
    fetch: FetchFn,
    *,
    ts: datetime | None = None,
) -> list[Fundamental]:
    ticker_by_uid = {
        row.uid: row.ticker for row in instruments if row.uid and row.ticker
    }
    if not ticker_by_uid:
        return list(existing)
    try:
        stats = fetch(list(ticker_by_uid.keys()))
    except Exception:
        log.exception("fundamentals fetch failed")
        return list(existing)
    paired = pair_stats(stats, ticker_by_uid)
    if not paired:
        return list(existing)
    return apply_snapshots(existing, paired, ts=ts or datetime.now(UTC))


async def _persist(rows: Sequence[Fundamental]) -> int:
    maker = get_sessionmaker()
    async with maker() as session:
        current = {
            row.ticker: row
            for row in await session.scalars(select(Fundamental))
        }
        instruments = list(await session.scalars(select(Instrument)))
        # rows already merged; upsert by ticker
        saved = 0
        for row in rows:
            found = current.get(row.ticker)
            if found is None:
                session.add(row)
                saved += 1
            else:
                found.asset_uid = row.asset_uid
                found.ts = row.ts
                found.pe_ratio_ttm = row.pe_ratio_ttm
                found.price_to_book_ttm = row.price_to_book_ttm
                found.eps_ttm = row.eps_ttm
                found.market_capitalization = row.market_capitalization
                found.raw = row.raw
                saved += 1
        await session.commit()
        log.info(
            "fundamentals upserted=%s instruments=%s", saved, len(instruments)
        )
        return saved


def persist_fundamentals(rows: Sequence[Fundamental]) -> int:
    if not rows:
        return 0
    return asyncio.run(_persist(rows))


async def run_fundamentals_refresh(fetch: FetchFn | None = None) -> int:
    from app.broker.tinkoff import fetch_asset_fundamentals

    maker = get_sessionmaker()
    async with maker() as session:
        instruments = list(await session.scalars(select(Instrument)))
        existing = list(await session.scalars(select(Fundamental)))
    fn = fetch or fetch_asset_fundamentals
    updated = refresh_snapshots(instruments, existing, fn)
    if not updated:
        return 0
    return await _persist(updated)
