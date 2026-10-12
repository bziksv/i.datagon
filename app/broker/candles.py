"""Свечи в `candles`: повторный fetch не плодит дубли (uq instrument_id+tf+ts)."""

from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.broker.port import CandleBar
from app.models import Candle


def new_candle_rows(
    instrument_id: UUID,
    tf: str,
    bars: Sequence[CandleBar],
    existing_ts: set[datetime],
) -> list[Candle]:
    seen = set(existing_ts)
    rows: list[Candle] = []
    for bar in bars:
        if bar.ts in seen:
            continue
        seen.add(bar.ts)
        rows.append(
            Candle(
                instrument_id=instrument_id,
                tf=tf,
                ts=bar.ts,
                o=bar.o,
                h=bar.h,
                low=bar.low,
                c=bar.c,
                v=bar.v,
            )
        )
    return rows


async def store_candles(
    session: AsyncSession,
    instrument_id: UUID,
    tf: str,
    bars: Sequence[CandleBar],
) -> int:
    existing = set(
        await session.scalars(
            select(Candle.ts).where(
                Candle.instrument_id == instrument_id,
                Candle.tf == tf,
            )
        )
    )
    rows = new_candle_rows(instrument_id, tf, bars, existing)
    session.add_all(rows)
    if rows:
        await session.flush()
    return len(rows)
