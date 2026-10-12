import inspect
from types import SimpleNamespace

from app.broker.instruments import (
    MOEX_CLASS_CODE,
    instrument_from_share,
    instrument_ids,
    merge_instrument,
    pick_by_id,
    pick_moex,
    resolve_mapped_instrument,
)
from app.broker.tinkoff import find_moex_instrument
from app.models import Instrument


def test_pick_moex_tqbr() -> None:
    hits = [
        SimpleNamespace(ticker="SBER", class_code="SPBXM"),
        SimpleNamespace(ticker="SBER", class_code="TQBR"),
        SimpleNamespace(ticker="GAZP", class_code="TQBR"),
    ]
    got = pick_moex(hits, "sber")
    assert got is not None
    assert got.class_code == MOEX_CLASS_CODE


def test_instrument_from_share() -> None:
    share = SimpleNamespace(
        ticker="SBER",
        figi="BBG004730N88",
        uid="uid-sber",
        lot=10,
        currency="RUB",
        class_code="TQBR",
    )
    row = instrument_from_share(share)
    assert row.ticker == "SBER"
    assert row.figi == "BBG004730N88"
    assert row.uid == "uid-sber"
    assert row.lot == 10
    assert row.currency == "rub"
    assert row.class_code == "TQBR"


def test_merge_does_not_insert_second_row() -> None:
    existing = Instrument(
        ticker="SBER", figi="old", uid="old", lot=1, currency="rub", class_code="TQBR"
    )
    found = instrument_from_share(
        SimpleNamespace(
            ticker="SBER",
            figi="BBG004730N88",
            uid="uid-sber",
            lot=10,
            currency="rub",
            class_code="TQBR",
        )
    )
    merged = merge_instrument(existing, found)
    assert merged is existing
    assert merged.figi == "BBG004730N88"
    assert merged.lot == 10


def _sber() -> Instrument:
    return Instrument(
        ticker="SBER",
        figi="BBG004730N88",
        uid="uid-sber",
        lot=10,
        currency="rub",
        class_code="TQBR",
    )


def test_ids_are_bidirectional() -> None:
    row = _sber()
    assert instrument_ids(row) == {
        "ticker": "SBER",
        "figi": "BBG004730N88",
        "uid": "uid-sber",
    }
    rows = [row]
    assert pick_by_id(rows, ticker="sber") is row
    assert pick_by_id(rows, figi="BBG004730N88") is row
    assert pick_by_id(rows, uid="uid-sber") is row


def test_repeat_lookup_hits_existing_row() -> None:
    calls = {"n": 0}

    def fetch() -> Instrument:
        calls["n"] += 1
        return _sber()

    existing = _sber()
    got, fetched = resolve_mapped_instrument(existing, fetch)
    assert fetched is False
    assert got is existing
    assert instrument_ids(got)["figi"] == "BBG004730N88"
    assert calls["n"] == 0

    missing, created = resolve_mapped_instrument(None, fetch)
    assert created is True
    assert missing.uid == "uid-sber"
    assert calls["n"] == 1


def test_sdk_uses_find_and_share_by() -> None:
    source = inspect.getsource(find_moex_instrument)
    assert "find_instrument" in source
    assert "share_by" in source
    assert "TQBR" in source or "MOEX_CLASS_CODE" in source
