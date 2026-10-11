from importlib.metadata import version

from app import __version__


def test_version() -> None:
    assert version("i-datagon") == __version__
