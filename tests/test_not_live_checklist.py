import os
from pathlib import Path

from app.broker.tinkoff import grpc_target
from tinkoff.invest.constants import INVEST_GRPC_API, INVEST_GRPC_API_SANDBOX

DOC = Path(__file__).resolve().parents[1] / "deploy" / "NOT-LIVE.md"


def test_ten_red_items_and_sandbox_target() -> None:
    text = DOC.read_text()
    reds = [line for line in text.splitlines() if line.startswith("|") and "RED" in line]
    assert len(reds) == 10
    assert "GREEN" not in text
    assert "TINKOFF_LIVE=0" in text
    assert "TINKOFF_LIVE=1" in text
    assert os.environ.get("TINKOFF_LIVE", "0") in {"0", "false", "False", ""}
    assert grpc_target() == INVEST_GRPC_API_SANDBOX
    assert grpc_target() != INVEST_GRPC_API
