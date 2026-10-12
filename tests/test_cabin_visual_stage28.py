"""Этап 28: spacing scale, radius tokens, button hierarchy, motion, visual QA."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = ROOT / "web" / "cabin.css"
TOUR_CSS = ROOT / "web" / "tour.css"
TZ = ROOT / "TZ-CABIN.md"


def test_spacing_and_radius_tokens() -> None:
    css = CSS.read_text()
    for token in (
        "--space-1:",
        "--space-2:",
        "--space-3:",
        "--space-4:",
        "--space-5:",
        "--space-6:",
        "--radius:",
        "--radius-sm:",
        "--radius-pill:",
        "--motion:",
    ):
        assert token in css
    assert "font-variant-numeric: tabular-nums" in css


def test_button_hierarchy() -> None:
    css = CSS.read_text()
    assert "button.primary" in css
    assert "button.ghost" in css
    assert "button.danger" in css
    assert "Button hierarchy" in css or "primary > default" in css


def test_motion_two_to_three() -> None:
    css = CSS.read_text()
    tour = TOUR_CSS.read_text()
    assert "cabin-badge-in" in css
    assert "@keyframes cabin-badge-in" in css
    assert "box-shadow: 0 0 0 3px rgba(" in css
    assert ".dot.bad" in css
    assert "180ms" in tour or "var(--motion)" in css
    assert "--motion: 180ms" in css


def test_table_density_and_overview_air() -> None:
    css = CSS.read_text()
    assert 'data-tour="journal-orders"' in css or "[data-tour=\"journal-orders\"]" in css
    assert 'data-tour="overview-capital"' in css or "[data-tour=\"overview-capital\"]" in css
    assert "min-height: 7.5rem" in css or "min-height: 3.25rem" in css


def test_tz_stage28_visual_qa() -> None:
    text = TZ.read_text()
    assert "### Этап 28" in text
    chunk = text.split("### Этап 28")[1].split("### Этап 29")[0]
    assert "**done**" in chunk
    assert "Visual QA" in chunk or "visual QA" in chunk.lower() or "Визуальный QA" in chunk
    for item in ("spacing", "radius", "motion", "button"):
        assert item.lower() in chunk.lower()
