from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from civitas.domain.identity.services import (
    normalize_email,
    normalize_provider_name,
    normalize_provider_subject,
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class UserAccount:
    id: UUID
    email: str
    created_at: datetime
    last_sign_in_at: datetime | None

    @classmethod
    def create(
        cls,
        *,
        email: str,
        created_at: datetime | None = None,
    ) -> "UserAccount":
        reference_time = created_at or _utc_now()
        return cls(
            id=uuid4(),
            email=normalize_email(email),
            created_at=reference_time,
            last_sign_in_at=reference_time,
        )


@dataclass(frozen=True)
class AuthIdentity:
    user_id: UUID
    provider_name: str
    provider_subject: str
    email: str
    email_verified: bool
    created_at: datetime
    last_authenticated_at: datetime

    @classmethod
    def create(
        cls,
        *,
        user_id: UUID,
        provider_name: str,
        provider_subject: str,
        email: str,
        email_verified: bool,
        created_at: datetime | None = None,
    ) -> "AuthIdentity":
        reference_time = created_at or _utc_now()
        return cls(
            user_id=user_id,
            provider_name=normalize_provider_name(provider_name),
            provider_subject=normalize_provider_subject(provider_subject),
            email=normalize_email(email),
            email_verified=email_verified,
            created_at=reference_time,
            last_authenticated_at=reference_time,
        )


@dataclass(frozen=True)
class AuthAttempt:
    id: str
    return_to: str
    code_verifier: str
    issued_at: datetime
    expires_at: datetime
    consumed_at: datetime | None

    @classmethod
    def create(
        cls,
        *,
        return_to: str,
        code_verifier: str,
        ttl: timedelta,
        issued_at: datetime | None = None,
    ) -> "AuthAttempt":
        if ttl.total_seconds() <= 0:
            raise ValueError("auth attempt ttl must be greater than zero")
        reference_time = issued_at or _utc_now()
        return cls(
            id=secrets.token_urlsafe(24),
            return_to=return_to,
            code_verifier=code_verifier,
            issued_at=reference_time,
            expires_at=reference_time + ttl,
            consumed_at=None,
        )

    def is_expired(self, *, at: datetime | None = None) -> bool:
        reference_time = at or _utc_now()
        return self.expires_at <= reference_time


@dataclass(frozen=True)
class AppSession:
    token: str
    user_id: UUID
    issued_at: datetime
    last_seen_at: datetime
    expires_at: datetime
    revoked_at: datetime | None
    revoke_reason: str | None

    @classmethod
    def create(
        cls,
        *,
        user_id: UUID,
        ttl: timedelta,
        issued_at: datetime | None = None,
    ) -> "AppSession":
        if ttl.total_seconds() <= 0:
            raise ValueError("session ttl must be greater than zero")
        reference_time = issued_at or _utc_now()
        return cls(
            token=secrets.token_urlsafe(32),
            user_id=user_id,
            issued_at=reference_time,
            last_seen_at=reference_time,
            expires_at=reference_time + ttl,
            revoked_at=None,
            revoke_reason=None,
        )

    def is_expired(self, *, at: datetime | None = None) -> bool:
        reference_time = at or _utc_now()
        return self.expires_at <= reference_time
