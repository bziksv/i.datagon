"""Агент allocator_advisor: пишет propose_weights, веса сам не меняет."""

from collections.abc import Sequence
from decimal import Decimal

from app.agent.flag import agents_enabled
from app.agent.proposals import new_proposal
from app.agent.runs import record_run
from app.agent.schemas import ProposeWeights, SleeveWeight
from app.alloc.view import ACTIVE_SLEEVES
from app.models import AgentProposal, AgentRun

ROLE = "allocator_advisor"


def _equal_weights(sleeves: Sequence[str]) -> ProposeWeights:
    n = len(sleeves)
    share = float(Decimal("1") / Decimal(n))
    return ProposeWeights(
        weights=[SleeveWeight(sleeve=name, weight=share) for name in sleeves]
    )


def advise_weights(
    sleeves: Sequence[str] = ACTIVE_SLEEVES,
    *,
    enabled: bool | None = None,
) -> tuple[AgentRun, AgentProposal] | tuple[None, None]:
    if not agents_enabled(enabled):
        return None, None
    body = _equal_weights(sleeves)
    proposal = new_proposal("weights", body.model_dump())
    run = record_run(
        role=ROLE,
        input=f"Suggest weights for {','.join(sleeves)}",
        output="propose_weights equal-weight, pending approve",
        secrets=(),
    )
    return run, proposal
