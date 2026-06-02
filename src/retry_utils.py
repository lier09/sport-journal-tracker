from __future__ import annotations

import random
import time
from collections.abc import Callable
from typing import TypeVar

import requests

T = TypeVar("T")

RETRYABLE_EXCEPTIONS = (
    requests.exceptions.Timeout,
    requests.exceptions.ConnectionError,
    requests.exceptions.SSLError,
    requests.exceptions.ChunkedEncodingError,
)


def with_retries(
    func: Callable[[], T],
    *,
    attempts: int = 3,
    base_delay: float = 2.0,
    max_delay: float = 20.0,
) -> T:
    """Run a network call with small exponential backoff.

    This handles common Crossref/PubMed transient failures without hiding permanent errors.
    """
    last_exc: Exception | None = None
    for i in range(attempts):
        try:
            return func()
        except RETRYABLE_EXCEPTIONS as exc:
            last_exc = exc
            if i >= attempts - 1:
                break
            delay = min(max_delay, base_delay * (2 ** i)) + random.uniform(0, 0.8)
            time.sleep(delay)
    assert last_exc is not None
    raise last_exc
