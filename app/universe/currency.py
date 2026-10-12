"""Фильтр вселенной: только RUB и лот ≥ 1. Валютные помечаем inactive."""

from collections.abc import Sequence

from app.models import Instrument, UniverseMember

RUB = "rub"


def is_rub_lot(instrument: Instrument) -> bool:
    currency = (instrument.currency or "").lower()
    lot = int(instrument.lot or 0)
    return currency == RUB and lot >= 1


def apply_currency_lot_filter(
    members: Sequence[UniverseMember],
    instruments: Sequence[Instrument],
) -> list[UniverseMember]:
    by_id = {row.id: row for row in instruments}
    for member in members:
        instrument = by_id.get(member.instrument_id)
        if instrument is None or not is_rub_lot(instrument):
            member.active = False
    return list(members)
