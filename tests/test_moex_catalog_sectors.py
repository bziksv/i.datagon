from app.advisory.moex_catalog import lookup_sector, normalize_sector, sector_title


def test_healthcare_maps_to_health_not_other() -> None:
    assert normalize_sector("health_care") == "health"
    assert normalize_sector("healthcare") == "health"
    assert sector_title("health") == "Здравоохранение"


def test_lookup_prefers_broker_health_and_catalog_over_other() -> None:
    assert lookup_sector("MDMG", {"sector": "health_care", "name": "Мать и дитя"}) == "health"
    assert lookup_sector("MDMG", {"sector": "other", "sector_id": "other"}) == "health"
    assert lookup_sector("UNKNOWN", {"sector": "other"}) == "other"
