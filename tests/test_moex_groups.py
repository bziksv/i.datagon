from app.strategy.moex_groups import (
    MOEX_DESK_CORE,
    all_moex_desk_tickers,
    filter_sectors_by_available,
)


def test_core_is_default_sector() -> None:
    sectors = filter_sectors_by_available(list(MOEX_DESK_CORE) + ["NLMK", "AFLT"])
    by_id = {row["id"]: row for row in sectors}
    assert by_id["moex_core"]["default_on"] is True
    assert set(by_id["moex_core"]["tickers"]) == set(MOEX_DESK_CORE)
    assert "NLMK" in by_id["moex_metals"]["tickers"]
    assert "AFLT" in by_id["moex_transport"]["tickers"]


def test_all_moex_desk_tickers_unique() -> None:
    names = all_moex_desk_tickers()
    assert len(names) == len(set(names))
    assert set(MOEX_DESK_CORE).issubset(set(names))
