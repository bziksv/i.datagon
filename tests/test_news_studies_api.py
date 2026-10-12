from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from app.main import create_app
from app.models import NewsStudy
from app.news.events import new_event
from app.news.view import studies_view
from fastapi.testclient import TestClient


def test_studies_view_links_news_title() -> None:
    event = new_event(
        ts=datetime(2026, 10, 12, tzinfo=UTC),
        source="rss",
        source_id="1",
        title="Сбер отчитался",
        url="https://ex/sber",
        tickers=["SBER"],
    )
    study = NewsStudy(
        id=uuid4(),
        news_event_id=event.id,
        ticker="SBER",
        horizon_n=3,
        t_minus_ts=datetime(2026, 10, 11, tzinfo=UTC),
        t_plus_ts=datetime(2026, 10, 15, tzinfo=UTC),
        ret=Decimal("0.05"),
        payload={"title": "fallback"},
    )
    got = studies_view([study], [event])
    assert len(got["studies"]) == 1
    row = got["studies"][0]
    assert row["title"] == "Сбер отчитался"
    assert row["news_event_id"] == str(event.id)
    assert row["news_url"] == "https://ex/sber"
    assert row["ret"] == 0.05
    assert row["ticker"] == "SBER"


def test_news_studies_unauthorized(monkeypatch) -> None:
    monkeypatch.setenv("APP_AUTH_TOKEN", "secret")
    client = TestClient(create_app())
    assert client.get("/news/studies").status_code == 401


def test_news_studies_without_db(monkeypatch) -> None:
    monkeypatch.setenv("APP_AUTH_TOKEN", "secret")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    client = TestClient(create_app())
    assert (
        client.get("/news/studies", headers={"X-App-Token": "secret"}).status_code
        == 503
    )
