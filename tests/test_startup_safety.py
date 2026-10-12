import pytest
from app.ops.safety import LIVE_FORBIDDEN, assert_paper_mode


@pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes", "on"])
def test_paper_build_rejects_live_startup(value: str) -> None:
    with pytest.raises(RuntimeError, match=LIVE_FORBIDDEN):
        assert_paper_mode({"TINKOFF_LIVE": value})


@pytest.mark.parametrize("value", ["", "0", "false", "off"])
def test_paper_build_accepts_explicit_non_live(value: str) -> None:
    assert_paper_mode({"TINKOFF_LIVE": value})
