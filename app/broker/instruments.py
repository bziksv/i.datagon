"""Поиск акции по ticker на MOEX (TQBR) и запись в `instruments`.

Маппинг ticker ↔ figi ↔ uid: повторный lookup читает строку из БД
и не ходит в брокер.
"""

from collections.abc import Callable, Sequence
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Instrument

MOEX_CLASS_CODE = "TQBR"


def pick_moex(hits: list[Any], ticker: str) -> Any | None:
    want = ticker.upper()
    for hit in hits:
        if (getattr(hit, "ticker", "") or "").upper() != want:
            continue
        if (getattr(hit, "class_code", "") or "") == MOEX_CLASS_CODE:
            return hit
    return None


def instrument_from_share(share: Any) -> Instrument:
    return Instrument(
        ticker=(share.ticker or "").upper(),
        figi=share.figi or None,
        uid=getattr(share, "uid", None) or None,
        lot=int(getattr(share, "lot", 1) or 1),
        currency=(getattr(share, "currency", None) or "rub").lower(),
        class_code=getattr(share, "class_code", None) or MOEX_CLASS_CODE,
    )


def merge_instrument(existing: Instrument | None, found: Instrument) -> Instrument:
    if existing is None:
        return found
    existing.figi = found.figi
    existing.uid = found.uid
    existing.lot = found.lot
    existing.currency = found.currency
    return existing


async def store_instrument(session: AsyncSession, found: Instrument) -> Instrument:
    existing = await session.scalar(
        select(Instrument).where(
            Instrument.ticker == found.ticker,
            Instrument.class_code == found.class_code,
        )
    )
    row = merge_instrument(existing, found)
    if existing is None:
        session.add(row)
        await session.flush()
    return row


def mapping_complete(row: Instrument | None) -> bool:
    return bool(row and row.ticker and row.figi and row.uid)


def instrument_ids(row: Instrument) -> dict[str, str]:
    return {"ticker": row.ticker, "figi": row.figi or "", "uid": row.uid or ""}


def pick_by_id(
    rows: Sequence[Instrument],
    *,
    ticker: str | None = None,
    figi: str | None = None,
    uid: str | None = None,
) -> Instrument | None:
    ticker_u = ticker.upper() if ticker else None
    for row in rows:
        if ticker_u and row.ticker == ticker_u:
            return row
        if figi and row.figi == figi:
            return row
        if uid and row.uid == uid:
            return row
    return None


def resolve_mapped_instrument(
    existing: Instrument | None,
    fetch: Callable[[], Instrument],
) -> tuple[Instrument, bool]:
    if mapping_complete(existing):
        return existing, False
    return fetch(), True


async def load_instrument(
    session: AsyncSession,
    *,
    ticker: str | None = None,
    figi: str | None = None,
    uid: str | None = None,
) -> Instrument | None:
    stmt = select(Instrument)
    if ticker:
        stmt = stmt.where(
            Instrument.ticker == ticker.upper(),
            Instrument.class_code == MOEX_CLASS_CODE,
        )
    elif figi:
        stmt = stmt.where(Instrument.figi == figi)
    elif uid:
        stmt = stmt.where(Instrument.uid == uid)
    else:
        return None
    return await session.scalar(stmt)


async def ensure_mapped_instrument(
    session: AsyncSession,
    fetch: Callable[[], Instrument],
    *,
    ticker: str | None = None,
    figi: str | None = None,
    uid: str | None = None,
) -> Instrument:
    existing = await load_instrument(session, ticker=ticker, figi=figi, uid=uid)
    row, fetched = resolve_mapped_instrument(existing, fetch)
    if fetched:
        return await store_instrument(session, row)
    return row


def moex_share_rows(shares: Sequence[Any]) -> list[Instrument]:
    rows: list[Instrument] = []
    for share in shares:
        if (getattr(share, "class_code", "") or "") != MOEX_CLASS_CODE:
            continue
        if not (getattr(share, "ticker", "") or "").strip():
            continue
        rows.append(instrument_from_share(share))
    return rows


def merge_instrument_table(
    existing: Sequence[Instrument],
    incoming: Sequence[Instrument],
) -> list[Instrument]:
    by_key = {(row.ticker, row.class_code): row for row in existing}
    for found in incoming:
        key = (found.ticker, found.class_code)
        by_key[key] = merge_instrument(by_key.get(key), found)
    return list(by_key.values())


def dump_moex_instruments(
    existing: Sequence[Instrument],
    shares: Sequence[Any],
) -> list[Instrument]:
    rows = merge_instrument_table(existing, moex_share_rows(shares))
    if not rows:
        raise RuntimeError("instruments dump is empty")
    return rows
