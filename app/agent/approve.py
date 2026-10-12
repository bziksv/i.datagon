"""Approve → риск → ордер или веса. Без approve ничего не едет."""

from collections.abc import Iterable
from decimal import Decimal
from typing import Any
from uuid import uuid4

from app.agent.proposals import STATUS_APPROVED, STATUS_PROPOSED, set_status
from app.agent.schemas import ProposeOrder, ProposeWeights
from app.agent.store import remember
from app.alloc.weights_store import save_weights
from app.book.orders import STATUS_REJECTED
from app.broker.port import BrokerPort, OrderRequest
from app.models import AgentProposal, Order
from app.risk.gate import place_after_gate


class NotProposedError(ValueError):
    pass


def apply_weights(payload: dict) -> dict[str, Decimal]:
    body = ProposeWeights.model_validate(payload)
    return {row.sleeve: Decimal(str(row.weight)) for row in body.weights}


def apply_approved(
    proposal: AgentProposal,
    *,
    tickers: Iterable[str],
    port: BrokerPort | None,
    **gate: Any,
) -> tuple[AgentProposal, Order | None, dict[str, Decimal] | None]:
    if proposal.status != STATUS_PROPOSED:
        raise NotProposedError(proposal.status)
    if proposal.kind == "order":
        body = ProposeOrder.model_validate(proposal.payload)
        order = place_after_gate(
            OrderRequest(
                ticker=body.ticker,
                side=body.side,
                qty=body.qty,
                type="market",
                client_order_id=str(uuid4()),
            ),
            sleeve=body.sleeve,
            port=port,
            tickers=tickers,
            **gate,
        )
        if order.status == STATUS_REJECTED:
            return proposal, order, None
        set_status(proposal, STATUS_APPROVED)
        remember(proposal)
        return proposal, order, None
    if proposal.kind == "weights":
        weights = apply_weights(proposal.payload)
        save_weights(weights)
        set_status(proposal, STATUS_APPROVED)
        remember(proposal)
        return proposal, None, weights
    raise ValueError(proposal.kind)
