# This file makes 'medflowai' a Python package

# You can optionally expose submodules or specific symbols here for easier imports,
# e.g.:
# from .core.triage_request import TriageRequest
# from .agents.triage_agent import TriageAgent
# from .tools.rag_tool import RAGTool

# --- Ensure subpackages are recognized even if preloaded as stubs in tests --- #
import importlib.util as _imp_util
import pathlib as _pt
import sys as _sys
import importlib as _il

_adapters_pkg_name = f"{__name__}.adapters"
if _adapters_pkg_name in _sys.modules:
    _adapters_mod = _sys.modules[_adapters_pkg_name]
    # If tests inserted a simple ModuleType without __path__, turn it into a namespace pkg
    if getattr(_adapters_mod, "__path__", None) is None:
        _adapters_mod.__path__ = [
            str((_pt.Path(__file__).parent / "adapters").resolve())
        ]
else:
    # Regular import when not preloaded by tests -> perform normal import so that it's a package
    _il.import_module(_adapters_pkg_name)

# Ensure core adapter module is discoverable during early imports
try:
    _il.import_module(f"{_adapters_pkg_name}.base_llm_adapter")
except ModuleNotFoundError:
    # If missing during test stubs, that's acceptable – agents requiring it will stub as needed
    pass
