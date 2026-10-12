"""Агент news_researcher: только offline, пишет study, не proposal ордера."""

from collections.abc import Mapping, Sequence

from app.agent.flag import agents_enabled
from app.agent.runs import record_run
from app.broker.port import CandleBar
from app.models import AgentRun, NewsEvent, NewsStudy
from app.news.study import DEFAULT_HORIZON_N, run_news_studies

ROLE = "news_researcher"


def research_news(
    events: Sequence[NewsEvent],
    bars_by_ticker: Mapping[str, Sequence[CandleBar]],
    *,
    n: int = DEFAULT_HORIZON_N,
    enabled: bool | None = None,
) -> tuple[AgentRun | None, list[NewsStudy]]:
    if not agents_enabled(enabled):
        return None, []
    studies = run_news_studies(events, bars_by_ticker, n=n)
    run = record_run(
        role=ROLE,
        input=f"offline window studies events={len(events)} n={n}",
        output=f"wrote {len(studies)} news_studies",
        secrets=(),
    )
    return run, studies
