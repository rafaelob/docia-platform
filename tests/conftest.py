import asyncio
import os

import pytest

from medflowai.db import SupabaseClient


@pytest.fixture(scope="module")
async def supabase_client():
    """Async fixture that yields a SupabaseClient and closes connection at teardown."""

    # Skip if env vars not set (CI), to avoid failing.
    if not os.getenv("SUPABASE_URL"):
        pytest.skip("SUPABASE_URL not configured; skipping Supabase integration tests")

    client = SupabaseClient()
    yield client
    await client.close()
