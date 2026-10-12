"""Предложения агента: proposed / approved / rejected / expired."""

from uuid import uuid4

from app.models import AgentProposal

STATUS_PROPOSED = "proposed"
STATUS_APPROVED = "approved"
STATUS_REJECTED = "rejected"
STATUS_EXPIRED = "expired"
STATUSES = frozenset(
    {STATUS_PROPOSED, STATUS_APPROVED, STATUS_REJECTED, STATUS_EXPIRED}
)


class ProposalStatusError(ValueError):
    pass


def new_proposal(kind: str, payload: dict | None = None) -> AgentProposal:
    return AgentProposal(
        id=uuid4(),
        kind=kind,
        payload=dict(payload or {}),
        status=STATUS_PROPOSED,
    )


def set_status(row: AgentProposal, status: str) -> AgentProposal:
    if status not in STATUSES:
        raise ProposalStatusError(status)
    row.status = status
    return row


def reject_proposal(row: AgentProposal) -> AgentProposal:
    if row.status != STATUS_PROPOSED:
        raise ProposalStatusError(row.status)
    return set_status(row, STATUS_REJECTED)
