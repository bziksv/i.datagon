from uuid import uuid4

from app.models import Instrument, UniverseMember
from app.universe.ensure import ensure_universe_members


def test_ensure_universe_adds_rub_lot() -> None:
    rub = Instrument(
        id=uuid4(),
        ticker="SBER",
        lot=10,
        currency="rub",
        class_code="TQBR",
    )
    usd = Instrument(
        id=uuid4(),
        ticker="AAPL",
        lot=1,
        currency="usd",
        class_code="SPBXM",
    )
    members, changed = ensure_universe_members([], [rub, usd])
    assert changed == 1
    assert len(members) == 1
    assert members[0].instrument_id == rub.id
    assert members[0].active is True


def test_ensure_universe_reactivates() -> None:
    inst = Instrument(
        id=uuid4(),
        ticker="GAZP",
        lot=10,
        currency="rub",
        class_code="TQBR",
    )
    dead = UniverseMember(
        id=uuid4(),
        instrument_id=inst.id,
        reason="old",
        active=False,
    )
    members, changed = ensure_universe_members([dead], [inst])
    assert changed == 1
    assert members[0].active is True
