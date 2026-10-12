"""Джоба: обновить снимки GetAssetFundamentals по бумагам desk/вселенной."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable, Sequence
from datetime import UTC, datetime

from app.broker.fundamentals import apply_snapshots, pair_stats
from app.broker.instruments import dump_moex_instruments
from app.db import get_sessionmaker
from app.models import Fundamental, Instrument
from app.strategy.moex_groups import all_moex_desk_tickers
from sqlalchemy import select

log = logging.getLogger("worker.fundamentals")

FetchFn = Callable[[list[str]], list]
ASSET_CHUNK = 80


class FundamentalsRefreshError(RuntimeError):
    """Ошибка обновления фундамента — текст уходит в кабинет."""


def target_tickers(existing: Sequence[Fundamental]) -> set[str]:
    want = set(all_moex_desk_tickers())
    want.update(row.ticker.upper() for row in existing if row.ticker)
    return want


def asset_map_for_tickers(
    shares: Sequence[object],
    tickers: set[str],
) -> dict[str, str]:
    """asset_uid → ticker. GetAssetFundamentals ждёт asset_uid, не instrument uid."""
    out: dict[str, str] = {}
    for share in shares:
        ticker = (getattr(share, "ticker", None) or "").strip().upper()
        asset_uid = (getattr(share, "asset_uid", None) or "").strip()
        if not ticker or not asset_uid or ticker not in tickers:
            continue
        out[asset_uid] = ticker
    return out


def refresh_snapshots(
    existing: Sequence[Fundamental],
    ticker_by_asset: dict[str, str],
    fetch: FetchFn,
    *,
    ts: datetime | None = None,
) -> list[Fundamental]:
    if not ticker_by_asset:
        raise FundamentalsRefreshError(
            "Нет бумаг для обновления: пустой справочник или нет asset_uid."
        )
    assets = list(ticker_by_asset.keys())
    stats: list = []
    try:
        for i in range(0, len(assets), ASSET_CHUNK):
            chunk = assets[i : i + ASSET_CHUNK]
            stats.extend(fetch(chunk))
    except FundamentalsRefreshError:
        raise
    except Exception as exc:
        log.exception("fundamentals fetch failed")
        raise FundamentalsRefreshError(
            f"Брокер не отдал фундамент: {exc}"
        ) from exc
    paired = pair_stats(stats, ticker_by_asset)
    if not paired:
        raise FundamentalsRefreshError(
            "Брокер ответил, но не сопоставил asset_uid с тикерами."
        )
    return apply_snapshots(existing, paired, ts=ts or datetime.now(UTC))


async def _persist_instruments(rows: Sequence[Instrument]) -> int:
    maker = get_sessionmaker()
    async with maker() as session:
        current = {
            (row.ticker, row.class_code): row
            for row in await session.scalars(select(Instrument))
        }
        saved = 0
        for row in rows:
            key = (row.ticker, row.class_code)
            found = current.get(key)
            if found is None:
                session.add(row)
                current[key] = row
                saved += 1
            else:
                found.figi = row.figi
                found.uid = row.uid
                found.lot = row.lot
                found.currency = row.currency
                saved += 1
        await session.commit()
        log.info("instruments upserted=%s", saved)
        return saved


async def _persist(rows: Sequence[Fundamental]) -> int:
    maker = get_sessionmaker()
    async with maker() as session:
        current = {
            row.ticker: row
            for row in await session.scalars(select(Fundamental))
        }
        instruments = list(await session.scalars(select(Instrument)))
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
    from app.broker.tinkoff import fetch_asset_fundamentals, fetch_moex_shares

    maker = get_sessionmaker()
    async with maker() as session:
        instruments = list(await session.scalars(select(Instrument)))
        existing = list(await session.scalars(select(Fundamental)))

    try:
        shares = await asyncio.to_thread(fetch_moex_shares)
    except Exception as exc:
        raise FundamentalsRefreshError(
            "Не удалось загрузить акции с брокера (sandbox API недоступен). "
            "Пока в таблице остаются старые/демо снимки — это не полный desk."
        ) from exc

    dumped = dump_moex_instruments(instruments, shares)
    await _persist_instruments(dumped)

    want = target_tickers(existing)
    ticker_by_asset = asset_map_for_tickers(shares, want)
    if not ticker_by_asset:
        raise FundamentalsRefreshError(
            "Справочник акций есть, но нет asset_uid для desk-тикеров. "
            "Проверьте токен sandbox и ответ instruments.shares."
        )

    fn = fetch or fetch_asset_fundamentals
    updated = refresh_snapshots(existing, ticker_by_asset, fn)
    return await _persist(updated)
