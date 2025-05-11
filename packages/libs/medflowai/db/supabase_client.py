"""Lightweight async Supabase REST client for MedflowAI.

Implements minimal CRUD operations for MVP.
"""
from __future__ import annotations

from typing import Any, Dict, List

import httpx
from pydantic import BaseModel, BaseSettings, Field, validator


class _Settings(BaseSettings):
    """Reads Supabase settings from environment variables."""

    supabase_url: str = Field(..., env="SUPABASE_URL")
    supabase_service_role_key: str = Field(..., env="SUPABASE_SERVICE_ROLE_KEY")

    class Config:
        case_sensitive = False

    @validator("supabase_url", pre=True)
    def _strip_trailing_slash(cls, v: str) -> str:  # noqa: D401,N805
        return v.rstrip("/")


class CaseIn(BaseModel):
    patient_id: str
    specialty: str
    description: str | None = None


class Case(CaseIn):
    id: str
    created_at: str


class ConsultationIn(BaseModel):
    case_id: str
    request: Dict[str, Any]
    response: Dict[str, Any] | None = None


class Consultation(ConsultationIn):
    id: str
    created_at: str


class SupabaseClient:
    """Async client wrapper using Supabase PostgREST endpoints."""

    def __init__(self) -> None:
        self.settings = _Settings()  # type: ignore[arg-type]
        base = self.settings.supabase_url
        self.base_url = f"{base}/rest/v1"
        token = self.settings.supabase_service_role_key
        self.headers = {
            "apikey": token,
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        }
        self.client = httpx.AsyncClient(base_url=self.base_url, headers=self.headers, timeout=10.0)

    # -------------------- CASES -------------------- #
    async def create_case(self, data: CaseIn) -> str:
        resp = await self.client.post("/cases", json=data.dict())
        resp.raise_for_status()
        return resp.json()[0]["id"]

    async def list_cases(self) -> List[Case]:
        resp = await self.client.get("/cases?select=*")
        resp.raise_for_status()
        return [Case(**row) for row in resp.json()]

    # ---------------- CONSULTATIONS --------------- #
    async def add_consultation(self, data: ConsultationIn) -> str:
        resp = await self.client.post("/consultations", json=data.dict())
        resp.raise_for_status()
        return resp.json()[0]["id"]

    async def list_consultations(self, case_id: str) -> List[Consultation]:
        query = f"/consultations?case_id=eq.{case_id}&select=*"
        resp = await self.client.get(query)
        resp.raise_for_status()
        return [Consultation(**row) for row in resp.json()]

    async def close(self) -> None:
        await self.client.aclose()


__all__ = [
    "SupabaseClient",
    "CaseIn",
    "Case",
    "ConsultationIn",
    "Consultation",
]
