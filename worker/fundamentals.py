"""Джоба: обновить снимки GetAssetFundamentals по всем TQBR с Тинькофф."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable, Sequence
from datetime import UTC, datetime

from app.advisory.moex_catalog import normalize_sector, sector_title
from app.broker.fundamentals import apply_snapshots, pair_stats
from app.broker.instruments import dump_moex_instruments
from app.db import get_sessionmaker
from app.models import Fundamental, Instrument
from sqlalchemy import select

log = logging.getLogger("worker.fundamentals")

FetchFn = Callable[[list[str]], list]
ASSET_CHUNK = 80


class FundamentalsRefreshError(RuntimeError):
    """Ошибка обновления фундамента — текст уходит в кабинет."""


def share_meta_map(shares: Sequence[object]) -> dict[str, dict[str, str]]:
    """ticker → name/sector из ответа instruments.shares."""
    out: dict[str, dict[str, str]] = {}
    for share in shares:
        ticker = (getattr(share, "ticker", None) or "").strip().upper()
        if not ticker:
            continue
        name = (getattr(share, "name", None) or "").strip() or ticker
        sector = normalize_sector(getattr(share, "sector", None))
        out[ticker] = {
            "name": name,
            "sector": sector,
            "sector_id": sector,
            "sector_title": sector_title(sector),
        }
    return out


def all_share_tickers(shares: Sequence[object]) -> set[str]:
    return {
        (getattr(share, "ticker", None) or "").strip().upper()
        for share in shares
        if (getattr(share, "ticker", None) or "").strip()
    }


def asset_map_for_tickers(
    shares: Sequence[object],
    tickers: set[str] | None = None,
) -> dict[str, str]:
    """asset_uid → ticker. GetAssetFundamentals ждёт asset_uid, не instrument uid."""
    out: dict[str, str] = {}
    for share in shares:
        ticker = (getattr(share, "ticker", None) or "").strip().upper()
        asset_uid = (getattr(share, "asset_uid", None) or "").strip()
        if not ticker or not asset_uid:
            continue
        if tickers is not None and ticker not in tickers:
            continue
        out[asset_uid] = ticker
    return out


def enrich_with_share_meta(
    rows: Sequence[Fundamental],
    meta: dict[str, dict[str, str]],
) -> list[Fundamental]:
    for row in rows:
        info = meta.get(row.ticker.upper())
        if not info:
            continue
        raw = dict(row.raw or {})
        raw.update(info)
        row.raw = raw
    return list(rows)


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
            "Не удалось загрузить акции РФ с брокера (sandbox API недоступен). "
            "Нажмите «Демо-данные» — расширенный каталог MOEX с названиями и секторами."
        ) from exc

    dumped = dump_moex_instruments(instruments, shares)
    await _persist_instruments(dumped)

    # Все TQBR с Тинькофф, не только desk.
    want = all_share_tickers(shares)
    ticker_by_asset = asset_map_for_tickers(shares, want)
    if not ticker_by_asset:
        raise FundamentalsRefreshError(
            "Справочник акций есть, но нет asset_uid у TQBR. "
            "Проверьте токен sandbox и ответ instruments.shares."
        )

    fn = fetch or fetch_asset_fundamentals
    updated = refresh_snapshots(existing, ticker_by_asset, fn)
    enrich_with_share_meta(updated, share_meta_map(shares))
    return await _persist(updated)
