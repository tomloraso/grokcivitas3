from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID

AnonymousReason = Literal["missing", "invalid", "expired", "revoked", "signed_out"]
SessionState = Literal["anonymous", "authenticated"]


@dataclass(frozen=True)
class AuthFlowStateDto:
    attempt_id: str


@dataclass(frozen=True)
class AuthProviderStartParamsDto:
    email: str
    state: str
    callback_url: str
    code_challenge: str | None
    code_challenge_method: str | None


@dataclass(frozen=True)
class IdentityProviderUserDto:
    provider_name: str
    provider_subject: str
    email: str
    email_verified: bool


@dataclass(frozen=True)
class SessionUserDto:
    id: UUID
    email: str


@dataclass(frozen=True)
class CurrentSessionDto:
    state: SessionState
    user: SessionUserDto | None
    expires_at: datetime | None
    anonymous_reason: AnonymousReason | None

    @classmethod
    def anonymous(cls, *, reason: AnonymousReason) -> "CurrentSessionDto":
        return cls(
            state="anonymous",
            user=None,
            expires_at=None,
            anonymous_reason=reason,
        )

    @classmethod
    def authenticated(
        cls,
        *,
        user: SessionUserDto,
        expires_at: datetime,
    ) -> "CurrentSessionDto":
        return cls(
            state="authenticated",
            user=user,
            expires_at=expires_at,
            anonymous_reason=None,
        )


@dataclass(frozen=True)
class StartSignInResultDto:
    redirect_url: str


@dataclass(frozen=True)
class CompleteAuthCallbackResultDto:
    return_to: str
    session_token: str
    expires_at: datetime
    user: SessionUserDto
