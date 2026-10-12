import pytest

from app.agent.proposals import (
    STATUSES,
    STATUS_APPROVED,
    STATUS_EXPIRED,
    STATUS_PROPOSED,
    STATUS_REJECTED,
    ProposalStatusError,
    new_proposal,
    set_status,
)
from app.models import AgentProposal


def test_new_proposal_starts_proposed() -> None:
    row = new_proposal("order", {"ticker": "SBER"})
    assert isinstance(row, AgentProposal)
    assert row.kind == "order"
    assert row.payload == {"ticker": "SBER"}
    assert row.status == STATUS_PROPOSED
    assert AgentProposal.__tablename__ == "agent_proposals"


def test_status_cycle() -> None:
    row = new_proposal("weights", {})
    assert set_status(row, STATUS_APPROVED).status == "approved"
    assert set_status(row, STATUS_REJECTED).status == "rejected"
    assert set_status(row, STATUS_EXPIRED).status == "expired"
    assert STATUSES == {"proposed", "approved", "rejected", "expired"}


def test_unknown_status_rejected() -> None:
    row = new_proposal("order")
    with pytest.raises(ProposalStatusError):
        set_status(row, "done")
    assert row.status == STATUS_PROPOSED
