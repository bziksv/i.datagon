"""Список вселенной для GET /universe."""

from collections.abc import Sequence

from app.models import Instrument, UniverseMember
from app.universe.cap import DEFAULT_UNIVERSE_MAX


def universe_item(member: UniverseMember, instrument: Instrument | None) -> dict:
    return {
        "ticker": instrument.ticker if instrument else None,
        "instrument_id": str(member.instrument_id),
        "reason": member.reason,
        "active": member.active,
        "updated_at": member.updated_at.isoformat() if member.updated_at else None,
    }


def universe_view(
    members: Sequence[UniverseMember],
    instruments: Sequence[Instrument],
    *,
    limit: int = DEFAULT_UNIVERSE_MAX,
) -> dict:
    by_id = {row.id: row for row in instruments}
    rows = sorted(
        members,
        key=lambda row: (
            0 if row.active else 1,
            (by_id.get(row.instrument_id).ticker if by_id.get(row.instrument_id) else "")
            or "",
        ),
    )
    active_count = sum(1 for row in rows if row.active)
    return {
        "members": [
            universe_item(row, by_id.get(row.instrument_id)) for row in rows
        ],
        "count": active_count,
        "limit": int(limit),
    }
