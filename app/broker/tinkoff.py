"""Адаптер T-Invest. Токен только TINKOFF_SANDBOX_TOKEN."""

import os
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from tinkoff.invest import (
    CandleInterval,
    Client,
    GetAssetFundamentalsRequest,
    InstrumentIdType,
    MoneyValue,
    OrderDirection,
    OrderType,
)
from tinkoff.invest.constants import INVEST_GRPC_API, INVEST_GRPC_API_SANDBOX
from tinkoff.invest.utils import decimal_to_quotation, money_to_decimal, quotation_to_decimal

from app.broker.instruments import (
    MOEX_CLASS_CODE,
    instrument_from_share,
    pick_moex,
)
from app.broker.port import CandleBar, OrderAck, OrderRequest
from app.broker.prices import last_price_map
from app.broker.sandbox_payin import DEFAULT_DEPOSIT, ensure_deposit
from app.broker.sandbox_snapshot import snapshot
from app.broker.trading_status import trading_status_view

_TF_INTERVAL = {
    "1m": CandleInterval.CANDLE_INTERVAL_1_MIN,
    "1h": CandleInterval.CANDLE_INTERVAL_HOUR,
    "1d": CandleInterval.CANDLE_INTERVAL_DAY,
}

__all__ = [
    "BrokerTokenError",
    "Client",
    "INVEST_GRPC_API_SANDBOX",
    "grpc_target",
    "make_client",
    "open_sandbox_account_id",
    "sandbox_pay_in_rub",
    "fetch_candles",
    "fetch_trading_status",
    "find_moex_instrument",
    "fetch_moex_shares",
    "fetch_asset_fundamentals",
    "last_prices_by_ticker",
    "post_sandbox_order",
    "cancel_sandbox_order",
    "sandbox_snapshot",
    "sandbox_token",
]


class BrokerTokenError(RuntimeError):
    pass


def grpc_target(*, live: bool = False) -> str:
    """Боевой контур только при явном live=True. Иначе sandbox."""
    if live:
        return INVEST_GRPC_API
    return INVEST_GRPC_API_SANDBOX


def sandbox_token() -> str:
    token = os.environ.get("TINKOFF_SANDBOX_TOKEN", "").strip()
    if not token:
        raise BrokerTokenError("TINKOFF_SANDBOX_TOKEN is empty")
    return token


def _packaged_russian_certs() -> list[Path]:
    """PEM Минцифры рядом с репо (deploy/certs) — нужен gRPC к Тиньку."""
    root = Path(__file__).resolve().parents[2] / "deploy" / "certs"
    names = (
        "russian_trusted_root_ca.crt",
        "russian_trusted_sub_ca.crt",
    )
    return [root / name for name in names if (root / name).is_file()]


def _ensure_grpc_roots() -> None:
    """Тинькофф на Russian Trusted CA; системный store macOS/gRPC его часто не знает.

    Собираем certifi + PEM Минцифры в tempfile (без пробелов в пути — gRPC fdopen).
    """
    from tempfile import gettempdir

    # c-ares на macOS без DNS в Wi‑Fi часто не резолвит; native стабильнее.
    os.environ.setdefault("GRPC_DNS_RESOLVER", "native")

    packaged = _packaged_russian_certs()
    if not packaged:
        existing = os.environ.get("GRPC_DEFAULT_SSL_ROOTS_FILE_PATH", "").strip()
        if existing and os.path.isfile(existing):
            return
        for path in (
            "/etc/ssl/certs/ca-certificates.crt",
            "/etc/pki/tls/certs/ca-bundle.crt",
            "/etc/ssl/cert.pem",
        ):
            if os.path.isfile(path):
                os.environ["GRPC_DEFAULT_SSL_ROOTS_FILE_PATH"] = path
                return
        return

    out = Path(gettempdir()) / "idatagon-grpc-roots.pem"
    parts: list[str] = []
    try:
        import certifi

        parts.append(Path(certifi.where()).read_text(encoding="utf-8"))
    except Exception:
        for path in (
            "/etc/ssl/certs/ca-certificates.crt",
            "/etc/ssl/cert.pem",
            "/etc/pki/tls/certs/ca-bundle.crt",
        ):
            if os.path.isfile(path):
                parts.append(Path(path).read_text(encoding="utf-8"))
                break
    for pem in packaged:
        parts.append(pem.read_text(encoding="utf-8"))
    blob = "\n".join(parts)
    if not out.is_file() or out.read_text(encoding="utf-8") != blob:
        out.write_text(blob, encoding="utf-8")
    os.environ["GRPC_DEFAULT_SSL_ROOTS_FILE_PATH"] = str(out)


def make_client(*, live: bool = False) -> Client:
    _ensure_grpc_roots()
    return Client(sandbox_token(), target=grpc_target(live=live))


def open_sandbox_account_id() -> str:
    with make_client() as client:
        return client.sandbox.open_sandbox_account(name="i.datagon").account_id


def sandbox_cash(account_id: str) -> Decimal:
    with make_client() as client:
        portfolio = client.sandbox.get_sandbox_portfolio(account_id=account_id)
        return money_to_decimal(portfolio.total_amount_currencies)


def sandbox_pay_in_rub(account_id: str, amount: Decimal) -> None:
    units = int(amount)
    nano = int((amount - units) * Decimal("1000000000"))
    with make_client() as client:
        client.sandbox.sandbox_pay_in(
            account_id=account_id,
            amount=MoneyValue(currency="rub", units=units, nano=nano),
        )


def ensure_sandbox_pay_in(
    account_id: str,
    deposit: Decimal = DEFAULT_DEPOSIT,
) -> Decimal:
    return ensure_deposit(
        sandbox_cash(account_id),
        lambda amount: sandbox_pay_in_rub(account_id, amount),
        deposit,
    )


def sandbox_snapshot(account_id: str | None = None) -> dict:
    with make_client() as client:
        accounts = list(client.sandbox.get_sandbox_accounts().accounts)
        aid = account_id or (accounts[0].id if accounts else "")
        portfolio = client.sandbox.get_sandbox_portfolio(account_id=aid)
        return snapshot(accounts, portfolio)


def historic_to_bar(candle) -> CandleBar:
    return CandleBar(
        ts=candle.time,
        o=quotation_to_decimal(candle.open),
        h=quotation_to_decimal(candle.high),
        low=quotation_to_decimal(candle.low),
        c=quotation_to_decimal(candle.close),
        v=Decimal(candle.volume),
    )


def fetch_candles(
    *,
    figi: str = "",
    instrument_id: str = "",
    tf: str = "1h",
    from_: datetime,
    to: datetime,
    limit: int = 100,
) -> list[CandleBar]:
    interval = _TF_INTERVAL[tf]
    with make_client() as client:
        raw = client.market_data.get_candles(
            figi=figi,
            instrument_id=instrument_id,
            from_=from_,
            to=to,
            interval=interval,
            limit=limit,
        )
        return [historic_to_bar(item) for item in raw.candles]


def last_prices_by_ticker(
    ticker_by_figi: dict[str, str] | None = None,
    ticker_by_uid: dict[str, str] | None = None,
) -> dict[str, Decimal]:
    figis = list((ticker_by_figi or {}).keys())
    uids = list((ticker_by_uid or {}).keys())
    with make_client() as client:
        raw = client.market_data.get_last_prices(
            figi=figis or None,
            instrument_id=uids or None,
        )
        return last_price_map(
            raw.last_prices,
            ticker_by_figi=ticker_by_figi,
            ticker_by_uid=ticker_by_uid,
        )


class InstrumentNotFound(RuntimeError):
    pass


def find_moex_instrument(ticker: str):
    query = ticker.strip().upper()
    with make_client() as client:
        hits = list(client.instruments.find_instrument(query=query).instruments)
        if pick_moex(hits, query) is None:
            raise InstrumentNotFound(query)
        share = client.instruments.share_by(
            id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_TICKER,
            class_code=MOEX_CLASS_CODE,
            id=query,
        ).instrument
        return instrument_from_share(share)


def fetch_moex_shares() -> list:
    """Сырые TQBR share с брокера (с asset_uid/name/sector) — не ORM Instrument."""
    with make_client() as client:
        raw = client.instruments.shares()
        return [
            share
            for share in raw.instruments
            if (getattr(share, "class_code", "") or "") == MOEX_CLASS_CODE
            and (getattr(share, "ticker", "") or "").strip()
        ]


def fetch_asset_fundamentals(assets: list[str]) -> list:
    with make_client() as client:
        raw = client.instruments.get_asset_fundamentals(
            GetAssetFundamentalsRequest(assets=list(assets))
        )
        return list(raw.fundamentals)


def fetch_trading_status(*, figi: str = "", instrument_id: str = "") -> dict:
    with make_client() as client:
        raw = client.market_data.get_trading_status(
            figi=figi, instrument_id=instrument_id
        )
        return trading_status_view(raw.trading_status)


def post_sandbox_order(
    order: OrderRequest,
    *,
    account_id: str,
    figi: str = "",
    instrument_id: str = "",
) -> OrderAck:
    direction = (
        OrderDirection.ORDER_DIRECTION_BUY
        if order.side.lower() == "buy"
        else OrderDirection.ORDER_DIRECTION_SELL
    )
    order_type = (
        OrderType.ORDER_TYPE_MARKET
        if order.type.lower() == "market"
        else OrderType.ORDER_TYPE_LIMIT
    )
    price = decimal_to_quotation(order.price) if order.price is not None else None
    with make_client() as client:
        raw = client.sandbox.post_sandbox_order(
            figi=figi,
            instrument_id=instrument_id,
            quantity=order.qty,
            price=price,
            direction=direction,
            account_id=account_id,
            order_type=order_type,
            order_id=order.client_order_id,
        )
        status = getattr(raw.execution_report_status, "name", None) or str(
            raw.execution_report_status
        )
        return OrderAck(
            broker_order_id=raw.order_id,
            client_order_id=order.client_order_id,
            status=status,
        )


def cancel_sandbox_order(
    *,
    account_id: str,
    order_id: str,
    client_order_id: str = "",
) -> OrderAck:
    with make_client() as client:
        client.sandbox.cancel_sandbox_order(
            account_id=account_id,
            order_id=order_id,
        )
        return OrderAck(
            broker_order_id=order_id,
            client_order_id=client_order_id,
            status="cancelled",
        )
