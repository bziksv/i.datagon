"""Внутренние счета книги. Не брокерский sandbox."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Account

TRADING_CASH = "trading_cash"
VAULT = "vault"


def account_kind(account: Account) -> str:
    return account.kind


def resolve_trading_cash(existing: Account | None) -> tuple[Account, bool]:
    if existing is not None and existing.kind == TRADING_CASH:
        return existing, False
    return Account(kind=TRADING_CASH), True


async def load_trading_cash(session: AsyncSession) -> Account | None:
    return await session.scalar(select(Account).where(Account.kind == TRADING_CASH))


async def ensure_trading_cash(session: AsyncSession) -> Account:
    account, created = resolve_trading_cash(await load_trading_cash(session))
    if created:
        session.add(account)
        await session.flush()
    return account
