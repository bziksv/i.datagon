from app.main import create_app
from fastapi.testclient import TestClient


def test_health() -> None:
    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_without_db(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    client = TestClient(create_app())
    response = client.get("/ready")
    assert response.status_code == 503


def test_version_unauthorized(monkeypatch) -> None:
    monkeypatch.setenv("APP_AUTH_TOKEN", "secret")
    client = TestClient(create_app())
    response = client.get("/version")
    assert response.status_code == 401
    assert response.json()["code"] == "401"
