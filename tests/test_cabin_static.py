import re
from pathlib import Path

from app.main import create_app
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
CABIN = ROOT / "web" / "index.html"
CSS = ROOT / "web" / "cabin.css"
JS = ROOT / "web" / "cabin.js"
NGINX = ROOT / "deploy" / "nginx-i.datagon.ru.snippet.conf"

MENU = (
    "Обзор",
    "Портфель",
    "Стратегии",
    "Компании",
    "Рекомендации",
    "Агенты",
    "Новости",
    "Рынок",
    "Журнал",
    "Работа",
    "Настройки",
    "Помощь",
)

ROUTES = (
    "overview",
    "portfolio",
    "strategies",
    "companies",
    "recommendations",
    "agents",
    "news",
    "market",
    "journal",
    "work",
    "home",
    "candles",
    "settings",
    "help",
)


def test_cabin_shell_stage01_menu_and_router() -> None:
    html = CABIN.read_text()
    css = CSS.read_text()
    js = JS.read_text()
    assert "<!DOCTYPE html>" in html
    assert 'href="/cabin.css?v=3.3.87"' in html
    assert 'src="/cabin.js?v=3.3.87"' in html
    assert "webpack" not in html.lower()
    assert "react" not in html.lower()
    assert "vite" not in html.lower()
    assert "--bg:" in css
    for title in MENU:
        assert title in js
    for route in ROUTES:
        assert route in js
    assert "location.hash" in js
    assert "hashchange" in js
    assert "Обучение" in html
    assert "TINKOFF" not in html
    assert "TINKOFF" not in js


def test_cabin_help_product_stage23() -> None:
    js = JS.read_text()
    assert "help-map" in js
    assert "help-legend" in js
    assert "help-glossary" in js
    assert "help-security" in js
    assert "help-learn" in js
    assert "help-limits" in js
    assert "help-vault" in js
    assert "Пройти тур Обзора" in js
    assert "Сбросить все туры" in js
    assert "Ограничения продукта" in js
    assert "боевого торгового интерфейса" in js or "Боевой торговый интерфейс" in js
    assert "этапе 23" not in js
    assert "Карта кабинета" in js


def test_cabin_journal_ledger_stage22() -> None:
    js = JS.read_text()
    assert "renderJournalLedger" in js
    assert "LEDGER_ACCOUNT_RU" in js
    assert "LEDGER_REASON_RU" in js
    assert 'apiGet("/ledger")' in js
    assert "торговый кэш" in js
    assert "сейф прибыли" in js
    assert "депозит" in js
    assert "journal-deposit" in js
    assert "account_kind" in js
    assert "is-deposit" in js


def test_cabin_journal_orders_stage21() -> None:
    js = JS.read_text()
    assert "renderJournalOrders" in js
    assert "JOURNAL_TOUR_KEY" in js
    assert "ORDER_REJECT_RU" in js
    assert "ORDER_STATUS_RU" in js
    assert 'apiGet("/orders")' in js
    assert "Отклонено: включён стоп торговли" in js
    assert "reject_reason: killed" in js
    assert "order-filter-status" in js
    assert "order-filter-sleeve" in js
    assert "order-filter-ticker" in js
    assert "#/journal?tab=orders" in js
    assert "orderRejectLabel" in js


def test_cabin_market_rules_stage20() -> None:
    js = JS.read_text()
    assert "renderMarketRules" in js
    assert "marketRiskRules" in js
    assert "market-rule-kill" in js
    assert "Стоп торговли" in js
    assert "Тикер в вселенной" in js
    assert "Доля бумаги" in js
    assert "Доля рукава" in js
    assert "Дневной убыток" in js
    assert "Один вход на бар" in js
    assert "День отчёта" in js
    assert "market-kill" in js
    assert "где увидите отказ" in js
    assert "#/journal" in js
    assert "Зачем:" in js
    assert "Что увидите при отказе:" in js


def test_cabin_market_universe_stage19() -> None:
    js = JS.read_text()
    assert "renderMarketUniverse" in js
    assert "MARKET_TOUR_KEY" in js
    assert "UNIVERSE_REASON_RU" in js
    assert 'apiGet("/universe")' in js
    assert "В вселенной" in js
    assert "Состав ещё не наполнен ситом" in js
    assert "активна" in js
    assert "неактивна" in js
    assert "прошла сито" in js
    assert "market-universe-table" in js


def test_cabin_news_studies_stage18() -> None:
    js = JS.read_text()
    assert "renderNewsStudies" in js
    assert 'apiGet("/news/studies")' in js
    assert "news-lookahead" in js
    assert "Lookahead запрещён" in js or "lookahead" in js.lower()
    assert "Ещё не считалось" in js
    assert "не сигнал «покупай»" in js or "не торговый приказ" in js
    assert "formatRetPct" in js
    assert "news-studies-empty" in js


def test_cabin_news_feed_stage17() -> None:
    js = JS.read_text()
    assert "renderNewsFeed" in js
    assert "NEWS_TOUR_KEY" in js
    assert 'apiGet("/news")' in js
    assert "news-disclaimer" in js
    assert "не открывают сделки" in js
    assert "news-filters" in js
    assert "news-empty" in js
    assert "filterNewsRows" in js
    assert "открыть источник" in js


def test_cabin_agents_accept_reject_stage16() -> None:
    js = JS.read_text()
    assert "explainApproveResult" in js
    assert "Принято вами, но риск отклонил ордер" in js
    assert "data-approve" in js
    assert "data-reject" in js
    assert "/proposals/" in js
    assert "/approve" in js
    assert "/reject" in js
    assert "askConfirm" in js
    assert "agents-flash" in js
    assert "riskReasonLabel" in js
    assert "Действия — следующий этап" not in js


def test_cabin_agents_queue_banner_stage15() -> None:
    js = JS.read_text()
    css = CSS.read_text()
    assert "renderAgents" in js
    assert "AGENTS_TOUR_KEY" in js
    assert "agents-banner" in js
    assert "Фоновые агенты выключены" in js
    assert "планы появляются только из Рекомендаций" in js
    assert "Небезопасные старые планы" not in js
    assert "AGENTS_ENABLED" not in js
    assert "agents-how" in js
    assert "agents-stats" in js
    assert "Ждут решения" in js
    assert "Недавние" in js
    assert "sortProposalsProposedFirst" in js
    assert "Подробнее" in js
    assert "JSON wall" not in js
    assert "proposalSummary" in js
    assert "attention.calm" in css
    assert "agents-how" in css
    assert "status-chip.is-wait" in css
    assert "tab=proposed" in js or 'tab === "proposed"' in js


def test_cabin_signals_language_filters_stage14() -> None:
    js = JS.read_text()
    assert "SIGNAL_KIND_RU" in js
    assert '"buy": "покупка"' in js or "buy: \"покупка\"" in js
    assert "продажа" in js
    assert "плоско" in js
    assert "выход" in js
    assert "strategies-filters" in js
    assert "signal-filter-ticker" in js
    assert "signal-filter-kind" in js
    assert "Нет пульса воркера" in js
    assert "За выбранный период решений не было." in js
    assert "Нет сигналов по выбранным фильтрам" in js
    assert "filterSignals" in js
    assert "worker_alive" in js


def test_cabin_strategies_card_stage13() -> None:
    js = JS.read_text()
    assert "renderStrategiesSleeveCard" in js
    assert "SLEEVE_HOWTO" in js
    assert "strategies-howto" in js
    assert "strategies-card-pnl" in js
    assert '/sleeves/" + encodeURIComponent(sleeveId)' in js or "/sleeves/" in js
    assert "sma_cross" in js
    assert "donchian_breakout" in js
    assert "rsi_reversion" in js
    assert "ema_scalp" in js
    assert "overnight_bounce" in js
    assert "Как устроен" in js
    # симметрия: все рукава из одного списка / howto
    assert "ACTIVE_SLEEVE_IDS" in js
    assert js.index("donchian_breakout") > 0


def test_cabin_strategies_compare_stage12() -> None:
    js = JS.read_text()
    assert "renderStrategiesCompare" in js
    assert "STRATEGIES_TOUR_KEY" in js
    assert "Пересечение средних" in js
    assert "Пробой Дончиана" in js
    assert "RSI-возврат" in js
    assert "EMA-скальп" in js
    assert "sma_cross" in js
    assert "donchian_breakout" in js
    assert "rsi_reversion" in js
    assert "ema_scalp" in js
    assert "overnight_bounce" in js
    assert "#/strategies/" in js
    assert "открыть" in js
    assert "зафиксировано" in js
    assert "на бумаге" in js
    assert 'apiGet("/sleeves")' in js
    assert "normalizeSleeves" in js
    assert "strategies-row-sma_cross" in js
    assert "strategies-row-donchian_breakout" in js
    assert "strategies-row-rsi_reversion" in js
    assert "strategies-row-ema_scalp" in js
    assert "vol_scalp" in js
    assert "Волатильный скальп" in js
    assert '"overnight_bounce"' in js


def test_cabin_portfolio_alloc_drift_stage11() -> None:
    js = JS.read_text()
    assert "renderPortfolioAllocation" in js
    assert "renderPortfolioDrift" in js
    assert "portfolio-alloc-table" in js
    assert "portfolio-drift-empty" in js
    assert 'apiGet("/allocation")' in js
    assert "/admin/drift?sandbox_cash=" in js
    assert "sandboxCashKnown" in js
    assert "не показывает «сходятся»" in js or "не притворяется" in js
    assert "нулевое расхождение" in js or "расхождение 0" in js
    # без известного sandbox нельзя рисовать ложную сходимость
    assert "sandboxCashKnown === null" in js or 'sandboxCashKnown === ""' in js


def test_cabin_portfolio_vault_stage10() -> None:
    js = JS.read_text()
    css = CSS.read_text()
    assert "renderPortfolioVault" in js
    assert "portfolio-vault-panel" in js
    assert "сейчас откладываем" in js
    assert "Как считается" in js
    assert "до перекрытия" in js
    assert 'apiGet("/vault")' in js
    assert "нереализованн" in js
    assert ".progress" in css
    assert ".fold" in css


def test_cabin_portfolio_positions_stage09() -> None:
    js = JS.read_text()
    assert "renderPortfolioPositions" in js
    assert "portfolio-positions" in js
    assert "Позиций нет" in js
    assert "#/strategies" in js
    assert "количество" in js
    assert "средняя цена" in js
    assert "оценка" in js
    assert "доля" in js
    assert "refreshPortfolioBook" in js
    assert 'apiGet("/portfolio")' in js


def test_cabin_portfolio_capital_stage08() -> None:
    js = JS.read_text()
    css = CSS.read_text()
    assert "renderPortfolio" in js
    assert "renderPortfolioCapital" in js
    assert "стоимость счёта" in js
    assert "свободный кэш" in js
    assert "сейф прибыли" in js
    assert "Источник: журнал проводок + позиции" in js
    assert "не баланс экрана" in js or "лабораторной книги" in js
    assert "whatis" in js
    assert "startPortfolioTour" in js
    assert "PORTFOLIO_TOUR_KEY" in js
    assert 'equity"' not in js or "стоимость счёта" in js
    assert ".tabs" in css
    assert ".disclaimer" in css
    assert ".whatis" in css


def test_cabin_queue_badge_stage07() -> None:
    html = CABIN.read_text()
    js = JS.read_text()
    css = CSS.read_text()
    assert 'id="queue-badge"' in html
    assert "#/agents?tab=proposed" in html or "agents?tab=proposed" in js
    assert "renderQueueBadge" in js
    assert "refreshProposals" in js
    assert "queueBadgeLabel" in js
    assert "ждут решения" in js
    assert ".queue-badge" in css
    assert "queue-badge[hidden]" in css


def test_cabin_overview_stage06() -> None:
    js = JS.read_text()
    css = CSS.read_text()
    html = CABIN.read_text()
    assert 'id="page-body"' in html
    assert "renderOverview" in js
    assert "overview-capital" in js
    assert "overview-queue" in js
    assert "overview-sleeves" in js
    assert "overview-attention" in js
    assert "стоимость счёта" in js
    assert "свободный кэш" in js
    assert "сейф прибыли" in js
    assert "Подробнее в Портфеле" in js
    assert "Очередь решений" in js
    assert "startOverviewTour" in js
    assert "OVERVIEW_TOUR_KEY" in js
    assert "/proposals" in js
    assert "/sleeves" in js
    assert "ledger" not in js.lower() or "Полный ledger" not in js
    assert ".metrics" in css
    assert ".proposal-card" in css


def test_cabin_tour_engine_stage05() -> None:
    html = CABIN.read_text()
    js = JS.read_text()
    tour_js = (ROOT / "web" / "tour.js").read_text()
    tour_css = (ROOT / "web" / "tour.css").read_text()
    assert 'href="/tour.css?v=3.3.24"' in html
    assert 'src="/tour.js?v=3.3.24"' in html
    assert "CabinTour" in tour_js
    assert "cabin_tour_v1:" in tour_js
    assert "resetAll" in tour_js
    assert "data-tour" in tour_js
    assert ".tour-spotlight" in tour_css
    assert "CabinTour.start" in js or "CabinTour.start" in tour_js
    assert "runTour" in js
    assert "startHelpDemoTour" in js
    assert "help-demo-tour" in js
    assert "Демо-тур (5 шагов)" in js


def test_cabin_kill_confirm_stage04() -> None:
    html = CABIN.read_text()
    js = JS.read_text()
    css = CSS.read_text()
    assert 'id="btn-kill"' in html
    assert 'id="btn-unkill"' in html
    assert 'id="confirm-modal"' in html
    assert 'id="kill-banner"' in html
    assert "Стоп торговлю" in html
    assert "Снять стоп" in html
    assert "Остановить торговлю?" in js
    assert "Снять стоп?" in js
    assert "askConfirm" in js
    assert "requestKill" in js
    assert 'fetch(path' in js or 'method: "POST"' in js
    assert 'method: "POST"' in js
    assert "/kill" in js
    assert "/unkill" in js
    assert "автоматически не закрываются" in js
    assert ".modal" in css
    assert "button.danger" in css


def test_cabin_status_pills_stage03() -> None:
    html = CABIN.read_text()
    js = JS.read_text()
    css = CSS.read_text()
    assert 'id="status-strip"' in html
    assert 'id="btn-refresh"' in html
    assert "Обновить" in html
    assert "status-pill" in css
    assert "renderStatus" in js
    assert "humanBeat" in js
    assert "Система" in js
    assert "Воркер" in js
    assert "Торговля" in js
    assert "Агенты" in js
    assert "выключены" in js
    assert "стоп включён" in js
    assert "можно выставлять" in js
    assert 'fetchJson("/status"' in js or 'fetch("/status"' in js
    assert "app-footer" in html


def test_cabin_gate_stage02_token_session() -> None:
    html = CABIN.read_text()
    js = JS.read_text()
    assert 'id="gate"' in html
    assert 'id="app"' in html
    assert 'id="app-token"' in html
    assert "Войти в кабинет" in html
    assert "Сменить токен" in html
    assert "Запомнить на этом устройстве" in html
    assert "APP_AUTH_TOKEN" in html
    assert "не токен Тинькоффа" in html
    assert 'localStorage.getItem("app_token")' in js or 'TOKEN_KEY = "app_token"' in js
    assert 'fetchJson("/status"' in js or 'fetch("/status"' in js
    assert "X-App-Token" in js
    assert "Токен не принят" in js
    assert "GATE_TOUR_KEY" in js or '"gate"' in js
    assert 'byId("app").hidden' in js or "setAuthed" in js
    assert "hidden" in html


FORBIDDEN = (
    "tinkoff.ru",
    "tinkoff-invest",
    "invest-public-api",
    "TINKOFF_SANDBOX",
    "TINKOFF_LIVE",
    "invest-python",
    "sandbox-invest",
)


def test_web_has_no_tinkoff_url_or_token() -> None:
    root = ROOT / "web"
    offenders: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        text = path.read_text(errors="ignore")
        lowered = text.lower()
        for needle in FORBIDDEN:
            if needle.lower() in lowered:
                offenders.append(f"{path.name}:{needle}")
        if re.search(r"\bt\.[A-Za-z0-9_-]{20,}", text):
            offenders.append(f"{path.name}:t.*token")
    assert offenders == []


def test_cabin_fetches_same_origin_paths() -> None:
    for path in (CABIN, JS, CSS):
        text = path.read_text()
        assert "http://" not in text
        assert "https://" not in text
        assert "cors" not in text.lower()
        assert "Access-Control" not in text
    for url in re.findall(r'fetch\((["\'])([^"\']+)\1', JS.read_text()):
        path = url[1]
        assert path.startswith("/")
        assert not path.startswith("//")


def test_nginx_serves_cabin_on_same_host() -> None:
    text = NGINX.read_text()
    assert "root $root_path/web;" in text
    assert "try_files /index.html @api;" in text
    assert "proxy_pass http://127.0.0.1:8000;" in text
    assert "Access-Control" not in text


def test_cabin_assets_public_without_token(monkeypatch) -> None:
    monkeypatch.setenv("APP_AUTH_TOKEN", "secret")
    client = TestClient(create_app())
    page = client.get("/")
    assert page.status_code == 200
    assert "Войти в кабинет" in page.text
    assert client.get("/cabin.css").status_code == 200
    assert client.get("/cabin.js").status_code == 200
    assert client.get("/tour.css").status_code == 200
    assert client.get("/tour.js").status_code == 200
    assert client.get("/portfolio").status_code == 401
    assert client.get("/status", headers={"X-App-Token": "secret"}).status_code in {
        200,
        503,
    }
