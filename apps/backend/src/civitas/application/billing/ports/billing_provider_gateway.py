from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from civitas.application.billing.dto import ProviderCheckoutSessionDto, ProviderWebhookEventDto
from civitas.domain.billing.value_objects import PaymentProviderName


class BillingProviderGateway(Protocol):
    provider_name: PaymentProviderName

    def create_checkout_session(
        self,
        *,
        checkout_id: UUID,
        product_code: str,
        product_price_lookup_key: str,
        user_id: UUID,
        user_email: str,
        success_url: str,
        cancel_url: str,
        existing_customer_id: str | None,
    ) -> ProviderCheckoutSessionDto: ...

    def create_billing_portal_session(
        self,
        *,
        provider_customer_id: str,
        return_url: str,
    ) -> str: ...

    def verify_and_parse_webhook_event(
        self,
        *,
        payload: bytes,
        signature_header: str | None,
        received_at: datetime,
    ) -> ProviderWebhookEventDto: ...
