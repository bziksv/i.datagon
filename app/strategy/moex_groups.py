"""Отраслевые группы MOEX для desk — та же сетка, что в moex_catalog / Компании."""

from __future__ import annotations

from collections.abc import Sequence

from app.advisory.moex_catalog import MOEX_CATALOG, SECTOR_TITLES, sector_title

# Исходные 14 — отмечены по умолчанию в прогоне (не отдельная отрасль).
MOEX_DESK_CORE: tuple[str, ...] = (
    "ALRS",
    "CHMF",
    "GAZP",
    "GMKN",
    "LKOH",
    "MGNT",
    "MOEX",
    "NVTK",
    "PLZL",
    "ROSN",
    "SBER",
    "SNGS",
    "TATN",
    "VTBR",
)

# Совместимость: старый импорт ожидал кортеж секторов.
MOEX_DESK_SECTORS: tuple[dict[str, object], ...] = tuple(
    {
        "id": sector_id,
        "title": title,
        "default_on": False,
        "tickers": tuple(
            ticker
            for ticker, row in MOEX_CATALOG.items()
            if row.get("sector") == sector_id
        ),
    }
    for sector_id, title in SECTOR_TITLES.items()
)


def all_moex_desk_tickers() -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for sector_id in SECTOR_TITLES:
        for ticker, row in MOEX_CATALOG.items():
            if row.get("sector") != sector_id:
                continue
            name = ticker.strip().upper()
            if not name or name in seen:
                continue
            seen.add(name)
            out.append(name)
    return out


def filter_sectors_by_available(
    available: Sequence[str],
) -> list[dict]:
    """Секторы в порядке SECTOR_TITLES; только тикеры, для которых есть файл."""
    have = {name.upper() for name in available}
    buckets: dict[str, list[str]] = {sector_id: [] for sector_id in SECTOR_TITLES}
    unknown: list[str] = []
    for name in sorted(have):
        row = MOEX_CATALOG.get(name)
        if row is None:
            unknown.append(name)
            continue
        sid = str(row.get("sector") or "other")
        if sid not in buckets:
            sid = "other"
        buckets[sid].append(name)
    if unknown:
        buckets.setdefault("other", []).extend(unknown)
        buckets["other"] = sorted(set(buckets["other"]))

    sectors: list[dict] = []
    for sector_id in SECTOR_TITLES:
        tickers = buckets.get(sector_id) or []
        if not tickers:
            continue
        sectors.append(
            {
                "id": sector_id,
                "title": sector_title(sector_id),
                "default_on": False,
                "tickers": tickers,
            }
        )
    return sectors


def default_desk_tickers(available: Sequence[str]) -> list[str]:
    have = {name.upper() for name in available}
    return [name for name in MOEX_DESK_CORE if name in have]
