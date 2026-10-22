from __future__ import annotations

import pytest

from app.work import service


class Limited(Exception):
    def __init__(self):
        meta = type("Meta", (), {"ratelimit_reset": 1})()
        super().__init__("StatusCode.RESOURCE_EXHAUSTED", "", meta)


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    slept: list[float] = []
    monkeypatch.setattr(service, "sleep", slept.append)
    return slept


def test_retries_rate_limit_with_same_order(no_sleep):
    calls = []

    def post(order, **kwargs):
        calls.append(order)
        if len(calls) < 3:
            raise Limited()
        return "ack"

    assert service._post_paced(post, "order-1", account_id="a") == "ack"
    assert calls == ["order-1"] * 3
    assert 1.0 in no_sleep


def test_other_errors_are_not_retried():
    calls = []

    def post(order, **kwargs):
        calls.append(order)
        raise ValueError("bad figi")

    with pytest.raises(ValueError):
        service._post_paced(post, "order-1")
    assert len(calls) == 1


def test_gives_up_after_retries():
    def post(order, **kwargs):
        raise Limited()

    with pytest.raises(Limited):
        service._post_paced(post, "order-1")
