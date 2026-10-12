"""Этап 29: приёмочные J1–J9 — чеклист + якоря UI + туры не блокируют стоп."""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
ACCEPT = ROOT / "CABIN-ACCEPTANCE.md"
JS = ROOT / "web" / "cabin.js"
TOUR_JS = ROOT / "web" / "tour.js"
HTML = ROOT / "web" / "index.html"
TZ = ROOT / "TZ-CABIN.md"


def test_acceptance_checklist_exists() -> None:
    text = ACCEPT.read_text()
    assert "J1" in text and "J9" in text
    for j in range(1, 10):
        assert f"## J{j}" in text or f"J{j} —" in text
    assert "Перед стартом" in text
    assert "Закрыть" in text
    assert "Esc" in text
    assert "Критерий закрытия этапа 29" in text


def test_j1_status_chrome() -> None:
    html = HTML.read_text()
    js = JS.read_text()
    assert 'id="status-strip"' in html
    assert 'id="btn-refresh"' in html
    assert "status-pill" in js
    assert "можно выставлять" in js or "стоп включён" in js
    assert "app-footer" in html
    assert "статус обновлён" in js


def test_j2_money_and_vault_phase() -> None:
    js = JS.read_text()
    assert "стоимость счёта" in js
    assert "свободный кэш" in js
    assert "сейф прибыли" in js
    assert "portfolio-vault-phase" in js
    assert "portfolio-disclaimer" in js
    assert "paper" in js.lower()


def test_j3_strategies() -> None:
    js = JS.read_text()
    assert "strategies-table" in js
    assert "strategies-signals" in js
    assert "strategies-howto" in js
    assert "Пересечение средних" in js
    assert "Пробой Дончиана" in js


def test_j4_agents_decide() -> None:
    js = JS.read_text()
    assert "agents-waiting" in js
    assert "agents-actions" in js
    assert "Принять" in js
    assert "Отклонить" in js
    assert "askConfirm" in js


def test_j5_news_research() -> None:
    js = JS.read_text()
    assert "news-feed" in js
    assert "news-studies" in js
    assert "не открывают сделки" in js or "сами сделки не открывают" in js


def test_j6_reject_reason_ru() -> None:
    js = JS.read_text()
    assert "ORDER_REJECT_RU" in js
    assert "Отклонено: включён стоп торговли" in js
    assert "journal-orders" in js
    assert "market-rules" in js


def test_j7_kill_confirm_and_tour_yields() -> None:
    js = JS.read_text()
    html = HTML.read_text()
    assert 'id="btn-kill"' in html
    assert 'id="confirm-modal"' in html
    assert "requestKill" in js
    assert "askConfirm" in js
    assert "CabinTour.isActive()" in js
    assert "CabinTour.stop(true)" in js
    kill_fn = js.split("function requestKill")[1].split("function humanizeHttpError")[0]
    assert "CabinTour.stop" in kill_fn


def test_j8_tours_all_sections_and_dismiss() -> None:
    js = JS.read_text()
    tour = TOUR_JS.read_text()
    for key in (
        "GATE_TOUR_KEY",
        "OVERVIEW_TOUR_KEY",
        "PORTFOLIO_TOUR_KEY",
        "STRATEGIES_TOUR_KEY",
        "AGENTS_TOUR_KEY",
        "NEWS_TOUR_KEY",
        "MARKET_TOUR_KEY",
        "JOURNAL_TOUR_KEY",
        "HELP_TOUR_KEY",
    ):
        assert key in js
    assert 'textContent = "Закрыть"' in tour
    assert 'event.key === "Escape"' in tour
    assert "startHelpDemoTour" in js
    assert "Сбросить все туры" in js or "resetAll" in js


def test_j9_freshness_and_paper_disclaimer() -> None:
    js = JS.read_text()
    html = HTML.read_text()
    assert "Данные paper-книги" in js or "Данные paper-книги" in html
    assert "portfolio-disclaimer" in js
    assert "не баланс экрана" in js or "не экран" in js
    assert "blockErrorHtml" in js


def test_d2_tour_min_steps() -> None:
    js = JS.read_text()
    mins = {
        "startGateTour": 2,
        "startOverviewTour": 6,
        "startPortfolioTour": 5,
        "startStrategiesTour": 4,
        "startAgentsTour": 4,
        "startNewsTour": 4,
        "startMarketTour": 4,
        "startJournalTour": 3,
        "startHelpDemoTour": 2,
    }
    for fn, need in mins.items():
        # Граница по top-level function (два пробела) — не резать вложенные function ()
        chunk = js.split(f"function {fn}")[1].split("\n  function ")[0]
        count = len(re.findall(r"\btour:\s*", chunk))
        assert count >= need, f"{fn}: {count} < {need}"


def test_tz_stage29_done() -> None:
    text = TZ.read_text()
    assert "### Этап 29" in text
    chunk = text.split("### Этап 29")[1].split("### Этап 30")[0]
    assert "**done**" in chunk
    assert "CABIN-ACCEPTANCE.md" in chunk or "J1–J9" in chunk
