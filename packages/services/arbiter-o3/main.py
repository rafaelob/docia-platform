"""O3-mini Arbiter stub service.

FastAPI micro-service that accepts two clinical reports plus justification and
returns a placeholder verdict. Future implementation will integrate real O3
model (GPT-4.1 or Gemini) for arbitration.
"""
from __future__ import annotations

import os

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, ConfigDict

from .llm_client import compare_reports, Verdict

app = FastAPI(title="O3-mini Arbiter Stub", version="0.1.0")


class ArbiterRequest(BaseModel):
    """Input payload for arbiter review."""

    report_a: str = Field(..., description="Clinical report from Specialist A")
    report_b: str = Field(..., description="Clinical report from Specialist B")
    justification: str = Field(..., description="LLM justification for divergence")
    session_id: str | None = Field(None, description="Consultation/session identifier")


class ArbiterResponse(BaseModel):
    """Verdict returned by arbiter service."""

    model_config = ConfigDict(use_enum_values=True)

    verdict: Verdict = Field(..., description="Final arbiter decision")
    rationale: str = Field(..., description="Arbiter rationale")

# Ensure Pydantic resolves forward refs when module is imported dynamically
ArbiterResponse.model_rebuild()


@app.post("/arbiter/v1/review", response_model=ArbiterResponse, status_code=202)
async def review_reports(payload: ArbiterRequest) -> ArbiterResponse:  # noqa: D401
    """Endpoint receiving divergent reports for arbitration.

    Current implementation is a stub: it acknowledges receipt and returns a
    'pending' verdict. The real implementation will call an internal
    orchestrator or LLM to generate the verdict.
    """

    try:
        verdict, rationale = await compare_reports(
            report_a=payload.report_a,
            report_b=payload.report_b,
            justification=payload.justification,
        )
        return ArbiterResponse(verdict=verdict, rationale=rationale)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc))


# ---------- Helper for internal calls (used by orchestrator) ---------- #

_ARBITER_URL_ENV = "ARBITER_O3_URL"
DEFAULT_ARBITER_URL = os.getenv(_ARBITER_URL_ENV, "http://localhost:8089/arbiter/v1/review")


async def send_to_arbiter(request: ArbiterRequest) -> ArbiterResponse:
    """Send divergence to arbiter service, fallback to direct stub if offline."""

    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            resp = await client.post(DEFAULT_ARBITER_URL, json=request.model_dump())
            resp.raise_for_status()
            return ArbiterResponse.model_validate(resp.json())
        except Exception as exc:  # noqa: BLE001
            # Log warning here in real service
            return ArbiterResponse(
                verdict="fallback", rationale=f"Arbiter unreachable: {exc}; stubbed."
            )
