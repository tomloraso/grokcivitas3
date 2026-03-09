from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID

from civitas.application.access.dto import AccountAccessState
from civitas.domain.access.models import EntitlementEvent, EntitlementGrant
from civitas.domain.billing.models import (
    BillingCheckoutSession,
    BillingSubscription,
    PaymentCustomer,
    PaymentEvent,
)
from civitas.domain.billing.value_objects import (
    BillingSubscriptionStatus,
    CheckoutProgressStatus,
    PaymentProviderName,
    ProviderEventEffect,
)

CheckoutCreationStatus = Literal["open", "already_covered"]


@dataclass(frozen=True)
class CreateCheckoutSessionResultDto:
    checkout_id: UUID | None
    product_code: str
    status: CheckoutCreationStatus
    redirect_url: str | None
    expires_at: datetime | None
    account_access_state: AccountAccessState


@dataclass(frozen=True)
class CheckoutStatusDto:
    checkout_id: UUID
    product_code: str
    status: CheckoutProgressStatus
    redirect_url: str | None
    expires_at: datetime | None
    account_access_state: AccountAccessState


@dataclass(frozen=True)
class CreateBillingPortalSessionResultDto:
    redirect_url: str


@dataclass(frozen=True)
class ProviderCheckoutSessionDto:
    provider_name: PaymentProviderName
    provider_checkout_session_id: str
    provider_customer_id: str | None
    provider_subscription_id: str | None
    checkout_url: str
    expires_at: datetime | None


@dataclass(frozen=True)
class ProviderWebhookEventDto:
    provider_name: PaymentProviderName
    provider_event_id: str
    event_type: str
    occurred_at: datetime
    received_at: datetime
    payload: dict[str, object]
    effect: ProviderEventEffect
    checkout_id: UUID | None
    user_id: UUID | None
    product_code: str | None
    provider_customer_id: str | None
    provider_checkout_session_id: str | None
    provider_subscription_id: str | None
    subscription_status: BillingSubscriptionStatus | None
    current_period_starts_at: datetime | None
    current_period_ends_at: datetime | None
    cancel_at_period_end: bool | None
    canceled_at: datetime | None
    latest_invoice_id: str | None
    latest_charge_id: str | None
    revoke_reason_code: str | None


@dataclass(frozen=True)
class BillingReconciliationMutation:
    payment_event: PaymentEvent
    payment_customer: PaymentCustomer | None
    checkout_session: BillingCheckoutSession | None
    subscription: BillingSubscription | None
    entitlement: EntitlementGrant | None
    entitlement_event: EntitlementEvent | None


@dataclass(frozen=True)
class ReconcilePaymentEventResultDto:
    provider_event_id: str
    reconciliation_status: Literal["applied", "duplicate", "ignored", "failed"]
    checkout_id: UUID | None
    entitlement_id: UUID | None
    account_access_state: AccountAccessState | None
