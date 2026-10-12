import time

from app.ops.guest_link import (
    guest_cabin_url,
    mint_guest_token,
    token_accepted,
    verify_guest_token,
)
from app.main import create_app
from fastapi.testclient import TestClient


def test_guest_token_roundtrip(monkeypatch) -> None:
    monkeypatch.setenv("APP_AUTH_TOKEN", "cabin-secret")
    now = time.time()
    token = mint_guest_token(hours=24, now=now)
    assert verify_guest_token(token, now=now + 60)
    assert not verify_guest_token(token, now=now + 25 * 3600)
    assert token_accepted(token, "cabin-secret")
    assert token_accepted("cabin-secret", "cabin-secret")
    assert not token_accepted("wrong", "cabin-secret")
    assert guest_cabin_url(token).startswith("https://i.datagon.ru/?access=")


def test_guest_token_api(monkeypatch) -> None:
    monkeypatch.setenv("APP_AUTH_TOKEN", "cabin-secret")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    client = TestClient(create_app())
    token = mint_guest_token(hours=1)
    # /health public
    assert client.get("/health").status_code == 200
    # protected with guest
    response = client.get("/version", headers={"X-App-Token": token})
    assert response.status_code == 200
    assert client.get("/version", headers={"X-App-Token": "nope"}).status_code == 401
