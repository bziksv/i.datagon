"""Этап 27: parallel fetch, per-block error/skeleton, double-refresh, timeout."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / "web" / "cabin.js"
TZ = ROOT / "TZ-CABIN.md"


def test_fetch_timeout_and_copy() -> None:
    js = JS.read_text()
    assert "FETCH_TIMEOUT_MS" in js
    assert "fetchJson" in js
    assert "AbortController" in js
    assert "Превышено время ожидания ответа API" in js
    assert 'status === "timeout"' in js or "status === 'timeout'" in js


def test_double_refresh_guard() -> None:
    js = JS.read_text()
    assert "refreshBusy" in js
    assert "aria-busy" in js
    assert "if (refreshBusy)" in js


def test_parallel_overview_independent_of_news() -> None:
    js = JS.read_text()
    overview = js.split("function loadOverviewData")[1].split("function renderOverview")[0]
    assert "Promise.all" in overview
    assert "/sleeves" in overview
    assert "refreshProposals" in overview
    assert 'apiGet("/news")' not in overview
    assert "refreshNews" not in overview
    assert "setBlockLoading" in overview
    assert "blockLoading" in js
    assert "isBlockLoading" in js


def test_news_per_block_error_does_not_wipe_others() -> None:
    js = JS.read_text()
    news = js.split("function refreshNews")[1].split("function marketTabsHtml")[0]
    assert "Promise.all" in news
    assert 'setLoadError("news"' in news or "setLoadError('news'" in news
    assert 'setLoadError("studies"' in news or "setLoadError('studies'" in news
    assert "clearLoadError" in news
    assert "skeletonHtml" in js


def test_tz_stage27_done() -> None:
    text = TZ.read_text()
    assert "### Этап 27" in text
    chunk = text.split("### Этап 27")[1].split("### Этап 28")[0]
    assert "**done**" in chunk
    for item in ("parallel", "timeout", "double", "skeleton", "503"):
        assert item.lower() in chunk.lower()
