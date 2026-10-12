from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from app.agent import tools
from app.agent.tools import ALLOWED_TOOLS, get_bars, get_positions, propose_order
from app.broker.port import CandleBar
from app.models import Position


def test_allowed_tools_have_no_place_order() -> None:
    assert "get_bars" in ALLOWED_TOOLS
    assert "get_positions" in ALLOWED_TOOLS
    assert "propose_order" in ALLOWED_TOOLS
    assert "propose_weights" in ALLOWED_TOOLS
    assert "place_order" not in ALLOWED_TOOLS
    assert not hasattr(tools, "place_order")


def test_agent_package_has_no_place_order() -> None:
    root = Path(__file__).resolve().parents[1] / "app" / "agent"
    hits: list[str] = []
    for path in root.rglob("*.py"):
        text = path.read_text()
        if "place_order" in text:
            hits.append(path.name)
    assert hits == []


def test_get_bars_and_positions() -> None:
    bars = get_bars(
        [
            CandleBar(
                ts=datetime(2026, 10, 12, tzinfo=UTC),
                o=Decimal("10"),
                h=Decimal("11"),
                low=Decimal("9"),
                c=Decimal("10.5"),
                v=Decimal("1"),
            )
        ]
    )
    assert bars[0]["c"] == "10.5"
    rows = get_positions(
        [
            Position(
                sleeve="sma_cross",
                instrument_id=uuid4(),
                qty=2,
                avg_price=Decimal("100"),
            )
        ]
    )
    assert rows[0]["qty"] == 2
    proposal = propose_order(
        {
            "ticker": "SBER",
            "side": "buy",
            "qty": 1,
            "stop": 250,
            "reason": "test",
            "sleeve": "sma_cross",
        }
    )
    assert proposal.kind == "order"
    assert proposal.status == "proposed"
