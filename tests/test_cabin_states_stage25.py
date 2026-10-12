"""Матрица состояний §E: loading/error без ложных нулей."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / "web" / "cabin.js"
CSS = ROOT / "web" / "cabin.css"
TZ = ROOT / "TZ-CABIN.md"


def test_humanize_http_errors() -> None:
    js = JS.read_text()
    assert "humanizeHttpError" in js
    assert "Сессия или токен не приняты" in js
    assert "Слишком частые запросы" in js
    assert "API недоступен или не готов" in js
    assert "Нет связи с API" in js


def test_skeleton_and_block_error() -> None:
    js = JS.read_text()
    css = CSS.read_text()
    assert "skeletonHtml" in js
    assert "blockErrorHtml" in js
    assert "loadErrors" in js
    assert ".skeleton" in css
    assert "не подставляются нулями" in js
    assert "это не «0 ордеров»" in js or "не «0 ордеров»" in js


def test_portfolio_error_not_silent_zero() -> None:
    js = JS.read_text()
    assert "Книга ещё не загрузилась. Это не нулевой баланс" in js
    assert "setLoadError(\"portfolio\"" in js or "setLoadError('portfolio'" in js


def test_tz_matrix_checklist_checked() -> None:
    text = TZ.read_text()
    assert "### Этап 25" in text
    assert "**done**" in text.split("### Этап 25")[1].split("### Этап 26")[0]
    for item in (
        "нет токена",
        "загрузка",
        "пусто (бизнес)",
        "401",
        "429",
        "503",
        "частичный фейл",
        "стоп включён",
    ):
        assert item in text
