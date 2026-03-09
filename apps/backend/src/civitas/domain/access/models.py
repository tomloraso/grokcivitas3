from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from civitas.domain.access.value_objects import (
    AccessDecisionReasonCode,
    AccessLevel,
    AccessRequirementKey,
    BillingInterval,
    CapabilityKey,
    EntitlementEventType,
    EntitlementStatus,
    PersistedEntitlementStatus,
    ProductCode,
    SectionState,
    normalize_access_requirement_key,
    normalize_capability_key,
    normalize_product_code,
)


@dataclass(frozen=True)
class PremiumProduct:
    code: ProductCode
    display_name: str
    description: str | None
    billing_interval: BillingInterval | None
    duration_days: int | None
    provider_price_lookup_key: str | None
    capability_keys: tuple[CapabilityKey, ...]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "code", normalize_product_code(self.code))
        object.__setattr__(
            self,
            "capability_keys",
            tuple(sorted(normalize_capability_key(key) for key in self.capability_keys)),
        )

    def grants_capability(self, capability_key: CapabilityKey) -> bool:
        return normalize_capability_key(capability_key) in self.capability_keys


@dataclass(frozen=True)
class EntitlementGrant:
    id: UUID
    user_id: UUID
    product_code: ProductCode
    status: PersistedEntitlementStatus
    starts_at: datetime
    ends_at: datetime | None
    revoked_at: datetime | None
    revoked_reason_code: str | None
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "product_code", normalize_product_code(self.product_code))

    def effective_status(self, *, at: datetime) -> EntitlementStatus:
        if self.status == "revoked" or self.revoked_at is not None:
            return "revoked"
        if self.status == "pending":
            return "pending"
        if self.starts_at > at:
            return "pending"
        if self.ends_at is not None and self.ends_at <= at:
            return "expired"
        return "active"

    def is_active_at(self, *, at: datetime) -> bool:
        return self.effective_status(at=at) == "active"


@dataclass(frozen=True)
class EntitlementEvent:
    id: UUID
    entitlement_id: UUID
    user_id: UUID
    product_code: ProductCode
    event_type: EntitlementEventType
    occurred_at: datetime
    reason_code: str | None
    provider_name: str | None
    provider_event_id: str | None
    correlation_id: str | None

    def __post_init__(self) -> None:
        object.__setattr__(self, "product_code", normalize_product_code(self.product_code))


@dataclass(frozen=True)
class AccessRequirement:
    key: AccessRequirementKey
    capability_key: CapabilityKey | None

    def __post_init__(self) -> None:
        object.__setattr__(self, "key", normalize_access_requirement_key(self.key))
        if self.capability_key is not None:
            object.__setattr__(
                self,
                "capability_key",
                normalize_capability_key(self.capability_key),
            )


@dataclass(frozen=True)
class AccessDecision:
    requirement_key: AccessRequirementKey
    access_level: AccessLevel
    section_state: SectionState
    capability_key: CapabilityKey | None
    reason_code: AccessDecisionReasonCode | None
    available_product_codes: tuple[ProductCode, ...]
    requires_auth: bool
    requires_purchase: bool
