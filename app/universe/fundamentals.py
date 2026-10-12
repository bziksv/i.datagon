"""Сито фундамента: по умолчанию выключено (UNIVERSE_FUNDAMENTALS=0)."""

from collections.abc import Sequence

from app.models import Fundamental, Instrument, UniverseMember

DEFAULT_ENABLED = False


def has_usable_fundamental(snap: Fundamental | None) -> bool:
    if snap is None:
        return False
    pe = snap.pe_ratio_ttm
    return pe is not None and float(pe) > 0


def apply_fundamentals_filter(
    members: Sequence[UniverseMember],
    instruments: Sequence[Instrument],
    snaps: Sequence[Fundamental],
    *,
    enabled: bool = DEFAULT_ENABLED,
) -> list[UniverseMember]:
    if not enabled:
        return list(members)
    by_ticker = {row.ticker: row for row in snaps}
    ticker_by_id = {row.id: row.ticker for row in instruments}
    for member in members:
        ticker = ticker_by_id.get(member.instrument_id, "")
        if not has_usable_fundamental(by_ticker.get(ticker)):
            member.active = False
    return list(members)
