"""Asynchronous retry helper with exponential back-off.

Placed in `core` to avoid directory creation issues.
"""
from __future__ import annotations

import asyncio
import random
from typing import Any, Awaitable, Callable, Tuple, TypeVar, Optional

import structlog
import logging

_T = TypeVar("_T")

async def async_retry(
    func: Callable[..., Awaitable[_T]],
    *args: Any,
    retries: int = 3,
    base_delay: float = 0.5,
    backoff: float = 2.0,
    jitter: float = 0.1,
    exceptions: Tuple[type[Exception], ...] = (Exception,),
    logger: Optional[structlog.BoundLogger] = None,
    **kwargs: Any,
) -> _T:
    """Execute *func* with retry and exponential back-off.

    Args are equivalent to the util description earlier.
    """
    _logger = logger
    if _logger is None:
        try:
            _logger = structlog.get_logger(__name__)
        except AttributeError:
            _logger = logging.getLogger(__name__)
    attempt = 0
    delay = base_delay
    while True:
        try:
            return await func(*args, **kwargs)
        except exceptions as exc:  # noqa: BLE001
            if attempt >= retries:
                _logger.error("retry_exhausted", extra={"attempts": attempt+1, "err": str(exc)})
                raise
            _logger.warning("retry", extra={"attempt": attempt+1, "err": str(exc)})
            await asyncio.sleep(delay * (1 + random.uniform(0, jitter)))
            delay *= backoff
            attempt += 1
