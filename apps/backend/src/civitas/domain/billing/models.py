from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from civitas.domain.access.value_objects import ProductCode, normalize_product_code
from civitas.domain.billing.value_objects import (
    BillingSubscriptionStatus,
    CheckoutSessionStatus,
    PaymentEventReconciliationStatus,
    PaymentProviderName,
    ProviderEventEffect,
    normalize_billing_subscription_status,
    normalize_checkout_session_status,
    normalize_payment_event_reconciliation_status,
    normalize_provider_event_effect,
    normalize_provider_name,
)


def _normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


@dataclass(frozen=True)
class PaymentCustomer:
    user_id: UUID
    provider_name: PaymentProviderName
    provider_customer_id: str
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "provider_name", normalize_provider_name(self.provider_name))
        provider_customer_id = _normalize_text(self.provider_customer_id)
        if provider_customer_id is None:
            raise ValueError("provider customer id must not be blank")
        object.__setattr__(self, "provider_customer_id", provider_customer_id)


@dataclass(frozen=True)
class BillingCheckoutSession:
    id: UUID
    user_id: UUID
    product_code: ProductCode
    provider_name: PaymentProviderName
    provider_checkout_session_id: str | None
    provider_customer_id: str | None
    provider_subscription_id: str | None
    status: CheckoutSessionStatus
    checkout_url: str | None
    success_path: str
    cancel_path: str
    requested_at: datetime
    expires_at: datetime | None
    completed_at: datetime | None
    canceled_at: datetime | None
    updated_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "product_code", normalize_product_code(self.product_code))
        object.__setattr__(self, "provider_name", normalize_provider_name(self.provider_name))
        object.__setattr__(
            self,
            "provider_checkout_session_id",
            _normalize_text(self.provider_checkout_session_id),
        )
        object.__setattr__(self, "provider_customer_id", _normalize_text(self.provider_customer_id))
        object.__setattr__(
            self,
            "provider_subscription_id",
            _normalize_text(self.provider_subscription_id),
        )
        object.__setattr__(self, "status", normalize_checkout_session_status(self.status))

    def is_open_at(self, *, at: datetime) -> bool:
        if self.status != "open":
            return False
        if self.completed_at is not None or self.canceled_at is not None:
            return False
        return self.expires_at is None or self.expires_at > at


@dataclass(frozen=True)
class BillingSubscription:
    id: UUID
    user_id: UUID
    product_code: ProductCode
    provider_name: PaymentProviderName
    provider_subscription_id: str
    provider_customer_id: str | None
    status: BillingSubscriptionStatus
    current_period_starts_at: datetime | None
    current_period_ends_at: datetime | None
    cancel_at_period_end: bool
    canceled_at: datetime | None
    latest_checkout_session_id: UUID | None
    entitlement_id: UUID | None
    latest_invoice_id: str | None
    latest_charge_id: str | None
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "product_code", normalize_product_code(self.product_code))
        object.__setattr__(self, "provider_name", normalize_provider_name(self.provider_name))
        provider_subscription_id = _normalize_text(self.provider_subscription_id)
        if provider_subscription_id is None:
            raise ValueError("provider subscription id must not be blank")
        object.__setattr__(self, "provider_subscription_id", provider_subscription_id)
        object.__setattr__(self, "provider_customer_id", _normalize_text(self.provider_customer_id))
        object.__setattr__(self, "status", normalize_billing_subscription_status(self.status))
        object.__setattr__(self, "latest_invoice_id", _normalize_text(self.latest_invoice_id))
        object.__setattr__(self, "latest_charge_id", _normalize_text(self.latest_charge_id))


@dataclass(frozen=True)
class PaymentEvent:
    id: UUID
    provider_name: PaymentProviderName
    provider_event_id: str
    event_type: str
    effect: ProviderEventEffect
    occurred_at: datetime
    received_at: datetime
    payload: dict[str, object]
    signature_verified: bool
    checkout_id: UUID | None
    user_id: UUID | None
    product_code: ProductCode | None
    provider_customer_id: str | None
    provider_checkout_session_id: str | None
    provider_subscription_id: str | None
    latest_invoice_id: str | None
    latest_charge_id: str | None
    reconciliation_status: PaymentEventReconciliationStatus
    reconciled_at: datetime | None

    def __post_init__(self) -> None:
        object.__setattr__(self, "provider_name", normalize_provider_name(self.provider_name))
        provider_event_id = _normalize_text(self.provider_event_id)
        if provider_event_id is None:
            raise ValueError("provider event id must not be blank")
        event_type = _normalize_text(self.event_type)
        if event_type is None:
            raise ValueError("provider event type must not be blank")
        object.__setattr__(self, "provider_event_id", provider_event_id)
        object.__setattr__(self, "event_type", event_type)
        object.__setattr__(self, "effect", normalize_provider_event_effect(self.effect))
        if self.product_code is not None:
            object.__setattr__(self, "product_code", normalize_product_code(self.product_code))
        object.__setattr__(self, "provider_customer_id", _normalize_text(self.provider_customer_id))
        object.__setattr__(
            self,
            "provider_checkout_session_id",
            _normalize_text(self.provider_checkout_session_id),
        )
        object.__setattr__(
            self,
            "provider_subscription_id",
            _normalize_text(self.provider_subscription_id),
        )
        object.__setattr__(self, "latest_invoice_id", _normalize_text(self.latest_invoice_id))
        object.__setattr__(self, "latest_charge_id", _normalize_text(self.latest_charge_id))
        object.__setattr__(
            self,
            "reconciliation_status",
            normalize_payment_event_reconciliation_status(self.reconciliation_status),
        )
