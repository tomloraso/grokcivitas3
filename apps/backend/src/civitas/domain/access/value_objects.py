from typing import Literal

CapabilityKey = str
ProductCode = str
AccessRequirementKey = str
BillingInterval = Literal["monthly", "annual", "one_time"]
PersistedEntitlementStatus = Literal["pending", "active", "revoked"]
EntitlementStatus = Literal["pending", "active", "expired", "revoked"]
AccessLevel = Literal[
    "free",
    "preview_only",
    "premium_unlocked",
    "requires_auth",
    "requires_purchase",
]
SectionState = Literal["available", "locked", "unavailable"]
AccessDecisionReasonCode = Literal[
    "free_baseline",
    "premium_capability_missing",
    "anonymous_user",
    "artefact_not_published",
    "artefact_not_supported",
    "entitlement_expired",
    "entitlement_revoked",
]
EntitlementEventType = str


def normalize_capability_key(value: str) -> CapabilityKey:
    normalized = value.strip().casefold()
    if not normalized:
        raise ValueError("capability key must not be blank")
    return normalized


def normalize_product_code(value: str) -> ProductCode:
    normalized = value.strip().casefold()
    if not normalized:
        raise ValueError("product code must not be blank")
    return normalized


def normalize_access_requirement_key(value: str) -> AccessRequirementKey:
    normalized = value.strip().casefold()
    if not normalized:
        raise ValueError("access requirement key must not be blank")
    return normalized
