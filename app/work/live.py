"""Боевой контур: только статус. Включить отсюда нельзя — это решение человека и `.env`."""

from __future__ import annotations

import os

# Пункты deploy/NOT-LIVE.md. Пока хоть один не зелёный — боевой не включаем.
NOT_LIVE_CHECKLIST: tuple[tuple[str, str], ...] = (
    ("money", "Нет клиентских денег на счёте контура"),
    ("token", "В .env нет боевого токена, только sandbox"),
    ("flag", "TINKOFF_LIVE=0, target не INVEST_GRPC_API"),
    ("agents", "AGENTS_ENABLED=0, агенты молчат"),
    ("kill", "Kill-switch проверен на боевом контуре"),
    ("backup", "Восстановление бэкапа Postgres проверено на проде"),
    ("drift", "Drift книга/брокер смотрится без sandbox-допущений"),
    ("incident", "Инцидент с утечкой боевого токена прогнан как учение"),
    ("legal", "У брокера открыт именно live, не песочница"),
    ("decision", "Есть решение человека включить live"),
)


def live_view() -> dict:
    flag = os.environ.get("TINKOFF_LIVE", "0").strip()
    checklist = [{"id": key, "title": title, "ok": False} for key, title in NOT_LIVE_CHECKLIST]
    return {
        "enabled": False,
        "flag": f"TINKOFF_LIVE={flag or '0'}",
        "ready": sum(1 for row in checklist if row["ok"]),
        "total": len(checklist),
        "checklist": checklist,
    }
