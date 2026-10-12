from app.broker.tinkoff import Client
from tinkoff.invest import Client as SdkClient


def test_tinkoff_client_import() -> None:
    assert Client is SdkClient
