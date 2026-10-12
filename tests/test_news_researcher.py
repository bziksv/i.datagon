import inspect
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.agent import researcher
from app.agent.researcher import research_news
from app.broker.port import CandleBar
from app.models import AgentRun, NewsStudy
from app.news.events import new_event


def _ts(day: int) -> datetime:
    return datetime(2026, 10, day, 18, 0, tzinfo=UTC)


def _bars() -> list[CandleBar]:
    closes = ["100", "101", "102", "110", "111", "112"]
    return [
        CandleBar(
            ts=_ts(10 + i),
            o=Decimal(c),
            h=Decimal(c),
            low=Decimal(c),
            c=Decimal(c),
            v=Decimal("1"),
        )
        for i, c in enumerate(closes)
    ]


def test_researcher_writes_study_offline() -> None:
    event = new_event(
        ts=_ts(12) - timedelta(hours=2),
        source="rss",
        source_id="sber-1",
        title="Сбербанк",
        url="https://ex/sber",
        tickers=["SBER"],
    )
    run, studies = research_news([event], {"SBER": _bars()}, enabled=True)
    assert isinstance(run, AgentRun)
    assert run.role == "news_researcher"
    assert "offline" in run.input
    assert len(studies) == 1
    assert isinstance(studies[0], NewsStudy)
    assert studies[0].ticker == "SBER"


def test_researcher_silent_when_disabled() -> None:
    run, studies = research_news([], {}, enabled=False)
    assert run is None
    assert studies == []


def test_researcher_has_no_order_path() -> None:
    source = inspect.getsource(researcher)
    assert "new_proposal" not in source
    assert "propose_order" not in source
    assert "propose_weights" not in source
    assert "draft_order" not in source
    assert "Order(" not in source
    assert "post_order" not in source
    assert "place_order" not in source
