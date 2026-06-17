from __future__ import annotations

import json
import logging
import time
from collections import Counter
from threading import Lock
from typing import Any

from app.db.repository import now_iso


logger = logging.getLogger("sellerharbor")


class RuntimeMetrics:
    def __init__(self) -> None:
        self.started_at = time.time()
        self._lock = Lock()
        self._request_count = 0
        self._error_count = 0
        self._rate_limited_count = 0
        self._total_duration_ms = 0.0
        self._status_counts: Counter[str] = Counter()
        self._method_counts: Counter[str] = Counter()

    def record_request(self, *, method: str, status_code: int, duration_ms: float) -> None:
        with self._lock:
            self._request_count += 1
            self._total_duration_ms += duration_ms
            self._status_counts[str(status_code)] += 1
            self._method_counts[method.upper()] += 1
            if status_code >= 500:
                self._error_count += 1

    def record_rate_limited(self) -> None:
        with self._lock:
            self._rate_limited_count += 1

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            avg_duration = self._total_duration_ms / self._request_count if self._request_count else 0
            return {
                "startedAt": now_iso_from_timestamp(self.started_at),
                "uptimeSeconds": max(0, int(time.time() - self.started_at)),
                "requestsTotal": self._request_count,
                "errorsTotal": self._error_count,
                "rateLimitedTotal": self._rate_limited_count,
                "averageDurationMs": round(avg_duration, 2),
                "statusCounts": dict(self._status_counts),
                "methodCounts": dict(self._method_counts),
            }


def log_access_event(
    *,
    request_id: str,
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    client: str,
    actor: str,
) -> None:
    payload = {
        "event": "http.request",
        "requestId": request_id,
        "method": method,
        "path": path,
        "statusCode": status_code,
        "durationMs": round(duration_ms, 2),
        "client": client,
        "actor": actor,
        "time": now_iso(),
    }
    logger.info(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))


def now_iso_from_timestamp(value: float) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(value))


runtime_metrics = RuntimeMetrics()
