"""Агент allocator_advisor: пишет propose_weights, веса сам не меняет."""

from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta
from decimal import Decimal

from app.agent.flag import agents_enabled
from app.agent.proposals import new_proposal
from app.agent.runs import record_run
from app.agent.schemas import ProposeWeights, SleeveWeight
from app.alloc.rebalance import constrain_weights, cooldown_active
from app.alloc.risk_budget import risk_budget_weights
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
    returns: Mapping[str, Sequence[float]] | None = None,
    max_invested_weight: Decimal = Decimal("0.50"),
    current_weights: Mapping[str, Decimal] | None = None,
    last_rebalance_at: datetime | None = None,
    cooldown: timedelta = timedelta(days=7),
    minimum_sleeve_weight: Decimal = Decimal("0.05"),
    maximum_sleeve_weight: Decimal = Decimal("0.30"),
    max_weight_step: Decimal = Decimal("0.10"),
) -> tuple[AgentRun | None, AgentProposal | None]:
    if not agents_enabled(enabled):
        return None, None
    if cooldown_active(last_rebalance_at, cooldown=cooldown):
        run = record_run(
            role=ROLE,
            input=f"Suggest weights for {','.join(sleeves)}",
            output="no proposal: rebalance cooldown is active",
            secrets=(),
        )
        return run, None
    qualified = [
        sleeve
        for sleeve in sleeves
        if evidence
        and sleeve in evidence
        and (
            bool(evidence[sleeve].get("capital_eligible", False))
            or (
                not bool(
                    evidence[sleeve].get("insufficient_statistics", True)
                )
                and int(evidence[sleeve].get("trades", 0)) >= 5
                and Decimal(
                    str(evidence[sleeve].get("excess_return", 0))
                )
                > 0
            )
        )
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
        budgets = risk_budget_weights(qualified, returns or {})
        targets = {
            sleeve: invested * budgets[sleeve] for sleeve in qualified
        }
        constrained = constrain_weights(
            targets,
            max_invested=invested,
            minimum=minimum_sleeve_weight,
            maximum=maximum_sleeve_weight,
            current=current_weights,
            max_step=max_weight_step,
        )
        invested = sum(constrained.values(), Decimal("0"))
        allocations: dict[str, Decimal] = {}
        allocated = Decimal("0")
        for sleeve in qualified[:-1]:
            value = constrained[sleeve].quantize(Decimal("0.000000000001"))
            allocations[sleeve] = value
            allocated += value
        allocations[qualified[-1]] = invested - allocated
        rows = [
            SleeveWeight(
                sleeve=sleeve,
                weight=float(allocations.get(sleeve, Decimal("0"))),
            )
            for sleeve in sleeves
        ]
        if invested < 1:
            rows.append(SleeveWeight(sleeve="cash", weight=float(1 - invested)))
        body = ProposeWeights(weights=rows)
        output = (
            "propose_weights qualified sleeves with correlation-aware "
            "risk budgets and explicit cash reserve"
        )
    proposal = new_proposal("weights", body.model_dump())
    run = record_run(
        role=ROLE,
        input=f"Suggest weights for {','.join(sleeves)}",
        output=output,
        secrets=(),
    )
    return run, proposal
