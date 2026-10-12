from pathlib import Path

from app.main import create_app
from fastapi.testclient import TestClient


def test_fundamentals_unauthorized(monkeypatch) -> None:
    monkeypatch.setenv("APP_AUTH_TOKEN", "secret")
    client = TestClient(create_app())
    assert client.get("/fundamentals").status_code == 401
    assert client.get("/recommendations").status_code == 401


def test_cabin_advisory_ui() -> None:
    js = Path("web/cabin.js").read_text()
    assert 'id: "companies"' in js
    assert 'id: "recommendations"' in js
    assert "renderCompanies" in js
    assert "renderRecommendations" in js
    assert 'apiGet("/fundamentals")' in js
    assert 'apiGet("/recommendations' in js
    assert 'apiPost("/recommendations/propose"' in js
    assert 'apiPost("/fundamentals/demo"' in js
    assert "recs-disclaimer" in js
    assert "fund_screener" in js
    assert Path("TZ-ADVISORY.md").exists()
