from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from app.db import get_db
from app.main import create_app
from app.models import Candle, Fundamental, Instrument, UniverseMember
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
    assert 'apiPost("/fundamentals/refresh"' in js
    assert 'apiPost("/fundamentals/demo"' not in js
    assert "companies-demo" not in js
    assert "recs-disclaimer" in js
    assert "fund_screener" in js
    assert "Одобрить paper-план" in js
    assert "В T‑Invest sandbox и на биржу ничего не отправляется" in js
    assert Path("TZ-ADVISORY.md").exists()


class _RecommendationSession:
    def __init__(self, *, active: bool = True, stale: bool = False) -> None:
        self.instrument = Instrument(
            id=uuid4(),
            ticker="SBER",
            lot=10,
            currency="RUB",
            class_code="TQBR",
        )
        self.member = UniverseMember(
            id=uuid4(),
            instrument_id=self.instrument.id,
            reason="test",
            active=active,
        )
        self.candle = Candle(
            id=uuid4(),
            instrument_id=self.instrument.id,
            tf="1d",
            ts=datetime.now(UTC) - (timedelta(days=3) if stale else timedelta()),
            o=300,
            h=305,
            low=295,
            c=300,
            v=1000,
        )
        self.fundamental = Fundamental(
            ticker="SBER",
            asset_uid="asset-sber",
            ts=datetime.now(UTC),
            pe_ratio_ttm=5.5,
            price_to_book_ttm=0.8,
            eps_ttm=45,
            market_capitalization=1,
            raw={"roe": 0.22, "dividend_yield_daily_ttm": 0.09},
        )

    async def scalars(self, stmt):
        entity = stmt.column_descriptions[0].get("entity")
        if entity is Fundamental:
            return [self.fundamental]
        if entity is UniverseMember:
            return [self.member] if self.member.active else []
        if entity is Instrument:
            return [self.instrument]
        if entity is Candle:
            return [self.candle]
        return []


async def _recommendation_db() -> AsyncIterator[_RecommendationSession]:
    yield _RecommendationSession()


async def _stale_recommendation_db() -> AsyncIterator[_RecommendationSession]:
    yield _RecommendationSession(stale=True)


def test_recommendation_proposal_freezes_fresh_lot_plan(
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setenv("APP_AUTH_TOKEN", "secret")
    monkeypatch.setenv("PROPOSALS_PATH", str(tmp_path / "proposals.json"))
    app = create_app()
    app.dependency_overrides[get_db] = _recommendation_db
    response = TestClient(app).post(
        "/recommendations/propose",
        headers={"X-App-Token": "secret"},
        json={"limit": 5, "min_score": 10, "stop_pct": 0.05},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    payload = body["proposals"][0]["payload"]
    assert payload["qty"] == payload["lot"] == 10
    assert payload["entry_price"] == 300
    assert payload["stop"] == 285
    assert payload["price_as_of"]
    assert payload["execution_mode"] == "paper_book"


def test_recommendation_proposal_skips_stale_market_price(
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setenv("APP_AUTH_TOKEN", "secret")
    monkeypatch.setenv("PROPOSALS_PATH", str(tmp_path / "proposals.json"))
    app = create_app()
    app.dependency_overrides[get_db] = _stale_recommendation_db
    response = TestClient(app).post(
        "/recommendations/propose",
        headers={"X-App-Token": "secret"},
        json={"limit": 5, "min_score": 10},
    )
    assert response.status_code == 200
    assert response.json()["count"] == 0
    assert response.json()["skipped"] == [
        {"ticker": "SBER", "reason": "market_price_stale"}
    ]
