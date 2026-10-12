"""Этап 26: Mobile + a11y — bottom tabs, scroll таблиц, клавиатура в модалке."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "web" / "index.html"
JS = ROOT / "web" / "cabin.js"
CSS = ROOT / "web" / "cabin.css"
TOUR_CSS = ROOT / "web" / "tour.css"
TZ = ROOT / "TZ-CABIN.md"


def test_mobile_primary_and_more() -> None:
    js = JS.read_text()
    html = HTML.read_text()
    assert "MOBILE_PRIMARY_IDS" in js
    assert "MOBILE_MORE_IDS" in js
    for route in ("overview", "portfolio", "recommendations", "companies", "settings"):
        assert route in js.split("MOBILE_PRIMARY_IDS")[1].split("]")[0]
    for route in ("strategies", "agents", "news", "market", "journal", "help"):
        assert route in js.split("MOBILE_MORE_IDS")[1].split("]")[0]
    assert "Ещё" in js
    assert 'id="mobile-more"' in html
    assert "mobile-more-sheet" in html
    assert "skip-link" in html
    assert "К содержимому" in html


def test_table_scroll_and_sticky_ticker() -> None:
    js = JS.read_text()
    css = CSS.read_text()
    assert "wrapTableScroll" in js
    assert "table-scroll" in css
    assert "is-sticky-first" in css
    assert "position: sticky" in css
    assert 'wrapTableScroll(' in js
    assert "portfolio-positions-table" in js
    assert "market-universe-table" in js
    assert "journal-orders-table" in js


def test_modal_keyboard_a11y() -> None:
    js = JS.read_text()
    css = CSS.read_text()
    assert "confirmReturnFocus" in js
    assert 'event.key === "Escape"' in js
    assert 'event.key === "Enter"' in js
    assert 'event.key === "Tab"' in js
    assert ":focus-visible" in css
    assert "skip-link" in css
    assert "prefers-reduced-motion" in css
    assert "prefers-reduced-motion" in TOUR_CSS.read_text()


def test_mobile_layout_390() -> None:
    css = CSS.read_text()
    assert "@media (max-width: 820px)" in css
    assert "position: fixed" in css
    assert "safe-area-inset-bottom" in css
    assert "@media (max-width: 420px)" in css


def test_tz_stage26_done() -> None:
    text = TZ.read_text()
    assert "### Этап 26" in text
    chunk = text.split("### Этап 26")[1].split("### Этап 27")[0]
    assert "**done**" in chunk
    for item in ("bottom", "sticky", "Escape", "Enter", "390"):
        assert item.lower() in chunk.lower() or item in chunk
