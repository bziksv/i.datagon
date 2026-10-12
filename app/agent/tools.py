"""Инструменты модели: чтение баров/позиций и propose_*."""

from collections.abc import Sequence

from app.agent.proposals import new_proposal
from app.agent.schemas import ProposeOrder, ProposeWeights
from app.book.portfolio import position_item
from app.broker.port import CandleBar
from app.models import AgentProposal, Position

ALLOWED_TOOLS = ("get_bars", "get_positions", "propose_order", "propose_weights")


def get_bars(bars: Sequence[CandleBar]) -> list[dict]:
    return [
        {
            "ts": bar.ts.isoformat(),
            "o": str(bar.o),
            "h": str(bar.h),
            "l": str(bar.low),
            "c": str(bar.c),
            "v": str(bar.v),
        }
        for bar in bars
    ]


def get_positions(positions: Sequence[Position]) -> list[dict]:
    return [position_item(row) for row in positions]


def propose_order(payload: dict) -> AgentProposal:
    body = ProposeOrder.model_validate(payload)
    return new_proposal("order", body.model_dump())


def propose_weights(payload: dict) -> AgentProposal:
    body = ProposeWeights.model_validate(payload)
    return new_proposal("weights", body.model_dump())
