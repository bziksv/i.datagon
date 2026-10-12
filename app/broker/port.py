from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Sequence


@dataclass(frozen=True)
class BrokerAccount:
    broker_account_id: str
    name: str


@dataclass(frozen=True)
class CandleBar:
    ts: datetime
    o: Decimal
    h: Decimal
    low: Decimal
    c: Decimal
    v: Decimal


@dataclass(frozen=True)
class LastPrice:
    ticker: str
    price: Decimal


@dataclass(frozen=True)
class OrderRequest:
    ticker: str
    side: str
    qty: int
    type: str
    client_order_id: str
    price: Decimal | None = None


@dataclass(frozen=True)
class OrderAck:
    broker_order_id: str
    client_order_id: str
    status: str


@dataclass(frozen=True)
class PositionView:
    ticker: str
    qty: int
    avg_price: Decimal


@dataclass(frozen=True)
class Portfolio:
    cash: Decimal
    currency: str
    positions: tuple[PositionView, ...]


class BrokerPort(ABC):
    @abstractmethod
    def account(self) -> BrokerAccount:
        raise NotImplementedError

    @abstractmethod
    def candles(self, *, figi: str, tf: str, limit: int = 100) -> list[CandleBar]:
        raise NotImplementedError

    @abstractmethod
    def prices(self, tickers: Sequence[str]) -> list[LastPrice]:
        raise NotImplementedError

    @abstractmethod
    def post_order(self, order: OrderRequest) -> OrderAck:
        raise NotImplementedError

    @abstractmethod
    def cancel(self, broker_order_id: str) -> OrderAck:
        raise NotImplementedError

    @abstractmethod
    def portfolio(self) -> Portfolio:
        raise NotImplementedError
