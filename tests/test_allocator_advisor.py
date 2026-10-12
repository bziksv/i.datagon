import inspect

from app.agent import allocator
from app.agent.allocator import advise_weights
from app.agent.proposals import STATUS_PROPOSED
from app.agent.schemas import ProposeWeights
from app.alloc.capital import allocate
from app.alloc.view import ACTIVE_SLEEVES


def test_advisor_writes_propose_weights() -> None:
    before = allocate(ACTIVE_SLEEVES)
    run, proposal = advise_weights(enabled=True)
    after = allocate(ACTIVE_SLEEVES)
    assert run.role == "allocator_advisor"
    assert proposal.kind == "weights"
    assert proposal.status == STATUS_PROPOSED
    parsed = ProposeWeights.model_validate(proposal.payload)
    assert sum(row.weight for row in parsed.weights) == 1
    assert before == after


def test_advisor_does_not_apply_weights() -> None:
    source = inspect.getsource(allocator)
    assert "new_proposal" in source
    assert "propose_weights" in source.lower() or "ProposeWeights" in source
    assert "set_status" not in source
    assert "approved" not in source
    assert "allocate(" not in source
