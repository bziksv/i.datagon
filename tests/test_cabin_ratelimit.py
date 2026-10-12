from fastapi.testclient import TestClient

from app.main import create_app
from app.ops.ratelimit import IpRateLimit, client_ip


def test_ip_limit_blocks_after_n() -> None:
    limiter = IpRateLimit(limit=2, window_sec=60)
    assert limiter.allow("1.1.1.1", 0) is True
    assert limiter.allow("1.1.1.1", 1) is True
    assert limiter.allow("1.1.1.1", 2) is False
    assert limiter.allow("2.2.2.2", 2) is True
    assert client_ip({"X-Real-IP": "10.0.0.8"}, "127.0.0.1") == "10.0.0.8"
    assert client_ip({"X-Forwarded-For": "9.9.9.9"}, "127.0.0.1") == "9.9.9.9"
    assert client_ip({"X-Forwarded-For": "8.8.8.8"}, "203.0.113.9") == "203.0.113.9"
    limiter.reset("1.1.1.1")
    assert limiter.allow("1.1.1.1", 3) is True


def test_cabin_api_returns_429(monkeypatch) -> None:
    monkeypatch.setenv("APP_AUTH_TOKEN", "secret")
    monkeypatch.setenv("CABIN_RATE_PER_MIN", "2")
    client = TestClient(create_app())
    headers = {"X-App-Token": "secret"}
    assert client.get("/version", headers=headers).status_code == 200
    assert client.get("/version", headers=headers).status_code == 200
    limited = client.get("/version", headers=headers)
    assert limited.status_code == 429
    assert limited.json()["code"] == "429"
    assert client.get("/health").status_code == 200
