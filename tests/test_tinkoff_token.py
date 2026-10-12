import inspect

import pytest
from app.broker.tinkoff import BrokerTokenError, make_client, sandbox_token
from app.main import create_app
from fastapi.testclient import TestClient


def test_empty_token_raises(monkeypatch) -> None:
    monkeypatch.delenv("TINKOFF_SANDBOX_TOKEN", raising=False)
    with pytest.raises(BrokerTokenError, match="TINKOFF_SANDBOX_TOKEN is empty"):
        sandbox_token()


def test_token_from_sandbox_env_only(monkeypatch) -> None:
    monkeypatch.setenv("INVEST_TOKEN", "live-secret")
    monkeypatch.setenv("TINKOFF_SANDBOX_TOKEN", "")
    with pytest.raises(BrokerTokenError):
        sandbox_token()
    monkeypatch.setenv("TINKOFF_SANDBOX_TOKEN", " sbx-1 ")
    assert sandbox_token() == "sbx-1"


def test_make_client_uses_sandbox_token() -> None:
    source = inspect.getsource(make_client)
    assert "sandbox_token()" in source
    assert "INVEST_TOKEN" not in source


def test_empty_token_api_json_not_traceback(monkeypatch) -> None:
    monkeypatch.delenv("TINKOFF_SANDBOX_TOKEN", raising=False)
    monkeypatch.setenv("APP_AUTH_TOKEN", "secret")
    app = create_app()

    @app.get("/_token")
    def _token() -> dict[str, str]:
        return {"token": sandbox_token()}

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/_token", headers={"X-App-Token": "secret"})
    assert response.status_code == 503
    assert response.json() == {
        "code": "broker_token",
        "message": "TINKOFF_SANDBOX_TOKEN is empty",
    }
    assert "Traceback" not in response.text
