from collections.abc import AsyncIterator

from app.book.orders import STATUS_UNKNOWN, draft_order
from app.broker.port import OrderRequest
from app.db import get_db
from app.main import create_app
from fastapi.testclient import TestClient


class _OrderSession:
    def __init__(self) -> None:
        self.order = draft_order(
            OrderRequest(
                ticker="SBER",
                side="buy",
                qty=10,
                type="market",
                client_order_id="api-reconcile",
            ),
            sleeve="manual",
        )
        self.order.status = STATUS_UNKNOWN
        self.commits = 0

    async def get(self, model, row_id):
        return self.order if self.order.id == row_id else None

    async def commit(self) -> None:
        self.commits += 1


def test_reconcile_order_api_appends_once(monkeypatch) -> None:
    monkeypatch.setenv("APP_AUTH_TOKEN", "secret")
    session = _OrderSession()

    async def db() -> AsyncIterator[_OrderSession]:
        yield session

    app = create_app()
    app.dependency_overrides[get_db] = db
    client = TestClient(app)
    headers = {"X-App-Token": "secret"}
    body = {
        "broker_status": "acknowledged",
        "filled_qty": 4,
        "reconciliation_id": "broker-poll-1",
    }
    url = f"/orders/{session.order.id}/reconcile"

    first = client.post(url, headers=headers, json=body)
    assert first.status_code == 200
    assert first.json()["status"] == "partially_filled"
    assert first.json()["reconciled"] is True
    assert session.commits == 1

    replay = client.post(url, headers=headers, json=body)
    assert replay.status_code == 200
    assert replay.json()["reconciled"] is False
    assert session.commits == 1
