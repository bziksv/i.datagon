import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.agent.schemas import ProposeWeights
from app.main import create_app

VALID = {
    "weights": [
        {"sleeve": "sma_cross", "weight": 0.5},
        {"sleeve": "donchian_breakout", "weight": 0.5},
    ]
}


def test_propose_weights_sum_to_one() -> None:
    body = ProposeWeights.model_validate(VALID)
    assert [row.sleeve for row in body.weights] == [
        "sma_cross",
        "donchian_breakout",
    ]
    assert [row.weight for row in body.weights] == [0.5, 0.5]


def test_propose_weights_invalid() -> None:
    with pytest.raises(ValidationError):
        ProposeWeights.model_validate(
            {
                "weights": [
                    {"sleeve": "sma_cross", "weight": 0.6},
                    {"sleeve": "donchian_breakout", "weight": 0.5},
                ]
            }
        )
    with pytest.raises(ValidationError):
        ProposeWeights.model_validate({"weights": []})


def test_propose_weights_api_422(monkeypatch) -> None:
    monkeypatch.setenv("APP_AUTH_TOKEN", "secret")
    client = TestClient(create_app())
    response = client.post(
        "/proposals/weights",
        headers={"X-App-Token": "secret"},
        json={"weights": [{"sleeve": "sma_cross", "weight": 1.5}]},
    )
    assert response.status_code == 422
    assert response.json()["code"] == "422"


def test_propose_weights_api_ok(monkeypatch) -> None:
    monkeypatch.setenv("APP_AUTH_TOKEN", "secret")
    client = TestClient(create_app())
    response = client.post(
        "/proposals/weights",
        headers={"X-App-Token": "secret"},
        json=VALID,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["kind"] == "weights"
    assert body["status"] == "proposed"
    assert body["payload"]["weights"][0]["weight"] == 0.5
