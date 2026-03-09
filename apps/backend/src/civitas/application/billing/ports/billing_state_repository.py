from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from civitas.application.billing.dto import BillingReconciliationMutation
from civitas.domain.billing.models import (
    BillingCheckoutSession,
    BillingSubscription,
    PaymentCustomer,
)


class BillingStateRepository(Protocol):
    def get_checkout_session(self, *, checkout_id: UUID) -> BillingCheckoutSession | None: ...

    def get_open_checkout_session(
        self,
        *,
        user_id: UUID,
        product_code: str,
        at: datetime,
    ) -> BillingCheckoutSession | None: ...

    def create_pending_checkout_session(
        self,
        checkout_session: BillingCheckoutSession,
    ) -> BillingCheckoutSession: ...

    def mark_checkout_session_open(
        self,
        *,
        checkout_id: UUID,
        provider_name: str,
        provider_checkout_session_id: str,
        provider_customer_id: str | None,
        provider_subscription_id: str | None,
        checkout_url: str,
        expires_at: datetime | None,
        updated_at: datetime,
    ) -> BillingCheckoutSession | None: ...

    def mark_checkout_session_failed(
        self,
        *,
        checkout_id: UUID,
        updated_at: datetime,
    ) -> BillingCheckoutSession | None: ...

    def get_payment_customer_by_user(
        self,
        *,
        user_id: UUID,
        provider_name: str,
    ) -> PaymentCustomer | None: ...

    def get_payment_customer_by_provider_customer_id(
        self,
        *,
        provider_name: str,
        provider_customer_id: str,
    ) -> PaymentCustomer | None: ...

    def get_subscription_by_provider_subscription_id(
        self,
        *,
        provider_name: str,
        provider_subscription_id: str,
    ) -> BillingSubscription | None: ...

    def get_subscription_by_latest_charge_id(
        self,
        *,
        provider_name: str,
        latest_charge_id: str,
    ) -> BillingSubscription | None: ...

    def get_latest_subscription_by_provider_customer_id(
        self,
        *,
        provider_name: str,
        provider_customer_id: str,
        product_code: str | None = None,
    ) -> BillingSubscription | None: ...

    def get_checkout_session_by_provider_checkout_session_id(
        self,
        *,
        provider_name: str,
        provider_checkout_session_id: str,
    ) -> BillingCheckoutSession | None: ...

    def apply_reconciliation(self, mutation: BillingReconciliationMutation) -> bool: ...
