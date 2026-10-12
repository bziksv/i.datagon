"""fund_screener: топ по скору → propose_order (без автоисполнения)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta

from app.advisory.view import recommendations_view
from app.agent.proposals import new_proposal
from app.agent.schemas import ProposeOrder
from app.agent.store import remember
from app.models import AgentProposal, Fundamental

SLEEVE = "fund_screener"
PAPER_EXECUTION_MODE = "paper_book"
REQUIRED_PLAN_FIELDS = ("entry_price", "price_as_of", "lot")


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
    trade_plans: Mapping[str, Mapping[str, object]],
    limit: int = 5,
    min_score: float = 40.0,
) -> list[AgentProposal]:
    created: list[AgentProposal] = []
    for row in rank_candidates(rows, limit=limit, min_score=min_score):
        plan = trade_plans.get(row["ticker"].upper())
        if not plan:
            continue
        body = ProposeOrder(
            ticker=row["ticker"],
            side="buy",
            qty=int(plan["qty"]),
            stop=float(plan["stop"]),
            entry_price=float(plan["entry_price"]),
            price_as_of=str(plan["price_as_of"]),
            lot=int(plan["lot"]),
            execution_mode=PAPER_EXECUTION_MODE,
            reason=row["rationale"],
            sleeve=SLEEVE,
        )
        proposal = remember(new_proposal("order", body.model_dump()))
        created.append(proposal)
    return created


def fund_screener_plan_error(
    payload: Mapping[str, object],
    *,
    now: datetime | None = None,
    max_price_age: timedelta | None = None,
) -> str | None:
    """Fail-close legacy recommendations that do not freeze a trading plan."""
    if payload.get("sleeve") != SLEEVE:
        return None
    if payload.get("execution_mode") != PAPER_EXECUTION_MODE:
        return "recommendation_plan_incomplete"
    if any(payload.get(field) in (None, "") for field in REQUIRED_PLAN_FIELDS):
        return "recommendation_plan_incomplete"
    try:
        qty = int(payload["qty"])
        lot = int(payload["lot"])
        entry = float(payload["entry_price"])
        stop = float(payload["stop"])
        price_as_of = datetime.fromisoformat(
            str(payload["price_as_of"]).replace("Z", "+00:00")
        )
    except (KeyError, TypeError, ValueError):
        return "recommendation_plan_incomplete"
    if lot < 1 or qty < lot or qty % lot != 0:
        return "recommendation_lot_invalid"
    if entry <= 0 or stop <= 0 or stop >= entry:
        return "recommendation_stop_invalid"
    if now is not None and max_price_age is not None:
        observed = (
            price_as_of
            if price_as_of.tzinfo is not None
            else price_as_of.replace(tzinfo=UTC)
        )
        reference = now if now.tzinfo is not None else now.replace(tzinfo=UTC)
        if observed > reference + timedelta(minutes=5):
            return "recommendation_price_invalid"
        if reference - observed > max_price_age:
            return "recommendation_price_stale"
    return None
