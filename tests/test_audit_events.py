from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

from app.book.audit import audit_chain_valid, new_audit_event
from app.db import get_db
from app.main import create_app
from app.models import AuditEvent, LedgerEntry
from fastapi.testclient import TestClient


def test_hash_chain_detects_mutation() -> None:
    now = datetime(2026, 10, 12, tzinfo=UTC)
    first = new_audit_event(
        event_type="ledger_correction",
        entity_type="ledger_entry",
        entity_id="one",
        payload={"amount": -10},
        occurred_at=now,
    )
    second = new_audit_event(
        event_type="ledger_correction",
        entity_type="ledger_entry",
        entity_id="two",
        payload={"amount": 10},
        previous_hash=first.event_hash,
        occurred_at=now + timedelta(seconds=1),
    )
    assert audit_chain_valid([first, second])
    second.payload["amount"] = 999
    assert not audit_chain_valid([first, second])


class _AuditSession:
    def __init__(self) -> None:
        self.events = []
        self.entries = []
        self.committed = False

    async def scalar(self, stmt):
        return self.events[-1] if self.events else None

    async def scalars(self, stmt):
        return list(self.events)

    def add(self, row) -> None:
        if isinstance(row, AuditEvent):
            self.events.append(row)
        elif isinstance(row, LedgerEntry):
            self.entries.append(row)

    async def commit(self) -> None:
        self.committed = True


def test_correction_api_appends_ledger_and_audit(monkeypatch) -> None:
    monkeypatch.setenv("APP_AUTH_TOKEN", "secret")
    session = _AuditSession()

    async def db() -> AsyncIterator[_AuditSession]:
        yield session

    app = create_app()
    app.dependency_overrides[get_db] = db
    client = TestClient(app)
    headers = {"X-App-Token": "secret"}
    response = client.post(
        "/ledger/corrections",
        headers=headers,
        json={
            "amount": -125.5,
            "original_ref": "fill-bad",
            "explanation": "компенсация ошибочной проводки",
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["entry"]["amount"] == -125.5
    assert len(session.entries) == 1
    assert len(session.events) == 1
    assert session.committed

    timeline = client.get("/audit/timeline", headers=headers)
    assert timeline.status_code == 200
    assert timeline.json()["chain_valid"] is True
    assert len(timeline.json()["events"]) == 1
