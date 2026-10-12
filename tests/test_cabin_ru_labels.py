"""Запрещённые английские пользовательские лейблы в UI кабинета."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"

# Подписи, которые нельзя показывать оператору как labels/заголовки.
FORBIDDEN_LABELS = (
    "Kill",
    "Equity",
    "Ledger",
    "Portfolio",
    "Orders",
    "Vault",
    "Drift",
    "Sleeve",
    "Overview",
    "Agents",
    "Status",
    "Refresh",
    "Submit",
    "Cancel",
    "Login",
    "Approve",
    "Reject",
    "Payload",
)

# Термины, которые в UI должны быть по-русски (не как заголовок/кнопка EN).
TERM_ALIGNMENT = {
    "стоимость счёта": ("Equity",),
    "стоп": ("Kill",),
    "проводки": ("Ledger",),
    "рукав": ("Sleeve",),
    "сейф": ("Vault",),
    "расхождение": ("Drift",),
}


def _ui_visible_chunks(text: str) -> list[str]:
    """Достаём пользовательские строки: HTML-текст и строковые литералы JS."""
    chunks: list[str] = []
    chunks.extend(re.findall(r">([^<>{}]+)<", text))
    chunks.extend(re.findall(r"""(['"])(.*?)\1""", text, flags=re.DOTALL))
    # из findall с группами берём только содержимое кавычек
    flat: list[str] = []
    for item in chunks:
        if isinstance(item, tuple):
            flat.append(item[1] if len(item) > 1 else item[0])
        else:
            flat.append(item)
    return [c.strip() for c in flat if c and c.strip()]


def _looks_like_user_label(chunk: str) -> bool:
    if len(chunk) > 80:
        return False
    # технические пути/ключи пропускаем
    if chunk.startswith("/") or chunk.startswith("#"):
        return False
    if "X-App-Token" in chunk or "cabin_tour_v1" in chunk:
        return False
    if re.fullmatch(r"[a-z0-9_./?-]+", chunk):
        return False
    return True


def test_forbidden_en_labels_absent_from_ui() -> None:
    texts = [
        (WEB / "index.html").read_text(),
        (WEB / "cabin.js").read_text(),
        (WEB / "tour.js").read_text(),
    ]
    offenders: list[str] = []
    for blob in texts:
        for chunk in _ui_visible_chunks(blob):
            if not _looks_like_user_label(chunk):
                continue
            for word in FORBIDDEN_LABELS:
                # целое слово как лейбл / в short title-case фразе
                if re.search(rf"(?<![A-Za-z]){re.escape(word)}(?![A-Za-z])", chunk):
                    # разрешаем упоминание в чеклисте запретов / тестах внутри комментариев нет
                    if "запрещ" in chunk.lower():
                        continue
                    offenders.append(f"{word} ← {chunk[:120]}")
    assert not offenders, "запрещённые EN-лейблы в UI:\n" + "\n".join(offenders[:30])


def test_term_alignment_russian_present() -> None:
    js = (WEB / "cabin.js").read_text()
    html = (WEB / "index.html").read_text()
    blob = js + "\n" + html
    for ru, _banned in TERM_ALIGNMENT.items():
        assert ru in blob, f"ожидался русский термин «{ru}»"


def test_no_kill_equity_ledger_as_button_or_heading() -> None:
    html = (WEB / "index.html").read_text()
    js = (WEB / "cabin.js").read_text()
    # кнопки/заголовки не должны быть голым EN
    for pattern in (
        r">\s*Kill\s*<",
        r">\s*Equity\s*<",
        r">\s*Ledger\s*<",
        r"""['"]Kill['"]""",
        r"""['"]Equity['"]""",
        r"""['"]Ledger['"]""",
        r"textContent\s*=\s*['\"]Kill['\"]",
        r"textContent\s*=\s*['\"]Equity['\"]",
        r"textContent\s*=\s*['\"]Ledger['\"]",
    ):
        assert not re.search(pattern, html + js), pattern
