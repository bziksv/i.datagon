"""Отраслевые группы MOEX для desk: ядро + доп. ликвидные имена."""

from __future__ import annotations

from collections.abc import Sequence

# Исходные 14 — отмечены по умолчанию в кабинете.
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

# Доп. бумаги по отраслям (без дублей с ядром в UI-группах ниже).
MOEX_DESK_SECTORS: tuple[dict[str, object], ...] = (
    {
        "id": "moex_core",
        "title": "MOEX · ядро",
        "default_on": True,
        "tickers": MOEX_DESK_CORE,
    },
    {
        "id": "moex_oil",
        "title": "MOEX · нефть и газ",
        "default_on": False,
        "tickers": ("SIBN", "TRNFP", "SNGSP", "TATNP", "BANE"),
    },
    {
        "id": "moex_banks",
        "title": "MOEX · банки и финансы",
        "default_on": False,
        "tickers": ("T", "CBOM", "BSPB", "SFIN"),
    },
    {
        "id": "moex_metals",
        "title": "MOEX · металлы и добыча",
        "default_on": False,
        "tickers": ("NLMK", "MAGN", "RUAL", "SELG", "MTLR"),
    },
    {
        "id": "moex_retail",
        "title": "MOEX · ритейл и потребление",
        "default_on": False,
        "tickers": ("LENT", "FIXP", "MVID", "OZON"),
    },
    {
        "id": "moex_tech",
        "title": "MOEX · телеком и IT",
        "default_on": False,
        "tickers": ("MTSS", "RTKM", "YDEX", "POSI", "VKCO", "ASTR"),
    },
    {
        "id": "moex_power",
        "title": "MOEX · энергетика",
        "default_on": False,
        "tickers": ("FEES", "HYDR", "IRAO", "MSNG", "OGKB"),
    },
    {
        "id": "moex_transport",
        "title": "MOEX · транспорт",
        "default_on": False,
        "tickers": ("AFLT", "FLOT", "NMTP"),
    },
    {
        "id": "moex_chem",
        "title": "MOEX · химия и удобрения",
        "default_on": False,
        "tickers": ("PHOR", "AKRN"),
    },
)


def all_moex_desk_tickers() -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for sector in MOEX_DESK_SECTORS:
        for raw in sector["tickers"]:  # type: ignore[index]
            name = str(raw).strip().upper()
            if not name or name in seen:
                continue
            seen.add(name)
            out.append(name)
    return out


def filter_sectors_by_available(
    available: Sequence[str],
) -> list[dict]:
    have = {name.upper() for name in available}
    sectors: list[dict] = []
    for sector in MOEX_DESK_SECTORS:
        tickers = [
            str(name).upper()
            for name in sector["tickers"]  # type: ignore[index]
            if str(name).upper() in have
        ]
        if not tickers:
            continue
        sectors.append(
            {
                "id": sector["id"],
                "title": sector["title"],
                "default_on": bool(sector["default_on"]),
                "tickers": tickers,
            }
        )
    return sectors
