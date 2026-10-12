"""Клиентский FakeBroker: стратегия гоняется без сети Тинькоффа."""

from decimal import Decimal
from typing import Sequence

from app.broker.port import (
    BrokerAccount,
    BrokerPort,
    CandleBar,
    LastPrice,
    OrderAck,
    OrderRequest,
    Portfolio,
    PositionView,
)


class FakeBroker(BrokerPort):
    def __init__(self) -> None:
        self._account = BrokerAccount(broker_account_id="sbx-1", name="fake")
        self._candles: dict[tuple[str, str], list[CandleBar]] = {}
        self._prices: dict[str, Decimal] = {}
        self._orders: dict[str, OrderAck] = {}
        self._cash = Decimal("1000000")
        self._positions: dict[str, PositionView] = {}
        self._seq = 0

    def seed_candle(self, figi: str, tf: str, bar: CandleBar) -> None:
        self._candles.setdefault((figi, tf), []).append(bar)

    def seed_price(self, ticker: str, price: Decimal) -> None:
        self._prices[ticker] = price

    def seed_position(self, position: PositionView) -> None:
        self._positions[position.ticker] = position

    def account(self) -> BrokerAccount:
        return self._account

    def candles(self, *, figi: str, tf: str, limit: int = 100) -> list[CandleBar]:
        return list(self._candles.get((figi, tf), [])[-limit:])

    def prices(self, tickers: Sequence[str]) -> list[LastPrice]:
        return [
            LastPrice(ticker=ticker, price=self._prices[ticker])
            for ticker in tickers
            if ticker in self._prices
        ]

    def post_order(self, order: OrderRequest) -> OrderAck:
        self._seq += 1
        ack = OrderAck(
            broker_order_id=f"ord-{self._seq}",
            client_order_id=order.client_order_id,
            status="new",
        )
        self._orders[ack.broker_order_id] = ack
        return ack

    def cancel(self, broker_order_id: str) -> OrderAck:
        prev = self._orders[broker_order_id]
        ack = OrderAck(
            broker_order_id=prev.broker_order_id,
            client_order_id=prev.client_order_id,
            status="cancelled",
        )
        self._orders[broker_order_id] = ack
        return ack

    def portfolio(self) -> Portfolio:
        return Portfolio(
            cash=self._cash,
            currency="RUB",
            positions=tuple(self._positions.values()),
        )
