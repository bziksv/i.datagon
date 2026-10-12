import pytest
from fastapi.testclient import TestClient

from app.agent.proposals import (
    STATUS_PROPOSED,
    STATUS_REJECTED,
    ProposalStatusError,
    new_proposal,
    reject_proposal,
)
from app.broker.fake import FakeBroker
from app.main import create_app


ORDER = {
    "ticker": "SBER",
    "side": "buy",
    "qty": 1,
    "stop": 250.0,
    "reason": "sma",
    "sleeve": "sma_cross",
}


def test_reject_sets_status() -> None:
    row = new_proposal("order", ORDER)
    port = FakeBroker()
    rejected = reject_proposal(row)
    assert rejected.status == STATUS_REJECTED
    assert port._orders == {}
    with pytest.raises(ProposalStatusError):
        reject_proposal(rejected)


def test_reject_api(monkeypatch) -> None:
    monkeypatch.setenv("APP_AUTH_TOKEN", "secret")
    client = TestClient(create_app())
    created = client.post(
        "/proposals/order",
        headers={"X-App-Token": "secret"},
        json=ORDER,
    )
    assert created.json()["status"] == STATUS_PROPOSED
    response = client.post(
        f"/proposals/{created.json()['id']}/reject",
        headers={"X-App-Token": "secret"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "rejected"
    assert "order" not in response.json()
