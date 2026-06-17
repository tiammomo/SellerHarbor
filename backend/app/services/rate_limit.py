from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import dataclass
from threading import Lock


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    limit: int
    remaining: int
    retry_after_seconds: int
    scope: str


class FixedWindowRateLimiter:
    def __init__(self, window_seconds: int = 60) -> None:
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, *, key: str, limit: int, scope: str) -> RateLimitResult:
        if limit <= 0:
            return RateLimitResult(True, limit, 0, 0, scope)

        now = time.monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            hits = self._hits[key]
            while hits and hits[0] <= cutoff:
                hits.popleft()

            if len(hits) >= limit:
                retry_after = max(1, int(self.window_seconds - (now - hits[0])))
                return RateLimitResult(False, limit, 0, retry_after, scope)

            hits.append(now)
            return RateLimitResult(True, limit, max(0, limit - len(hits)), 0, scope)


rate_limiter = FixedWindowRateLimiter()
