"""Kill-switch: флаг в БД, все новые ордера deny."""

from collections.abc import Sequence

from app.book.orders import reject_order
from app.models import Flag, Order

KILL_KEY = "kill"
KILLED = "killed"


def is_killed(flags: Sequence[Flag]) -> bool:
    for row in flags:
        if row.key == KILL_KEY:
            return bool(row.value)
    return False


def apply_kill(flags: list[Flag], killed: bool) -> Flag:
    for row in flags:
        if row.key == KILL_KEY:
            row.value = killed
            return row
    row = Flag(key=KILL_KEY, value=killed)
    flags.append(row)
    return row


def kill_view(flags: Sequence[Flag]) -> dict:
    return {"killed": is_killed(flags)}


def gate_kill(order: Order, flags: Sequence[Flag]) -> Order:
    if not is_killed(flags):
        return order
    return reject_order(order, KILLED)
