import pytest
import asyncio

import importlib.util
import sys
import types
from pathlib import Path

# Load service package dynamically (directory contains hyphen, not valid module name)
base_dir = (
    Path(__file__).resolve().parents[2]
    / "packages"
    / "services"
    / "arbiter-o3"
)

# Create fake package 'arbiter_o3'
package_name = "arbiter_o3"
package = types.ModuleType(package_name)
package.__path__ = [str(base_dir)]
sys.modules[package_name] = package

# --- Provide dummy adapters to satisfy imports ---
adapters_pkg = types.ModuleType("medflowai.adapters")
sys.modules["medflowai.adapters"] = adapters_pkg

# Dummy GeminiAdapter
gem_dummy = types.ModuleType("medflowai.adapters.gemini_adapter")

class DummyGeminiAdapter:  # noqa: D101
    async def chat_completion(self, *_, **__):
        return types.SimpleNamespace(error="not-implemented", content="")

gem_dummy.GeminiAdapter = DummyGeminiAdapter
sys.modules["medflowai.adapters.gemini_adapter"] = gem_dummy

# Dummy OpenAIAdapter
open_dummy = types.ModuleType("medflowai.adapters.openai_adapter")

class DummyOpenAIAdapter:  # noqa: D101
    async def chat_completion(self, *_, **__):
        return types.SimpleNamespace(error="not-implemented", content="")

open_dummy.OpenAIAdapter = DummyOpenAIAdapter
sys.modules["medflowai.adapters.openai_adapter"] = open_dummy

# Load llm_client into package namespace
llm_spec = importlib.util.spec_from_file_location(
    f"{package_name}.llm_client", base_dir / "llm_client.py"
)
llm_mod = importlib.util.module_from_spec(llm_spec)
llm_spec.loader.exec_module(llm_mod)
sys.modules[f"{package_name}.llm_client"] = llm_mod

# Load main.py as submodule of fake package
main_spec = importlib.util.spec_from_file_location(
    f"{package_name}.main", base_dir / "main.py"
)
arbiter_app = importlib.util.module_from_spec(main_spec)
main_spec.loader.exec_module(arbiter_app)


@pytest.mark.asyncio
async def test_review_endpoint_happy(monkeypatch):
    """Arbiter returns verdict via fake compare function."""

    async def _fake_compare(*_, **__):
        return "a", "Relatório A superior"

    monkeypatch.setattr(arbiter_app, "compare_reports", _fake_compare)

    from arbiter_o3 import llm_client  # type: ignore

    RequestModel = getattr(arbiter_app, "ArbiterRequest")

    payload = RequestModel(
        report_a="Relatório A", report_b="Relatório B", justification="div"
    )

    response = await arbiter_app.review_reports(payload)  # type: ignore[arg-type]

    assert response.verdict == "a"
    assert "Relatório A" in response.rationale
