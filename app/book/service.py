"""Единая загрузка рыночной valuation из книги и последних свечей."""

from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.book.valuation import PriceMark, value_portfolio
from app.models import Candle, EquitySnapshot, Fill, LedgerEntry, Position


async def portfolio_valuation(
    session: AsyncSession,
    *,
    now: datetime | None = None,
    stale_after: timedelta = timedelta(hours=36),
) -> dict:
    entries = list(await session.scalars(select(LedgerEntry)))
    positions = list(await session.scalars(select(Position)))
    fills = list(await session.scalars(select(Fill)))
    snapshots = list(await session.scalars(select(EquitySnapshot)))
    instrument_ids = {row.instrument_id for row in positions}
    candles = (
        list(
            await session.scalars(
                select(Candle).where(Candle.instrument_id.in_(instrument_ids))
            )
        )
        if instrument_ids
        else []
    )
    latest: dict[UUID, Candle] = {}
    for candle in candles:
        previous = latest.get(candle.instrument_id)
        if previous is None or candle.ts > previous.ts:
            latest[candle.instrument_id] = candle
    marks = {
        instrument_id: PriceMark(
            instrument_id=instrument_id,
            price=Decimal(str(candle.c)),
            as_of=candle.ts,
            source=f"candle:{candle.tf}",
        )
        for instrument_id, candle in latest.items()
    }
    return value_portfolio(
        entries,
        positions,
        marks,
        fills=fills,
        snapshots=snapshots,
        now=now,
        stale_after=stale_after,
    )
