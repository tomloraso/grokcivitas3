from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class SectionAccessResponse(BaseModel):
    state: Literal["available", "locked", "unavailable"]
    capability_key: str | None
    reason_code: (
        Literal[
            "free_baseline",
            "premium_capability_missing",
            "anonymous_user",
            "artefact_not_published",
            "artefact_not_supported",
            "entitlement_expired",
            "entitlement_revoked",
        ]
        | None
    )
    product_codes: list[str] = Field(default_factory=list)
    requires_auth: bool
    requires_purchase: bool
    school_name: str | None = None


class AccountEntitlementResponse(BaseModel):
    id: UUID
    product_code: str
    product_display_name: str
    capability_keys: list[str] = Field(default_factory=list)
    status: Literal["pending", "active", "expired", "revoked"]
    starts_at: datetime
    ends_at: datetime | None
    revoked_at: datetime | None
    revoked_reason_code: str | None


class AccountAccessResponse(BaseModel):
    account_access_state: Literal["anonymous", "free", "pending", "premium"]
    capability_keys: list[str] = Field(default_factory=list)
    access_epoch: str
    entitlements: list[AccountEntitlementResponse] = Field(default_factory=list)
