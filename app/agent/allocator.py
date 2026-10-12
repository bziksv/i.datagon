"""Агент allocator_advisor: пишет propose_weights, веса сам не меняет."""

from collections.abc import Mapping, Sequence
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
    evidence: Mapping[str, Mapping[str, object]] | None = None,
    max_invested_weight: Decimal = Decimal("0.50"),
) -> tuple[AgentRun, AgentProposal] | tuple[None, None]:
    if not agents_enabled(enabled):
        return None, None
    qualified = [
        sleeve
        for sleeve in sleeves
        if evidence
        and sleeve in evidence
        and not bool(evidence[sleeve].get("insufficient_statistics", True))
        and int(evidence[sleeve].get("trades", 0)) >= 5
        and Decimal(str(evidence[sleeve].get("excess_return", 0))) > 0
    ]
    if not qualified:
        body = ProposeWeights(
            weights=[
                *[
                    SleeveWeight(sleeve=sleeve, weight=0.0)
                    for sleeve in sleeves
                ],
                SleeveWeight(sleeve="cash", weight=1.0),
            ]
        )
        output = "propose_weights cash-only: no strategy passed OOS qualification"
    else:
        invested = min(max(Decimal(max_invested_weight), Decimal("0")), Decimal("1"))
        share = invested / Decimal(len(qualified))
        rows = [
            SleeveWeight(
                sleeve=sleeve,
                weight=float(share if sleeve in qualified else Decimal("0")),
            )
            for sleeve in sleeves
        ]
        if invested < 1:
            rows.append(SleeveWeight(sleeve="cash", weight=float(1 - invested)))
        body = ProposeWeights(weights=rows)
        output = "propose_weights qualified OOS sleeves with explicit cash reserve"
    proposal = new_proposal("weights", body.model_dump())
    run = record_run(
        role=ROLE,
        input=f"Suggest weights for {','.join(sleeves)}",
        output=output,
        secrets=(),
    )
    return run, proposal
