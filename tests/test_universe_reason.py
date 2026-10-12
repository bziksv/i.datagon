from uuid import uuid4

from app.models import UniverseMember
from app.universe.reason import INCLUDED, ReasonFacts, inclusion_reason
from worker.universe import explain_universe


def test_each_paper_has_explainable_reason() -> None:
    included_id = uuid4()
    halted_id = uuid4()
    fx_id = uuid4()
    thin_id = uuid4()
    overflow_id = uuid4()
    rows = {
        included_id: UniverseMember(instrument_id=included_id, reason="", active=True),
        halted_id: UniverseMember(instrument_id=halted_id, reason="", active=False),
        fx_id: UniverseMember(instrument_id=fx_id, reason="", active=False),
        thin_id: UniverseMember(instrument_id=thin_id, reason="", active=False),
        overflow_id: UniverseMember(instrument_id=overflow_id, reason="", active=False),
    }
    facts = {
        included_id: ReasonFacts(True, True, True, True),
        halted_id: ReasonFacts(False, True, True, True),
        fx_id: ReasonFacts(True, False, True, True),
        thin_id: ReasonFacts(True, True, False, True),
        overflow_id: ReasonFacts(True, True, True, False),
    }
    explain_universe(list(rows.values()), facts)
    assert rows[included_id].reason == INCLUDED
    assert rows[halted_id].reason == "not_tradable"
    assert rows[fx_id].reason == "not_rub_or_lot"
    assert rows[thin_id].reason == "illiquid"
    assert rows[overflow_id].reason == "over_universe_max"
    assert all(row.reason for row in rows.values())
    assert inclusion_reason(facts[included_id]) == "tradable,rub,lot,liquid"
