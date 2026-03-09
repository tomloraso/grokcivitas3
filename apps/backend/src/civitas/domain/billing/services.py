from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime

from civitas.domain.billing.value_objects import CheckoutProgressStatus


def product_is_already_covered(
    *,
    required_capability_keys: Iterable[str],
    active_capability_keys: Iterable[str],
) -> bool:
    required = {value.strip().casefold() for value in required_capability_keys}
    active = {value.strip().casefold() for value in active_capability_keys}
    return bool(required) and required.issubset(active)


def checkout_status_to_progress_status(
    *,
    checkout_status: str,
    expires_at: datetime | None,
    at: datetime,
) -> CheckoutProgressStatus:
    normalized = checkout_status.strip().casefold()
    if normalized == "completed":
        return "completed"
    if normalized == "canceled":
        return "canceled"
    if normalized == "failed":
        return "failed"
    if normalized == "expired":
        return "expired"
    if expires_at is not None and expires_at <= at:
        return "expired"
    if normalized == "open":
        return "processing_payment"
    return "processing_payment"


def subscription_supports_access(
    *,
    status: str,
    current_period_ends_at: datetime | None,
    at: datetime,
) -> bool:
    normalized = status.strip().casefold()
    if normalized not in {"active", "trialing", "past_due"}:
        return False
    if current_period_ends_at is None:
        return True
    return current_period_ends_at > at
