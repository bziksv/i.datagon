from app.advisory.moex_catalog import SECTOR_TITLES
from app.strategy.moex_groups import (
    MOEX_DESK_CORE,
    all_moex_desk_tickers,
    default_desk_tickers,
    filter_sectors_by_available,
)


def test_sectors_match_catalog_titles() -> None:
    sectors = filter_sectors_by_available(list(MOEX_DESK_CORE) + ["NLMK", "AFLT", "MDMG"])
    by_id = {row["id"]: row for row in sectors}
    assert "banks" in by_id
    assert "SBER" in by_id["banks"]["tickers"]
    assert by_id["banks"]["title"] == SECTOR_TITLES["banks"]
    assert "NLMK" in by_id["metals"]["tickers"]
    assert by_id["metals"]["title"] == "Металлы и добыча"
    assert "AFLT" in by_id["transport"]["tickers"]
    assert "MDMG" in by_id["health"]["tickers"]
    assert by_id["health"]["title"] == "Здравоохранение и фарма"
    assert "moex_core" not in by_id


def test_default_desk_tickers_are_core() -> None:
    assert default_desk_tickers(list(MOEX_DESK_CORE) + ["NLMK"]) == list(MOEX_DESK_CORE)


def test_all_moex_desk_tickers_unique() -> None:
    names = all_moex_desk_tickers()
    assert len(names) == len(set(names))
    assert set(MOEX_DESK_CORE).issubset(set(names))
