"""Configuration loader for MedflowAI orchestrations.

This module reads YAML definitions under ``config/orchestrations/`` and parses
them into strongly-typed Pydantic models.  The default architecture (``dual_llm_v1``)
mirrors the hard-coded flow baked into :pyclass:`medflowai.core.orchestrator.OrchestratorPrincipal`.

Future tasks (T-38/T-39/T-42) will wire these models into the runtime orchestrator
so users can select alternative flows via CLI/env.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union
import os

import yaml  # type: ignore
from pydantic import BaseModel, Field, field_validator, model_validator, ValidationError

# ---------------------------------------------------------------------------
# Typed Models
# ---------------------------------------------------------------------------

class OrchestrationStep(BaseModel):
    """One step in the orchestration flow (agent or tool)."""

    type: Literal["agent", "tool", "parallel"] = Field(..., description="Kind of step to execute.")
    name: str | None = Field(
        None,
        description="Import path or registry key of the agent/tool class. Not required for parallel steps.",
    )
    on_error: Literal["retry", "skip", "abort"] = Field(
        "retry", description="Error reaction if the step fails."
    )
    agents: List["OrchestrationStep"] | None = Field(
        None,
        description="List of agent steps to run in parallel (only for type='parallel').",
    )
    condition: str | None = Field(
        None,
        description="Condition expression (e.g., '{{ diverged }}') to evaluate before executing this step.",
    )

    @model_validator(mode="after")
    def validate_step(self) -> "OrchestrationStep":
        if self.type in ("agent", "tool") and not self.name:
            raise ValueError(f"'name' is required for {self.type} steps")
        if self.type == "parallel":
            if not self.agents:
                raise ValueError("'agents' list is required for parallel steps")
            if not all(a.type in ("agent", "tool") for a in (self.agents or [])):
                raise ValueError("Parallel steps can only contain 'agent' or 'tool' steps")
        return self


class OrchestrationConfig(BaseModel):
    """Parsed YAML representation."""

    id: str = Field(..., pattern=r"^[a-z0-9_\-]+$", description="Slug/identifier of the config.")
    description: str
    flow: List[OrchestrationStep]
    llm_overrides: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, description="Per-agent LLM param overrides."
    )
    env: List[str] | None = Field(
        default=None,
        description="List of required environment variables.",
    )
    version: str | None = Field(
        None,
        description="SemVer of authoring library.",
        pattern=r"^\d+\.\d+\.\d+(-[a-zA-Z0-9\.]+)?$",
    )

    @field_validator("flow")
    @classmethod
    def _non_empty_flow(cls, v: List[OrchestrationStep]):  # noqa: D401 – validator
        if not v:
            raise ValueError("`flow` must contain at least one step.")
        return v


# ---------------------------------------------------------------------------
# Loader API
# ---------------------------------------------------------------------------

CONFIG_ROOT = Path(__file__).resolve().parents[4] / "config" / "orchestrations"
DEFAULT_ORCHESTRATION_ID = "dual_llm_v1"
_ENV_KEY = "ORCHESTRATION_ID"


def load_orchestration_config(config_id: str | None = None) -> OrchestrationConfig:
    """Load and parse an orchestration YAML file.

    Order of precedence to select the *config_id*:
    1. Explicit *config_id* argument.
    2. Environment variable ``ORCHESTRATION_ID``.
    3. :pydata:`DEFAULT_ORCHESTRATION_ID`.
    """

    selected_id = config_id or os.getenv(_ENV_KEY, DEFAULT_ORCHESTRATION_ID)
    file_path = CONFIG_ROOT / f"{selected_id}.yaml"

    if not file_path.is_file():
        raise FileNotFoundError(
            f"Orchestration config '{selected_id}' not found at {file_path}."
        )

    with file_path.open("r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)

    try:
        cfg = OrchestrationConfig.model_validate(raw)
    except ValidationError as ve:
        raise ValueError(f"Invalid orchestration config '{selected_id}': {ve}") from ve

    # Check required env vars
    if cfg.env:
        missing = [var for var in cfg.env if var not in os.environ]
        if missing:
            raise EnvironmentError(
                f"Missing required environment variables for orchestration '{selected_id}': {', '.join(missing)}"
            )

    return cfg


__all__ = ["OrchestrationConfig", "OrchestrationStep", "load_orchestration_config"]
