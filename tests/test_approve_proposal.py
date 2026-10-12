from collections.abc import AsyncIterator
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from app.agent.approve import apply_approved
from app.agent.proposals import STATUS_APPROVED, STATUS_PROPOSED, new_proposal
from app.book.orders import STATUS_REJECTED
from app.broker.fake import FakeBroker
from app.db import get_db
from app.main import create_app
from app.models import Candle, EquitySnapshot, Instrument, LedgerEntry, UniverseMember
from app.risk.context import RiskContext
from fastapi.testclient import TestClient

ORDER = {
    "ticker": "SBER",
    "side": "buy",
    "qty": 1,
    "stop": 250.0,
    "reason": "sma",
    "sleeve": "sma_cross",
}


def _context() -> RiskContext:
    return RiskContext(
        price=Decimal("250"),
        price_as_of=datetime.now(UTC),
        equity=Decimal("1000000"),
        start_equity=Decimal("1000000"),
        stop_price=Decimal("240"),
    )


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
    row, order, weights = apply_approved(
        row,
        tickers=["SBER"],
        port=port,
        context=_context(),
    )
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
    def __init__(self, *, include_snapshot: bool = True) -> None:
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
        now = datetime.now(UTC)
        self._candle = Candle(
            id=uuid4(),
            instrument_id=inst.id,
            tf="1d",
            ts=now,
            o=260,
            h=261,
            low=259,
            c=260,
            v=1000,
        )
        self._entry = LedgerEntry(
            id=uuid4(),
            account_kind="trading_cash",
            amount=1_000_000,
            reason="deposit",
            ts=now,
        )
        self._snapshot = EquitySnapshot(
            id=uuid4(),
            ts=now,
            trading_cash=1_000_000,
            vault=0,
            positions_value=0,
            equity=1_000_000,
        )
        self._include_snapshot = include_snapshot
        self.added = []

    def add(self, row) -> None:
        self.added.append(row)

    async def commit(self) -> None:
        return None

    async def scalars(self, stmt):
        entity = stmt.column_descriptions[0].get("entity")
        if entity is Instrument:
            return [self._inst]
        if entity is UniverseMember:
            return [self._member]
        if entity is Candle:
            return [self._candle]
        if entity is LedgerEntry:
            return [self._entry]
        if entity is EquitySnapshot:
            return [self._snapshot] if self._include_snapshot else []
        return []


async def _universe_db() -> AsyncIterator[_UniverseSession]:
    yield _UniverseSession()


async def _universe_without_snapshot() -> AsyncIterator[_UniverseSession]:
    yield _UniverseSession(include_snapshot=False)


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
    assert approved.json()["order"]["broker_order_id"] is None
    assert approved.json()["order"]["raw"]["execution_mode"] == "paper_book"


def test_legacy_fund_screener_proposal_cannot_be_approved(monkeypatch) -> None:
    monkeypatch.setenv("APP_AUTH_TOKEN", "secret")
    app = create_app()
    app.dependency_overrides[get_db] = _universe_db
    client = TestClient(app)
    legacy = {
        **ORDER,
        "reason": "legacy recommendation",
        "sleeve": "fund_screener",
    }
    created = client.post(
        "/proposals/order",
        headers={"X-App-Token": "secret"},
        json=legacy,
    )
    proposal_id = created.json()["id"]
    approved = client.post(
        f"/proposals/{proposal_id}/approve",
        headers={"X-App-Token": "secret"},
    )
    assert approved.status_code == 409
    assert approved.json()["message"] == "recommendation_plan_incomplete"
    listed = client.get("/proposals", headers={"X-App-Token": "secret"}).json()
    row = next(item for item in listed["proposals"] if item["id"] == proposal_id)
    assert row["status"] == "expired"
    assert row["payload"]["expired_reason"] == "recommendation_plan_incomplete"


def test_approve_api_fails_closed_without_day_start_snapshot(monkeypatch) -> None:
    monkeypatch.setenv("APP_AUTH_TOKEN", "secret")
    app = create_app()
    app.dependency_overrides[get_db] = _universe_without_snapshot
    client = TestClient(app)
    created = client.post(
        "/proposals/order",
        headers={"X-App-Token": "secret"},
        json=ORDER,
    )
    approved = client.post(
        f"/proposals/{created.json()['id']}/approve",
        headers={"X-App-Token": "secret"},
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "proposed"
    assert approved.json()["order"]["status"] == STATUS_REJECTED
    assert approved.json()["order"]["raw"]["reject_reason"] == "risk_context_missing"
