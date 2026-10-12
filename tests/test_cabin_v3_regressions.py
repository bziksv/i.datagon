"""Регрессии, найденные полным аудитом кабинета v3."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
JS = (ROOT / "web" / "cabin.js").read_text()
CSS = (ROOT / "web" / "cabin.css").read_text()
HTML = (ROOT / "web" / "index.html").read_text()


def test_light_theme_overrides_legacy_dark_components() -> None:
    v3 = CSS.split("v3 light-theme migration for the remaining detailed screens.")[1]
    assert "#app .data-table th" in v3
    assert "background: #f1f4f1" in v3
    assert "#app .decision-flow strong" in v3
    assert "color: var(--text)" in v3
    assert "#app .audit-event__head strong" in v3
    assert "#app .position-card" in v3
    assert "#app .experiment-report" in v3


def test_weights_summary_accepts_api_array_contract() -> None:
    summary = JS.split("function proposalSummary")[1].split(
        "function proposalWillDo"
    )[0]
    assert "Array.isArray(weights)" in summary
    assert "item.sleeve" in summary
    assert "pctLabel(item.weight)" in summary


def test_strategy_detail_has_real_loading_state() -> None:
    card = JS.split("function renderStrategiesSleeveCard")[1].split(
        "function renderStrategies"
    )[0]
    assert "sleeveDetailLoading" in card
    assert "Загружаем результат, позиции и сигналы рукава" in card
    assert "skeletonHtml" in card


def test_ledger_error_and_weekly_unavailable_are_explicit() -> None:
    ledger = JS.split("function renderJournalLedger")[1].split(
        "function renderJournalAudit"
    )[0]
    assert "loadErrors.ledger" in ledger
    assert 'blockErrorHtml("ledger")' in ledger
    overview = JS.split("function renderOverview")[1].split(
        "function renderHelpPanel"
    )[0]
    assert "weekly.available === false" in overview
    assert '"нет данных"' in overview


def test_tabs_are_url_addressable_and_accessible() -> None:
    assert "function setRouteTab" in JS
    for route in ("portfolio", "news", "market", "journal"):
        assert f'setRouteTab("{route}"' in JS
    assert 'role="tablist"' in JS
    assert 'role="tab"' in JS
    assert 'aria-selected="' in JS
    assert 'setAttribute("aria-current", "page")' in JS


def test_gate_skip_link_and_ru_labels() -> None:
    assert '<a class="skip-link" href="#gate-form">' in HTML
    for label in (
        "Open PnL",
        "<dt>Qty",
        "<dt>Cost",
        "<dt>Mark",
        "<dt>Weight",
        "01 / THESIS",
        "Audit trail",
        "CHAIN VALID",
    ):
        assert label not in JS
    assert "MARK_QUALITY_RU" in JS
    assert "help-cabin-version" in JS
    assert "Одиннадцать разделов" in JS


def test_wide_tables_do_not_expand_the_page_grid() -> None:
    assert "grid-template-columns: minmax(0, 1fr)" in CSS
    assert "#page-body > *" in CSS
    table_scroll = CSS.split(".table-scroll {", 1)[1].split("}", 1)[0]
    assert "overflow-x: auto" in table_scroll
    assert "width: 100%" in table_scroll
    assert "min-width: 0" in table_scroll
    assert 'inline: "nearest"' in JS
