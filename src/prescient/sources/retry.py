"""Shared tenacity retry policy for source HTTP clients."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)


def network_retry(
    *, include_status_errors: bool = False, attempts: int = 4
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Return a retry decorator with exponential backoff for transient failures.

    Retries transport errors always, and 4xx/5xx responses when
    ``include_status_errors`` is set (feeds that occasionally 5xx).
    """
    exc: tuple[type[Exception], ...] = (httpx.TransportError,)
    if include_status_errors:
        exc = (*exc, httpx.HTTPStatusError)
    return retry(
        stop=stop_after_attempt(attempts),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        retry=retry_if_exception_type(exc),
        reraise=True,
    )
