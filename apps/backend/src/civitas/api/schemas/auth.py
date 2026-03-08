from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class AuthStartRequest(BaseModel):
    email: str
    return_to: str | None = None


class AuthStartResponse(BaseModel):
    redirect_url: str


class SessionUserResponse(BaseModel):
    id: UUID
    email: str


class SessionResponse(BaseModel):
    state: Literal["anonymous", "authenticated"]
    user: SessionUserResponse | None
    expires_at: datetime | None
    anonymous_reason: Literal["missing", "invalid", "expired", "revoked", "signed_out"] | None
