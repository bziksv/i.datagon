"""In-memory broker failures used by admission drills."""

from app.broker.fake import FakeBroker


class TimeoutDrillBroker(FakeBroker):
    def post_order(self, order):  # type: ignore[override]
        raise TimeoutError("emergency drill timeout")
