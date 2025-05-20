"""Tests for async_retry utility."""
import asyncio
import pytest

from medflowai.core.retry_utils import async_retry


class TransientError(RuntimeError):
    """Custom exception for testing."""


@pytest.mark.asyncio
async def test_async_retry_succeeds_after_failures():
    attempts = {
        "count": 0,
    }

    async def flaky() -> str:  # noqa: D401
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise TransientError("boom")
        return "ok"

    result = await async_retry(flaky, retries=3, exceptions=(TransientError,))
    assert result == "ok"
    assert attempts["count"] == 3


@pytest.mark.asyncio
async def test_async_retry_exhausts_and_raises():
    async def always_fail() -> None:  # noqa: D401
        raise TransientError("bad")

    with pytest.raises(TransientError):
        await async_retry(always_fail, retries=1, exceptions=(TransientError,))
