import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.agent.schemas import ProposeOrder
from app.main import create_app


VALID = {
    "ticker": "sber",
    "side": "BUY",
    "qty": 10,
    "stop": 250.0,
    "reason": "sma cross",
    "sleeve": "sma_cross",
}


def test_propose_order_schema() -> None:
    body = ProposeOrder.model_validate(VALID)
    assert body.ticker == "SBER"
    assert body.side == "buy"
    assert body.qty == 10
    assert body.stop == 250.0
    assert body.reason == "sma cross"
    assert body.sleeve == "sma_cross"


def test_propose_order_invalid_raises() -> None:
    with pytest.raises(ValidationError):
        ProposeOrder.model_validate({**VALID, "qty": 0})
    with pytest.raises(ValidationError):
        ProposeOrder.model_validate({**VALID, "side": "hold"})
    with pytest.raises(ValidationError):
        ProposeOrder.model_validate({k: VALID[k] for k in VALID if k != "ticker"})


def test_propose_order_api_422(monkeypatch) -> None:
    monkeypatch.setenv("APP_AUTH_TOKEN", "secret")
    client = TestClient(create_app())
    response = client.post(
        "/proposals/order",
        headers={"X-App-Token": "secret"},
        json={"ticker": "SBER"},
    )
    assert response.status_code == 422
    assert response.json()["code"] == "422"


def test_propose_order_api_ok(monkeypatch) -> None:
    monkeypatch.setenv("APP_AUTH_TOKEN", "secret")
    client = TestClient(create_app())
    response = client.post(
        "/proposals/order",
        headers={"X-App-Token": "secret"},
        json=VALID,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["kind"] == "order"
    assert body["status"] == "proposed"
    assert body["payload"]["ticker"] == "SBER"
    assert body["payload"]["side"] == "buy"
