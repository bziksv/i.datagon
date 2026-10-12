from uuid import uuid4

from app.models import Instrument, UniverseMember
from app.universe.currency import is_rub_lot
from worker.universe import mark_rub_lots


def _instrument(*, currency: str, lot: int) -> Instrument:
    return Instrument(
        id=uuid4(),
        ticker="SBER",
        figi="FIGI",
        uid="uid",
        lot=lot,
        currency=currency,
        class_code="TQBR",
    )


def test_usd_is_marked_inactive() -> None:
    rub = _instrument(currency="rub", lot=10)
    usd = _instrument(currency="usd", lot=1)
    keep = UniverseMember(instrument_id=rub.id, reason="dump", active=True)
    drop = UniverseMember(instrument_id=usd.id, reason="dump", active=True)
    mark_rub_lots([keep, drop], [rub, usd])
    assert keep.active is True
    assert drop.active is False


def test_zero_lot_is_marked_inactive() -> None:
    bad = _instrument(currency="RUB", lot=0)
    member = UniverseMember(instrument_id=bad.id, reason="dump", active=True)
    mark_rub_lots([member], [bad])
    assert member.active is False
    assert is_rub_lot(bad) is False
