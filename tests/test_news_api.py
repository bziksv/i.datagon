from datetime import UTC, datetime

from app.main import create_app
from app.news.events import new_event
from app.news.view import news_view
from fastapi.testclient import TestClient


def test_news_view_orders_newest_first() -> None:
    older = new_event(
        ts=datetime(2026, 1, 1, tzinfo=UTC),
        source="rss",
        source_id="1",
        title="Old",
        url="https://ex/old",
        tickers=["SBER"],
    )
    newer = new_event(
        ts=datetime(2026, 2, 1, tzinfo=UTC),
        source="rss",
        source_id="2",
        title="New",
        url="https://ex/new",
        tickers=["GAZP"],
    )
    got = news_view([older, newer])
    assert [row["title"] for row in got["news"]] == ["New", "Old"]
    assert got["news"][0]["tickers"] == ["GAZP"]
    assert "url" in got["news"][0]


def test_news_unauthorized(monkeypatch) -> None:
    monkeypatch.setenv("APP_AUTH_TOKEN", "secret")
    client = TestClient(create_app())
    assert client.get("/news").status_code == 401


def test_news_without_db(monkeypatch) -> None:
    monkeypatch.setenv("APP_AUTH_TOKEN", "secret")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    client = TestClient(create_app())
    assert client.get("/news", headers={"X-App-Token": "secret"}).status_code == 503
