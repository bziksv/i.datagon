"""Простой лимит запросов кабинета на IP."""

from collections import defaultdict

# Кабинет при входе дергает пачку API; плюс один IP часто делят браузер и
# служебные проверки. 120/мин слишком тесно и ложно блокирует вход.
DEFAULT_CABIN_RATE_PER_MIN = 600
WINDOW_SEC = 60


class IpRateLimit:
    def __init__(
        self,
        limit: int = DEFAULT_CABIN_RATE_PER_MIN,
        window_sec: int = WINDOW_SEC,
    ) -> None:
        self.limit = limit
        self.window_sec = window_sec
        self.hits: dict[str, list[float]] = defaultdict(list)

    def allow(self, ip: str, now: float) -> bool:
        if self.limit <= 0:
            return True
        recent = [ts for ts in self.hits[ip] if now - ts < self.window_sec]
        if len(recent) >= self.limit:
            self.hits[ip] = recent
            return False
        recent.append(now)
        self.hits[ip] = recent
        return True

    def reset(self, ip: str | None = None) -> None:
        if ip is None:
            self.hits.clear()
            return
        self.hits.pop(ip, None)


TRUSTED_HOPS = frozenset({"127.0.0.1", "::1", "localhost"})


def client_ip(headers: dict[str, str], remote: str | None) -> str:
    """Реальный клиент за nginx: X-Real-IP / X-Forwarded-For с доверенного hop."""
    if remote in TRUSTED_HOPS:
        real = (
            headers.get("x-real-ip")
            or headers.get("X-Real-IP")
            or headers.get("x-forwarded-for")
            or headers.get("X-Forwarded-For")
        )
        if real:
            return real.split(",")[0].strip()
    return remote or "unknown"
