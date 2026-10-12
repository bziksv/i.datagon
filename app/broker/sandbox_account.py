"""Идемпотентное открытие sandbox-счёта.

Если в `accounts` уже есть строка kind=sandbox с broker_account_id,
повторный запуск её возвращает и не зовёт OpenSandboxAccount.
Иначе один вызов opener() (SDK OpenSandboxAccount) и новая строка.
"""

from collections.abc import Callable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Account

SANDBOX_KIND = "sandbox"


def resolve_sandbox_account(
    existing: Account | None,
    open_account: Callable[[], str],
) -> tuple[Account, bool]:
    if existing is not None and existing.broker_account_id:
        return existing, False
    return Account(kind=SANDBOX_KIND, broker_account_id=open_account()), True


async def load_sandbox_account(session: AsyncSession) -> Account | None:
    return await session.scalar(
        select(Account).where(
            Account.kind == SANDBOX_KIND,
            Account.broker_account_id.is_not(None),
        )
    )


async def ensure_sandbox_account(
    session: AsyncSession,
    open_account: Callable[[], str],
) -> Account:
    account, created = resolve_sandbox_account(
        await load_sandbox_account(session),
        open_account,
    )
    if created:
        session.add(account)
        await session.flush()
    return account
