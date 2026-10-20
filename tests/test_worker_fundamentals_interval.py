import inspect

from worker import __main__ as worker_main


def test_fundamentals_default_interval_is_one_hour() -> None:
    source = inspect.getsource(worker_main.run_worker)
    assert 'FUNDAMENTALS_INTERVAL_SEC", "3600"' in source
    assert "3600" in source
