"""Small in-memory rate limiter for sensitive routes.

This protects a single server process. A multi-server deployment should
replace it with a shared store such as Redis. The limit is per client IP.
"""

import time
from collections import defaultdict
from threading import Lock

from fastapi import HTTPException, Request, status


class RateLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()

    def enforce(self, request: Request, bucket: str, limit: int, window_seconds: int) -> None:
        host = request.client.host if request.client else "unknown"
        key = f"{bucket}:{host}"
        now = time.monotonic()
        with self._lock:
            recent = [stamp for stamp in self._hits[key] if now - stamp < window_seconds]
            if len(recent) >= limit:
                self._hits[key] = recent
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests. Please wait a minute and try again.",
                )
            recent.append(now)
            self._hits[key] = recent


limiter = RateLimiter()


def rate_limit(bucket: str, limit: int, window_seconds: int = 60):
    def dependency(request: Request) -> None:
        limiter.enforce(request, bucket, limit, window_seconds)

    return dependency
