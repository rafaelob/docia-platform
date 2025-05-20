"""HTTP client helper for the O3-mini Arbiter service.

Used by OrchestratorPrincipal to escalate divergent specialist reports. Keeps
HTTP details isolated from core orchestration logic.
"""
from __future__ import annotations

import os
from enum import Enum
from typing import Optional

import httpx
from pydantic import BaseModel, Field, ConfigDict

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ARBITER_URL_ENV = "ARBITER_O3_URL"
DEFAULT_ARBITER_URL = "http://localhost:8089/arbiter/v1/review"
ARBITER_URL: str = os.getenv(ARBITER_URL_ENV, DEFAULT_ARBITER_URL)


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class ArbiterRequest(BaseModel):
    """Payload forwarded to the arbiter service."""

    report_a: str
    report_b: str
    justification: str
    session_id: Optional[str] = None


class Verdict(str, Enum):
    a = "a"
    b = "b"
    combine = "combine"
    cannot_decide = "cannot_decide"


class ArbiterResponse(BaseModel):
    """Response returned by the arbiter service (or fallback)."""

    model_config = ConfigDict(use_enum_values=True)

    verdict: Verdict = Field(default=Verdict.cannot_decide)
    rationale: str


# ---------------------------------------------------------------------------
# Client helper
# ---------------------------------------------------------------------------

async def send_to_arbiter(request: ArbiterRequest) -> ArbiterResponse:  # pragma: no cover
    """POST a divergence package to the arbiter service and parse response.

    Falls back to local stub response if the service is unreachable.
    """
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            response = await client.post(ARBITER_URL, json=request.model_dump())
            response.raise_for_status()
            # Assume arbiter returns JSON matching ArbiterResponse schema
            return ArbiterResponse.model_validate(response.json())
        except Exception as exc:  # noqa: BLE001
            return ArbiterResponse(verdict="fallback", rationale=f"Arbiter unreachable: {exc}")
