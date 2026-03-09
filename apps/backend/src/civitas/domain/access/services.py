from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from uuid import UUID

from civitas.domain.access.models import AccessDecision, AccessRequirement, EntitlementGrant
from civitas.domain.access.value_objects import (
    AccessDecisionReasonCode,
    ProductCode,
    normalize_capability_key,
)


def infer_missing_access_reason(
    *,
    relevant_entitlements: Iterable[EntitlementGrant],
    relevant_product_codes: Iterable[ProductCode],
    at: datetime,
) -> AccessDecisionReasonCode:
    product_codes = set(relevant_product_codes)
    statuses = {
        entitlement.effective_status(at=at)
        for entitlement in relevant_entitlements
        if entitlement.product_code in product_codes
    }
    if "revoked" in statuses:
        return "entitlement_revoked"
    if "expired" in statuses:
        return "entitlement_expired"
    return "premium_capability_missing"


def build_access_decision(
    *,
    requirement: AccessRequirement,
    user_id: UUID | None,
    active_capability_keys: Iterable[str],
    relevant_entitlements: Iterable[EntitlementGrant],
    available_product_codes: Iterable[ProductCode],
    at: datetime,
    allow_preview: bool,
) -> AccessDecision:
    if requirement.capability_key is None:
        return AccessDecision(
            requirement_key=requirement.key,
            access_level="free",
            section_state="available",
            capability_key=None,
            reason_code="free_baseline",
            available_product_codes=(),
            requires_auth=False,
            requires_purchase=False,
        )

    normalized_capability_keys = {
        normalize_capability_key(capability_key) for capability_key in active_capability_keys
    }
    normalized_product_codes = tuple(sorted(set(available_product_codes)))

    if requirement.capability_key in normalized_capability_keys:
        return AccessDecision(
            requirement_key=requirement.key,
            access_level="premium_unlocked",
            section_state="available",
            capability_key=requirement.capability_key,
            reason_code=None,
            available_product_codes=normalized_product_codes,
            requires_auth=False,
            requires_purchase=False,
        )

    if user_id is None:
        return AccessDecision(
            requirement_key=requirement.key,
            access_level="preview_only" if allow_preview else "requires_auth",
            section_state="locked",
            capability_key=requirement.capability_key,
            reason_code="anonymous_user",
            available_product_codes=normalized_product_codes,
            requires_auth=True,
            requires_purchase=False,
        )

    return AccessDecision(
        requirement_key=requirement.key,
        access_level="preview_only" if allow_preview else "requires_purchase",
        section_state="locked",
        capability_key=requirement.capability_key,
        reason_code=infer_missing_access_reason(
            relevant_entitlements=relevant_entitlements,
            relevant_product_codes=normalized_product_codes,
            at=at,
        ),
        available_product_codes=normalized_product_codes,
        requires_auth=False,
        requires_purchase=True,
    )
