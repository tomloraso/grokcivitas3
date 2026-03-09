from typing import Literal

PaymentProviderName = Literal["stripe"]
CheckoutSessionStatus = Literal[
    "pending_provider",
    "open",
    "completed",
    "expired",
    "canceled",
    "failed",
]
CheckoutProgressStatus = Literal[
    "open",
    "already_covered",
    "processing_payment",
    "completed",
    "canceled",
    "expired",
    "failed",
]
BillingSubscriptionStatus = Literal[
    "incomplete",
    "incomplete_expired",
    "trialing",
    "active",
    "past_due",
    "canceled",
    "unpaid",
    "paused",
]
PaymentEventReconciliationStatus = Literal["pending", "applied", "duplicate", "ignored", "failed"]
ProviderEventEffect = Literal[
    "checkout_completed",
    "invoice_paid",
    "invoice_payment_failed",
    "subscription_updated",
    "subscription_deleted",
    "charge_refunded",
    "charge_disputed",
    "ignored",
]


def normalize_provider_name(value: str) -> PaymentProviderName:
    normalized = value.strip().casefold()
    if normalized != "stripe":
        raise ValueError("provider name must be stripe")
    return "stripe"


def normalize_checkout_session_status(value: str) -> CheckoutSessionStatus:
    normalized = value.strip().casefold()
    if normalized not in {
        "pending_provider",
        "open",
        "completed",
        "expired",
        "canceled",
        "failed",
    }:
        raise ValueError(f"unsupported checkout session status '{value}'")
    return normalized  # type: ignore[return-value]


def normalize_billing_subscription_status(value: str) -> BillingSubscriptionStatus:
    normalized = value.strip().casefold()
    if normalized not in {
        "incomplete",
        "incomplete_expired",
        "trialing",
        "active",
        "past_due",
        "canceled",
        "unpaid",
        "paused",
    }:
        raise ValueError(f"unsupported billing subscription status '{value}'")
    return normalized  # type: ignore[return-value]


def normalize_payment_event_reconciliation_status(value: str) -> PaymentEventReconciliationStatus:
    normalized = value.strip().casefold()
    if normalized not in {"pending", "applied", "duplicate", "ignored", "failed"}:
        raise ValueError(f"unsupported payment event reconciliation status '{value}'")
    return normalized  # type: ignore[return-value]


def normalize_provider_event_effect(value: str) -> ProviderEventEffect:
    normalized = value.strip().casefold()
    if normalized not in {
        "checkout_completed",
        "invoice_paid",
        "invoice_payment_failed",
        "subscription_updated",
        "subscription_deleted",
        "charge_refunded",
        "charge_disputed",
        "ignored",
    }:
        raise ValueError(f"unsupported provider event effect '{value}'")
    return normalized  # type: ignore[return-value]
