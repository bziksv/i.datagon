from collections.abc import AsyncIterator
from uuid import uuid4

from app.agent.approve import apply_approved
from app.agent.proposals import STATUS_APPROVED, STATUS_PROPOSED, new_proposal
from app.book.orders import STATUS_REJECTED
from app.broker.fake import FakeBroker
from app.db import get_db
from app.main import create_app
from app.models import Instrument, UniverseMember
from fastapi.testclient import TestClient

ORDER = {
    "ticker": "SBER",
    "side": "buy",
    "qty": 1,
    "stop": 250.0,
    "reason": "sma",
    "sleeve": "sma_cross",
}


def test_without_approve_nothing_moves() -> None:
    port = FakeBroker()
    row = new_proposal("order", ORDER)
    assert row.status == STATUS_PROPOSED
    assert port._orders == {}
    weights = new_proposal(
        "weights",
        {
            "weights": [
                {"sleeve": "sma_cross", "weight": 0.5},
                {"sleeve": "donchian_breakout", "weight": 0.5},
            ]
        },
    )
    assert weights.status == STATUS_PROPOSED


def test_approve_order_goes_through_gate() -> None:
    port = FakeBroker()
    row = new_proposal("order", ORDER)
    row, order, weights = apply_approved(row, tickers=["SBER"], port=port)
    assert row.status == STATUS_APPROVED
    assert order is not None
    assert order.broker_order_id
    assert weights is None
    assert len(port._orders) == 1


def test_approve_order_denied_by_risk() -> None:
    port = FakeBroker()
    row = new_proposal("order", {**ORDER, "ticker": "GAZP"})
    row, order, _ = apply_approved(row, tickers=["SBER"], port=port)
    assert row.status == STATUS_PROPOSED
    assert order is not None
    assert order.status == STATUS_REJECTED
    assert port._orders == {}


def test_approve_weights() -> None:
    row = new_proposal(
        "weights",
        {
            "weights": [
                {"sleeve": "sma_cross", "weight": 0.5},
                {"sleeve": "donchian_breakout", "weight": 0.5},
            ]
        },
    )
    row, order, weights = apply_approved(row, tickers=[], port=None)
    assert row.status == STATUS_APPROVED
    assert order is None
    assert weights is not None
    assert sum(weights.values()) == 1


def test_list_proposals_api(monkeypatch) -> None:
    monkeypatch.setenv("APP_AUTH_TOKEN", "secret")
    client = TestClient(create_app())
    empty = client.get("/proposals", headers={"X-App-Token": "secret"})
    assert empty.status_code == 200
    created = client.post(
        "/proposals/order",
        headers={"X-App-Token": "secret"},
        json=ORDER,
    )
    listed = client.get("/proposals", headers={"X-App-Token": "secret"})
    assert any(row["id"] == created.json()["id"] for row in listed.json()["proposals"])


class _UniverseSession:
    def __init__(self) -> None:
        inst = Instrument(
            id=uuid4(),
            ticker="SBER",
            lot=1,
            currency="RUB",
            class_code="TQBR",
        )
        self._inst = inst
        self._member = UniverseMember(
            id=uuid4(),
            instrument_id=inst.id,
            reason="test",
            active=True,
        )

    async def scalars(self, stmt):
        entity = stmt.column_descriptions[0].get("entity")
        if entity is Instrument:
            return [self._inst]
        if entity is UniverseMember:
            return [self._member]
        return []


async def _universe_db() -> AsyncIterator[_UniverseSession]:
    yield _UniverseSession()


def test_approve_api(monkeypatch) -> None:
    monkeypatch.setenv("APP_AUTH_TOKEN", "secret")
    app = create_app()
    app.dependency_overrides[get_db] = _universe_db
    client = TestClient(app)
    created = client.post(
        "/proposals/order",
        headers={"X-App-Token": "secret"},
        json=ORDER,
    )
    assert created.status_code == 200
    assert created.json()["status"] == "proposed"
    proposal_id = created.json()["id"]
    approved = client.post(
        f"/proposals/{proposal_id}/approve",
        headers={"X-App-Token": "secret"},
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"
    assert approved.json()["order"]["ticker"] == "SBER"
