import asyncio
import os
import sys
from pathlib import Path
import types
import pytest_asyncio

# Ensure the medflowai package inside packages/libs is importable when running tests without poetry
project_root = Path(__file__).resolve().parents[1]
medflowai_lib_path = project_root / "packages" / "libs" / "medflowai"
if medflowai_lib_path.exists():
    sys.path.insert(0, str(medflowai_lib_path))

import pytest

# ---- Stub external optional dependencies when not installed ---- #
from types import ModuleType

def _ensure_stub(name: str) -> ModuleType:  # Helper to create/get stub module hierarchically
    if name in sys.modules:
        return sys.modules[name]
    stub_mod = ModuleType(name)
    sys.modules[name] = stub_mod
    return stub_mod

# Top-level stubs
for _mod in (
    "structlog",
    "supabase",
    "supabase.client",
    "langchain_core",
    "langchain_core.documents",
    "langchain_openai",
    "langchain_community",
    "langchain_community.vectorstores",
):
    _ensure_stub(_mod)

# ---- Populate specific attributes used in code/tests ---- #
# supabase.client.Client / create_client
supabase_stub = sys.modules["supabase"]
client_stub_mod = sys.modules["supabase.client"]
if not hasattr(client_stub_mod, "Client"):
    class _StubSupabaseClient:  # pylint: disable=too-few-public-methods
        pass
    setattr(client_stub_mod, "Client", _StubSupabaseClient)

def _noop_create_client(*args, **kwargs):  # type: ignore[unused-argument]
    return _StubSupabaseClient()
setattr(client_stub_mod, "create_client", _noop_create_client)
# Also expose at supabase level for "from supabase import Client" imports.
setattr(supabase_stub, "Client", _StubSupabaseClient)
setattr(supabase_stub, "create_client", _noop_create_client)

# langchain_core.documents.Document
lc_doc_mod = sys.modules["langchain_core.documents"]
if not hasattr(lc_doc_mod, "Document"):
    from typing import Optional
    class Document(dict):  # simple placeholder behaves like dict/content holder
        def __init__(self, page_content: str = "", metadata: Optional[dict] = None, **kwargs):
            super().__init__(page_content=page_content, metadata=metadata or {}, **kwargs)
            self.page_content = page_content
            self.metadata = metadata or {}
    setattr(lc_doc_mod, "Document", Document)

# langchain_openai.OpenAIEmbeddings stub
lco_mod = sys.modules["langchain_openai"]
if not hasattr(lco_mod, "OpenAIEmbeddings"):
    class OpenAIEmbeddings:  # pylint: disable=too-few-public-methods
        def __init__(self, *args, **kwargs):
            pass
    setattr(lco_mod, "OpenAIEmbeddings", OpenAIEmbeddings)

# langchain_community.vectorstores.SupabaseVectorStore stub
lcc_mod = sys.modules["langchain_community.vectorstores"]
if not hasattr(lcc_mod, "SupabaseVectorStore"):
    class SupabaseVectorStore:  # pylint: disable=too-few-public-methods
        def __init__(self, *args, **kwargs):
            pass
        async def asimilarity_search_with_relevance_scores(self, **kwargs):  # noqa: D401
            return []
    setattr(lcc_mod, "SupabaseVectorStore", SupabaseVectorStore)

from medflowai.db import SupabaseClient

# -------------------- AsyncIO Event Loop Fixture -------------------- #
# pytest-asyncio requires an event_loop fixture. For module-scoped async fixtures we need
# to ensure the event_loop fixture has the same or broader scope (module or session).

@pytest_asyncio.fixture(scope="module")
def event_loop():  # type: ignore[missing-return-type-doc]
    """Create an instance of the default event loop for each test module."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="module")
async def supabase_client():
    """Async fixture that yields a SupabaseClient and closes connection at teardown."""

    # Skip if env vars not set (CI), to avoid failing.
    if not os.getenv("SUPABASE_URL"):
        pytest.skip("SUPABASE_URL not configured; skipping Supabase integration tests")

    client = SupabaseClient()
    yield client
    await client.close()
