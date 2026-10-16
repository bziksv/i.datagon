"""Дозаполнение активной вселенной из instruments (RUB + лот)."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Instrument, UniverseMember
from app.universe.currency import is_rub_lot

AUTO_REASON = "auto_rub_lot"


def ensure_universe_members(
    members: Sequence[UniverseMember],
    instruments: Sequence[Instrument],
    *,
    reason: str = AUTO_REASON,
) -> tuple[list[UniverseMember], int]:
    """Вернуть полный список members и число новых/включённых строк."""
    by_id = {row.instrument_id: row for row in members}
    changed = 0
    out = list(members)
    for instrument in instruments:
        if not is_rub_lot(instrument):
            continue
        found = by_id.get(instrument.id)
        if found is None:
            row = UniverseMember(
                instrument_id=instrument.id,
                reason=reason,
                active=True,
            )
            by_id[instrument.id] = row
            out.append(row)
            changed += 1
            continue
        if not found.active:
            found.active = True
            found.reason = reason
            changed += 1
    return out, changed


async def sync_universe_members(
    session: AsyncSession,
    *,
    reason: str = AUTO_REASON,
) -> int:
    instruments = list(await session.scalars(select(Instrument)))
    members = list(await session.scalars(select(UniverseMember)))
    updated, changed = ensure_universe_members(
        members, instruments, reason=reason
    )
    existing_ids = {row.instrument_id for row in members}
    for row in updated:
        if row.instrument_id not in existing_ids:
            session.add(row)
    if changed:
        await session.flush()
    return changed
