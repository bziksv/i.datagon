"""Каталог MOEX TQBR: тикер → название и отрасль (для кабинета и демо)."""

from __future__ import annotations

from collections.abc import Mapping

# Отрасли в UI (стабильные id).
SECTOR_TITLES: dict[str, str] = {
    "oil_gas": "Нефть и газ",
    "banks": "Банки и финансы",
    "metals": "Металлы и добыча",
    "retail": "Ритейл и потребление",
    "tech": "Телеком и IT",
    "power": "Энергетика",
    "transport": "Транспорт",
    "chem": "Химия и удобрения",
    "real_estate": "Недвижимость",
    "industrials": "Промышленность",
    "health": "Здравоохранение",
    "other": "Прочее",
}

# Маппинг sector-строк Тинькофф → наш id.
TINKOFF_SECTOR_MAP: dict[str, str] = {
    "energy": "oil_gas",
    "oil": "oil_gas",
    "gas": "oil_gas",
    "financial": "banks",
    "finance": "banks",
    "banks": "banks",
    "materials": "metals",
    "metallurgy": "metals",
    "mining": "metals",
    "consumer": "retail",
    "retail": "retail",
    "telecom": "tech",
    "it": "tech",
    "technology": "tech",
    "utilities": "power",
    "electric_utilities": "power",
    "industrials": "industrials",
    "industrial": "industrials",
    "transport": "transport",
    "real_estate": "real_estate",
    "health_care": "health",
    "healthcare": "health",
    "health": "health",
    "pharma": "health",
    "telecoms": "tech",
}

# (ticker, name_ru, sector_id) — широкий ликвидный РФ-набор + desk.
_MOEX_ROWS: tuple[tuple[str, str, str], ...] = (
    # нефть и газ
    ("GAZP", "Газпром", "oil_gas"),
    ("LKOH", "ЛУКОЙЛ", "oil_gas"),
    ("ROSN", "Роснефть", "oil_gas"),
    ("NVTK", "Новатэк", "oil_gas"),
    ("SNGS", "Сургутнефтегаз", "oil_gas"),
    ("SNGSP", "Сургутнефтегаз привилегированные", "oil_gas"),
    ("TATN", "Татнефть", "oil_gas"),
    ("TATNP", "Татнефть привилегированные", "oil_gas"),
    ("SIBN", "Газпром нефть", "oil_gas"),
    ("TRNFP", "Транснефть привилегированные", "oil_gas"),
    ("BANE", "Башнефть", "oil_gas"),
    ("BANEP", "Башнефть привилегированные", "oil_gas"),
    ("RNFT", "РуссНефть", "oil_gas"),
    # банки
    ("SBER", "Сбербанк", "banks"),
    ("SBERP", "Сбербанк привилегированные", "banks"),
    ("VTBR", "ВТБ", "banks"),
    ("T", "Т-Технологии (Т-Банк)", "banks"),
    ("CBOM", "МКБ", "banks"),
    ("BSPB", "Банк Санкт-Петербург", "banks"),
    ("SFIN", "ЭсЭфАй", "banks"),
    ("MOEX", "Московская биржа", "banks"),
    ("IQJT", "СПБ Биржа", "banks"),
    ("RENI", "Ренессанс Страхование", "banks"),
    # металлы
    ("GMKN", "Норникель", "metals"),
    ("NLMK", "НЛМК", "metals"),
    ("MAGN", "ММК", "metals"),
    ("CHMF", "Северсталь", "metals"),
    ("ALRS", "АЛРОСА", "metals"),
    ("PLZL", "Полюс", "metals"),
    ("RUAL", "РУСАЛ", "metals"),
    ("MTLR", "Мечел", "metals"),
    ("MTLRP", "Мечел привилегированные", "metals"),
    ("SELG", "Селигдар", "metals"),
    ("POLY", "Polymetal", "metals"),
    ("VSMO", "ВСМПО-АВИСМА", "metals"),
    ("TRMK", "ТМК", "metals"),
    ("UGLD", "Южуралзолото", "metals"),
    # ритейл / потребление
    ("MGNT", "Магнит", "retail"),
    ("LENT", "Лента", "retail"),
    ("FIVE", "X5 Group", "retail"),
    ("FIXP", "Fix Price", "retail"),
    ("MVID", "М.Видео", "retail"),
    ("OZON", "Ozon", "retail"),
    ("MDMG", "Мать и дитя", "health"),
    ("BELU", "НоваБев", "retail"),
    ("WUSH", "Whoosh", "retail"),
    ("HHRU", "HeadHunter", "retail"),
    # телеком / IT
    ("MTSS", "МТС", "tech"),
    ("RTKM", "Ростелеком", "tech"),
    ("RTKMP", "Ростелеком привилегированные", "tech"),
    ("YDEX", "Яндекс", "tech"),
    ("VKCO", "VK", "tech"),
    ("POSI", "Positive Technologies", "tech"),
    ("ASTR", "Группа Астра", "tech"),
    ("CIAN", "Циан", "tech"),
    ("IVAT", "IVA Technologies", "tech"),
    ("SOFL", "Софтлайн", "tech"),
    # энергетика
    ("IRAO", "Интер РАО", "power"),
    ("FEES", "ФСК — Россети", "power"),
    ("HYDR", "РусГидро", "power"),
    ("MSNG", "Мосэнерго", "power"),
    ("OGKB", "ОГК-2", "power"),
    ("UPRO", "Юнипро", "power"),
    ("ELFV", "ЭЛ5-Энерго", "power"),
    ("LSNG", "Ленэнерго", "power"),
    ("LSNGP", "Ленэнерго привилегированные", "power"),
    # транспорт
    ("AFLT", "Аэрофлот", "transport"),
    ("FLOT", "Совкомфлот", "transport"),
    ("NMTP", "НМТП", "transport"),
    ("FESH", "ДВМП", "transport"),
    ("GLTR", "Globaltrans", "transport"),
    # химия
    ("PHOR", "ФосАгро", "chem"),
    ("AKRN", "Акрон", "chem"),
    ("KAZT", "Куйбышевазот", "chem"),
    ("KZOS", "Казаньоргсинтез", "chem"),
    ("NKNC", "Нижнекамскнефтехим", "chem"),
    ("NKNCP", "Нижнекамскнефтехим привилегированные", "chem"),
    # недвижимость / девелопмент
    ("PIKK", "ПИК", "real_estate"),
    ("SMLT", "Самолет", "real_estate"),
    ("ETLN", "Эталон", "real_estate"),
    ("LSRG", "ЛСР", "real_estate"),
    ("SFTL", "Софтлайн недвижимость", "real_estate"),
    # промышленность / прочее
    ("AFKS", "АФК Система", "industrials"),
    ("ENPG", "ЭН+ Груп", "industrials"),
    ("SGZH", "Сегежа", "industrials"),
    ("GCHE", "Черкизово", "industrials"),
    ("AQUA", "Инарктика", "industrials"),
    ("DELI", "Делимобиль", "industrials"),
    ("GEMC", "Юнайтед Медикал", "health"),
    ("CNRU", "ЦМТ", "industrials"),
)


def _index() -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for ticker, name, sector in _MOEX_ROWS:
        out[ticker] = {"name": name, "sector": sector}
    return out


MOEX_CATALOG: dict[str, dict[str, str]] = _index()


def all_catalog_tickers() -> list[str]:
    return list(MOEX_CATALOG.keys())


def normalize_sector(raw: str | None) -> str:
    if not raw:
        return "other"
    key = raw.strip().lower().replace(" ", "_").replace("-", "_")
    if key in SECTOR_TITLES:
        return key
    return TINKOFF_SECTOR_MAP.get(key, "other")


def sector_title(sector_id: str) -> str:
    return SECTOR_TITLES.get(sector_id, SECTOR_TITLES["other"])


def lookup_name(ticker: str, raw: Mapping[str, object] | None = None) -> str:
    payload = raw or {}
    for key in ("name", "company_name", "name_ru"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    row = MOEX_CATALOG.get(ticker.upper())
    if row:
        return row["name"]
    return ticker.upper()


def lookup_sector(ticker: str, raw: Mapping[str, object] | None = None) -> str:
    """Сектор брокера, если он осмысленный; иначе каталог. «other» не затирает каталог."""
    payload = raw or {}
    catalog = MOEX_CATALOG.get(ticker.upper())
    for key in ("sector_id", "sector"):
        value = payload.get(key)
        if not isinstance(value, str) or not value.strip():
            continue
        sid = normalize_sector(value)
        if sid != "other":
            return sid
    if catalog:
        return catalog["sector"]
    return "other"
