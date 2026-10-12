from app.book.orders import draft_order, orders_view, reject_order
from app.broker.port import OrderRequest
from app.main import create_app
from fastapi.testclient import TestClient


def _req(client_order_id: str) -> OrderRequest:
    return OrderRequest(
        ticker="SBER",
        side="buy",
        qty=1,
        type="market",
        client_order_id=client_order_id,
    )


def test_orders_filter_by_status() -> None:
    opened = draft_order(_req("c-new"), sleeve="manual")
    failed = reject_order(draft_order(_req("c-rej"), sleeve="manual"), "broker_unavailable")
    all_rows = orders_view([opened, failed])
    assert len(all_rows["orders"]) == 2
    rejected = orders_view([opened, failed], status="rejected")
    assert [row["status"] for row in rejected["orders"]] == ["rejected"]
    assert rejected["orders"][0]["client_order_id"] == "c-rej"
    assert rejected["orders"][0]["raw"]["reject_reason"] == "broker_unavailable"


def test_orders_unauthorized(monkeypatch) -> None:
    monkeypatch.setenv("APP_AUTH_TOKEN", "secret")
    client = TestClient(create_app())
    response = client.get("/orders")
    assert response.status_code == 401


def test_orders_without_db(monkeypatch) -> None:
    monkeypatch.setenv("APP_AUTH_TOKEN", "secret")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    client = TestClient(create_app())
    response = client.get(
        "/orders",
        params={"status": "new"},
        headers={"X-App-Token": "secret"},
    )
    assert response.status_code == 503
