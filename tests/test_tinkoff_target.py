import inspect

from app.broker.tinkoff import grpc_target, make_client
from tinkoff.invest.constants import INVEST_GRPC_API, INVEST_GRPC_API_SANDBOX


def test_default_target_is_sandbox() -> None:
    assert grpc_target() == INVEST_GRPC_API_SANDBOX
    assert grpc_target(live=False) == INVEST_GRPC_API_SANDBOX


def test_live_target_only_when_flag_set() -> None:
    assert grpc_target(live=True) == INVEST_GRPC_API


def test_make_client_always_passes_target() -> None:
    source = inspect.getsource(make_client)
    assert "target=grpc_target(live=live)" in source
    assert "Client(token)" not in source
    assert "sandbox_token()" in source
