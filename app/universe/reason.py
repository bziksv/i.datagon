"""Почему бумага в сите или выпала — пишем в universe_members.reason."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from uuid import UUID

from app.models import UniverseMember

INCLUDED = "tradable,rub,lot,liquid"


@dataclass(frozen=True)
class ReasonFacts:
    tradable: bool
    rub_lot: bool
    liquid: bool
    in_cap: bool
    fundamental: bool = True


def inclusion_reason(facts: ReasonFacts) -> str:
    if not facts.tradable:
        return "not_tradable"
    if not facts.rub_lot:
        return "not_rub_or_lot"
    if not facts.liquid:
        return "illiquid"
    if not facts.fundamental:
        return "weak_fundamental"
    if not facts.in_cap:
        return "over_universe_max"
    return INCLUDED


def apply_reasons(
    members: Sequence[UniverseMember],
    facts: Mapping[UUID, ReasonFacts],
) -> list[UniverseMember]:
    for member in members:
        member.reason = inclusion_reason(
            facts.get(
                member.instrument_id,
                ReasonFacts(
                    tradable=False, rub_lot=False, liquid=False, in_cap=False
                ),
            )
        )
    return list(members)
