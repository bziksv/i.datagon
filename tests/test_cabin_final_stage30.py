"""Этап 30+: финальная приёмка — версия UI, TZ-ссылки, known limitations."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / "web" / "cabin.js"
FINAL = ROOT / "CABIN-FINAL.md"
ACCEPT = ROOT / "CABIN-ACCEPTANCE.md"
TZ = ROOT / "TZ.md"
TZ_CABIN = ROOT / "TZ-CABIN.md"


def test_cabin_ui_version_in_help() -> None:
    js = JS.read_text()
    assert "CABIN_UI_VERSION" in js
    assert 'CABIN_UI_VERSION = "v3.3.11"' in js
    assert "help-version" in js
    assert "help-cabin-version" in js
    assert "кабинет" in js
    assert "help-known-limits" in js
    assert "кабинет " in js  # footer


def test_final_checklist_artifact() -> None:
    text = FINAL.read_text()
    assert "кабинет" in text.lower()
    assert "v1" in text
    assert "Known limitations" in text or "known limitations" in text.lower()
    assert "Подпись заказчика" in text
    assert "CABIN-ACCEPTANCE.md" in text
    assert "TZ-CABIN.md" in text
    for item in (
        "боевого",
        "стакан",
        "чат",
        "мультиаккаунт",
        "001–156",
    ):
        assert item.lower() in text.lower() or item in text


def test_tz_md_links_cabin_final() -> None:
    text = TZ.read_text()
    assert "TZ-CABIN.md" in text
    assert "CABIN-ACCEPTANCE.md" in text
    assert "CABIN-FINAL.md" in text
    assert "01–30 done" in text or "01-30 done" in text
    assert "этап 26" not in text.split("## Следующая итерация")[1].split("---")[0]


def test_tz_cabin_stage30_done_and_closed() -> None:
    text = TZ_CABIN.read_text()
    assert "### Этап 30" in text
    chunk = text.split("### Этап 30")[1].split("# Часть J")[0]
    assert "**done**" in chunk
    assert "CABIN-FINAL.md" in chunk
    assert "кабинет v1" in chunk.lower() or "v1" in chunk
    tail = text.split("## Следующая итерация")[1]
    assert "0 / 30" in tail
    assert "01–30 done" in tail or "01-30 done" in tail
    # все этапы 01–29 тоже done
    for n in range(1, 30):
        assert f"### Этап {n:02d}" in text
        part = text.split(f"### Этап {n:02d}")[1].split("### Этап")[0]
        assert "**done**" in part, f"этап {n:02d} не done"


def test_acceptance_points_to_final() -> None:
    text = ACCEPT.read_text()
    assert "CABIN-FINAL.md" in text
    assert "v1" in text
