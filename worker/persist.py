"""Запись сигналов воркера в Postgres."""

import asyncio
from collections.abc import Sequence

from app.db import get_sessionmaker
from app.models import SignalRow


async def _save(rows: Sequence[SignalRow]) -> int:
    if not rows:
        return 0
    maker = get_sessionmaker()
    async with maker() as session:
        for row in rows:
            session.add(row)
        await session.commit()
    return len(rows)


def persist_signals(rows: Sequence[SignalRow]) -> int:
    if not rows:
        return 0
    return asyncio.run(_save(rows))
