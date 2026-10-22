"""Запись сигналов воркера в Postgres."""

import asyncio
from collections.abc import Sequence

from app.db import get_sessionmaker
from app.models import SignalRow
from sqlalchemy import select


def _key(row: SignalRow) -> tuple:
    return (row.sleeve, row.ticker, row.ts)


async def persist_signals_async(rows: Sequence[SignalRow]) -> int:
    """Повторный прогон того же бара (перезапуск воркера) не плодит дубли."""
    if not rows:
        return 0
    maker = get_sessionmaker()
    async with maker() as session:
        found = await session.execute(
            select(SignalRow.sleeve, SignalRow.ticker, SignalRow.ts).where(
                SignalRow.ts.in_({row.ts for row in rows}),
                SignalRow.sleeve.in_({row.sleeve for row in rows}),
            )
        )
        seen = {tuple(item) for item in found}
        fresh = []
        for row in rows:
            if _key(row) not in seen:
                seen.add(_key(row))
                fresh.append(row)
        session.add_all(fresh)
        await session.commit()
    return len(fresh)


def persist_signals(rows: Sequence[SignalRow]) -> int:
    if not rows:
        return 0
    return asyncio.run(persist_signals_async(rows))
