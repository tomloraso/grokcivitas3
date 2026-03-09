from __future__ import annotations

from datetime import datetime
from uuid import UUID

from civitas.application.billing.dto import ProviderCheckoutSessionDto, ProviderWebhookEventDto
from civitas.application.billing.errors import PaymentProviderUnavailableError
from civitas.application.billing.ports.billing_provider_gateway import BillingProviderGateway
from civitas.infrastructure.config.settings import AppSettings
from civitas.infrastructure.payments.stripe_billing_provider_gateway import (
    StripeBillingProviderGateway,
)


class DisabledBillingProviderGateway(BillingProviderGateway):
    provider_name = "stripe"

    def __init__(self, message: str = "Billing is not enabled.") -> None:
        self._message = message

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
    ) -> ProviderCheckoutSessionDto:
        raise PaymentProviderUnavailableError(self._message)

    def create_billing_portal_session(
        self,
        *,
        provider_customer_id: str,
        return_url: str,
    ) -> str:
        raise PaymentProviderUnavailableError(self._message)

    def verify_and_parse_webhook_event(
        self,
        *,
        payload: bytes,
        signature_header: str | None,
        received_at: datetime,
    ) -> ProviderWebhookEventDto:
        raise PaymentProviderUnavailableError(self._message)


def build_billing_provider_gateway(settings: AppSettings) -> BillingProviderGateway:
    if not settings.billing.enabled:
        return DisabledBillingProviderGateway()

    stripe_settings = settings.billing.stripe
    if settings.billing.provider == "stripe" and stripe_settings is not None:
        return StripeBillingProviderGateway(
            secret_key=stripe_settings.secret_key,
            webhook_secret=stripe_settings.webhook_secret,
            portal_configuration_id=stripe_settings.portal_configuration_id,
        )

    return DisabledBillingProviderGateway("Billing provider is not configured.")
