from types import SimpleNamespace
from uuid import uuid4

from app.models import UniverseMember
from app.universe.trading import apply_trading_filter, tradable_map
from worker.universe import mark_tradable


def test_not_tradable_is_inactive() -> None:
    live_id = uuid4()
    dead_id = uuid4()
    live = UniverseMember(instrument_id=live_id, reason="dump", active=True)
    dead = UniverseMember(instrument_id=dead_id, reason="dump", active=True)
    mark_tradable(
        [live, dead],
        {
            live_id: SimpleNamespace(name="SECURITY_TRADING_STATUS_NORMAL_TRADING"),
            dead_id: SimpleNamespace(
                name="SECURITY_TRADING_STATUS_NOT_AVAILABLE_FOR_TRADING"
            ),
        },
    )
    assert live.active is True
    assert dead.active is False


def test_missing_status_is_inactive() -> None:
    member = UniverseMember(instrument_id=uuid4(), reason="dump", active=True)
    apply_trading_filter([member], {})
    assert member.active is False


def test_tradable_map_uses_status() -> None:
    instrument_id = uuid4()
    got = tradable_map(
        {instrument_id: SimpleNamespace(name="SECURITY_TRADING_STATUS_NORMAL_TRADING")}
    )
    assert got[instrument_id] is True
