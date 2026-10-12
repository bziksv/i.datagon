"""fund_screener: топ по скору → propose_order (без автоисполнения)."""

from __future__ import annotations

from collections.abc import Sequence

from app.advisory.view import recommendations_view
from app.agent.proposals import new_proposal
from app.agent.schemas import ProposeOrder
from app.agent.store import remember
from app.models import AgentProposal, Fundamental

SLEEVE = "fund_screener"
DEFAULT_QTY = 1
DEFAULT_STOP = 250.0


def rank_candidates(
    rows: Sequence[Fundamental],
    *,
    limit: int = 5,
    min_score: float = 40.0,
) -> list[dict]:
    return recommendations_view(rows, limit=limit, min_score=min_score)["candidates"]


def propose_from_scores(
    rows: Sequence[Fundamental],
    *,
    limit: int = 5,
    min_score: float = 40.0,
    qty: int = DEFAULT_QTY,
    stop: float = DEFAULT_STOP,
) -> list[AgentProposal]:
    created: list[AgentProposal] = []
    for row in rank_candidates(rows, limit=limit, min_score=min_score):
        body = ProposeOrder(
            ticker=row["ticker"],
            side="buy",
            qty=qty,
            stop=stop,
            reason=row["rationale"],
            sleeve=SLEEVE,
        )
        proposal = remember(new_proposal("order", body.model_dump()))
        created.append(proposal)
    return created
