from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any, cast
from uuid import UUID

import stripe

from civitas.application.billing.dto import (
    ProviderCheckoutSessionDto,
    ProviderWebhookEventDto,
)
from civitas.application.billing.errors import (
    PaymentEventVerificationError,
    PaymentProviderUnavailableError,
)
from civitas.application.billing.ports.billing_provider_gateway import BillingProviderGateway
from civitas.domain.billing.value_objects import (
    BillingSubscriptionStatus,
    ProviderEventEffect,
    normalize_billing_subscription_status,
)


class StripeBillingProviderGateway(BillingProviderGateway):
    provider_name = "stripe"

    def __init__(
        self,
        *,
        secret_key: str,
        webhook_secret: str,
        portal_configuration_id: str | None = None,
        client: stripe.StripeClient | None = None,
    ) -> None:
        self._webhook_secret = webhook_secret
        self._portal_configuration_id = portal_configuration_id
        self._client = client or stripe.StripeClient(secret_key)

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
        metadata = {
            "checkout_id": str(checkout_id),
            "product_code": product_code,
            "user_id": str(user_id),
        }
        params: dict[str, object] = {
            "mode": "subscription",
            "success_url": success_url,
            "cancel_url": cancel_url,
            "client_reference_id": str(checkout_id),
            "line_items": [
                {
                    "price": self._lookup_price_id(product_price_lookup_key),
                    "quantity": 1,
                }
            ],
            "metadata": metadata,
            "subscription_data": {"metadata": metadata},
        }
        if existing_customer_id is not None:
            params["customer"] = existing_customer_id
        else:
            params["customer_email"] = user_email

        try:
            session = self._client.v1.checkout.sessions.create(cast(Any, params))
        except stripe.StripeError as exc:
            raise PaymentProviderUnavailableError("Stripe checkout is unavailable.") from exc

        payload = session.to_dict_recursive()
        checkout_session_id = _required_text(payload.get("id"), "checkout session id")
        checkout_url = _required_text(payload.get("url"), "checkout session url")
        return ProviderCheckoutSessionDto(
            provider_name=self.provider_name,
            provider_checkout_session_id=checkout_session_id,
            provider_customer_id=_string_or_none(payload.get("customer")),
            provider_subscription_id=_string_or_none(payload.get("subscription")),
            checkout_url=checkout_url,
            expires_at=_timestamp_to_datetime(payload.get("expires_at")),
        )

    def create_billing_portal_session(
        self,
        *,
        provider_customer_id: str,
        return_url: str,
    ) -> str:
        params: dict[str, object] = {
            "customer": provider_customer_id,
            "return_url": return_url,
        }
        if self._portal_configuration_id is not None:
            params["configuration"] = self._portal_configuration_id

        try:
            session = self._client.v1.billing_portal.sessions.create(cast(Any, params))
        except stripe.StripeError as exc:
            raise PaymentProviderUnavailableError("Stripe billing portal is unavailable.") from exc

        payload = session.to_dict_recursive()
        return _required_text(payload.get("url"), "billing portal url")

    def verify_and_parse_webhook_event(
        self,
        *,
        payload: bytes,
        signature_header: str | None,
        received_at: datetime,
    ) -> ProviderWebhookEventDto:
        if signature_header is None or not signature_header.strip():
            raise PaymentEventVerificationError("Stripe signature header is missing.")

        try:
            stripe.Webhook.construct_event(
                payload=payload,
                sig_header=signature_header,
                secret=self._webhook_secret,
            )
        except ValueError as exc:
            raise PaymentEventVerificationError("Stripe webhook payload is invalid.") from exc
        except stripe.SignatureVerificationError as exc:
            raise PaymentEventVerificationError(
                "Stripe webhook signature could not be verified."
            ) from exc

        try:
            event_payload = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise PaymentEventVerificationError("Stripe webhook payload is invalid.") from exc
        if not isinstance(event_payload, dict):
            raise PaymentEventVerificationError("Stripe webhook payload is invalid.")
        return _to_provider_webhook_event(event_payload=event_payload, received_at=received_at)

    def _lookup_price_id(self, lookup_key: str) -> str:
        try:
            response = self._client.v1.prices.list(
                {
                    "lookup_keys": [lookup_key],
                    "active": True,
                    "limit": 10,
                }
            )
        except stripe.StripeError as exc:
            raise PaymentProviderUnavailableError("Stripe price lookup is unavailable.") from exc

        candidates = [
            item.to_dict_recursive() if hasattr(item, "to_dict_recursive") else item
            for item in response.data
        ]
        recurring_candidates = [
            item
            for item in candidates
            if isinstance(item, dict)
            and _string_or_none(item.get("lookup_key")) == lookup_key
            and isinstance(item.get("recurring"), dict)
        ]
        if recurring_candidates:
            return _required_text(recurring_candidates[0].get("id"), "price id")
        for item in candidates:
            if isinstance(item, dict) and _string_or_none(item.get("lookup_key")) == lookup_key:
                return _required_text(item.get("id"), "price id")
        raise PaymentProviderUnavailableError(
            f"Stripe price lookup key '{lookup_key}' is not configured."
        )


def _to_provider_webhook_event(
    *,
    event_payload: dict[str, object],
    received_at: datetime,
) -> ProviderWebhookEventDto:
    event_type = _required_text(event_payload.get("type"), "event type")
    effect = _effect_for_event_type(event_type)
    event_object = _get_event_object(event_payload)
    metadata = _find_metadata(event_object)

    checkout_id = _uuid_or_none(metadata.get("checkout_id"))
    user_id = _uuid_or_none(metadata.get("user_id"))
    product_code = _string_or_none(metadata.get("product_code"))
    provider_customer_id = _string_or_none(event_object.get("customer"))
    provider_checkout_session_id = _provider_checkout_session_id(
        event_type=event_type,
        event_object=event_object,
    )
    provider_subscription_id = _provider_subscription_id(
        event_type=event_type,
        event_object=event_object,
    )
    subscription_status = _subscription_status_for_event(
        event_type=event_type,
        event_object=event_object,
    )
    period_starts_at, period_ends_at = _period_bounds_for_event(
        event_type=event_type,
        event_object=event_object,
    )
    latest_invoice_id = _latest_invoice_id(event_type=event_type, event_object=event_object)
    latest_charge_id = _latest_charge_id(event_type=event_type, event_object=event_object)
    canceled_at = _timestamp_to_datetime(event_object.get("canceled_at"))

    return ProviderWebhookEventDto(
        provider_name="stripe",
        provider_event_id=_required_text(event_payload.get("id"), "event id"),
        event_type=event_type,
        occurred_at=_timestamp_to_datetime(event_payload.get("created")) or received_at,
        received_at=received_at,
        payload=event_payload,
        effect=effect,
        checkout_id=checkout_id,
        user_id=user_id,
        product_code=product_code,
        provider_customer_id=provider_customer_id,
        provider_checkout_session_id=provider_checkout_session_id,
        provider_subscription_id=provider_subscription_id,
        subscription_status=subscription_status,
        current_period_starts_at=period_starts_at,
        current_period_ends_at=period_ends_at,
        cancel_at_period_end=_bool_or_none(event_object.get("cancel_at_period_end")),
        canceled_at=canceled_at,
        latest_invoice_id=latest_invoice_id,
        latest_charge_id=latest_charge_id,
        revoke_reason_code=_revoke_reason_code(effect),
    )


def _effect_for_event_type(event_type: str) -> ProviderEventEffect:
    normalized = event_type.strip().casefold()
    if normalized == "checkout.session.completed":
        return "checkout_completed"
    if normalized == "invoice.paid":
        return "invoice_paid"
    if normalized == "invoice.payment_failed":
        return "invoice_payment_failed"
    if normalized in {"customer.subscription.created", "customer.subscription.updated"}:
        return "subscription_updated"
    if normalized == "customer.subscription.deleted":
        return "subscription_deleted"
    if normalized == "charge.refunded":
        return "charge_refunded"
    if normalized == "charge.dispute.created":
        return "charge_disputed"
    return "ignored"


def _get_event_object(event_payload: dict[str, object]) -> dict[str, object]:
    data = event_payload.get("data")
    if not isinstance(data, dict):
        return {}
    event_object = data.get("object")
    if not isinstance(event_object, dict):
        return {}
    return event_object


def _find_metadata(event_object: dict[str, object]) -> dict[str, object]:
    candidates = (
        event_object.get("metadata"),
        _path(event_object, "subscription_details", "metadata"),
        _path(event_object, "parent", "subscription_details", "metadata"),
        _path(event_object, "subscription_data", "metadata"),
        _path(event_object, "lines", "data", 0, "metadata"),
    )
    for candidate in candidates:
        if isinstance(candidate, dict):
            return candidate
    return {}


def _provider_checkout_session_id(
    *,
    event_type: str,
    event_object: dict[str, object],
) -> str | None:
    if event_type == "checkout.session.completed":
        return _string_or_none(event_object.get("id"))
    return _string_or_none(event_object.get("checkout_session"))


def _provider_subscription_id(
    *,
    event_type: str,
    event_object: dict[str, object],
) -> str | None:
    if event_type.startswith("customer.subscription."):
        return _string_or_none(event_object.get("id"))
    return _string_or_none(event_object.get("subscription"))


def _subscription_status_for_event(
    *,
    event_type: str,
    event_object: dict[str, object],
) -> BillingSubscriptionStatus | None:
    if event_type.startswith("customer.subscription."):
        status = _string_or_none(event_object.get("status"))
        if status is None:
            return None
        try:
            return normalize_billing_subscription_status(status)
        except ValueError:
            return None
    if event_type == "invoice.paid":
        return "active"
    if event_type == "invoice.payment_failed":
        return "past_due"
    return None


def _period_bounds_for_event(
    *,
    event_type: str,
    event_object: dict[str, object],
) -> tuple[datetime | None, datetime | None]:
    if event_type.startswith("customer.subscription."):
        return (
            _timestamp_to_datetime(event_object.get("current_period_start")),
            _timestamp_to_datetime(event_object.get("current_period_end")),
        )
    if event_type.startswith("invoice."):
        invoice_line = _path(event_object, "lines", "data", 0)
        if isinstance(invoice_line, dict):
            return (
                _timestamp_to_datetime(_path(invoice_line, "period", "start")),
                _timestamp_to_datetime(_path(invoice_line, "period", "end")),
            )
        return (
            _timestamp_to_datetime(event_object.get("period_start")),
            _timestamp_to_datetime(event_object.get("period_end")),
        )
    return None, None


def _latest_invoice_id(*, event_type: str, event_object: dict[str, object]) -> str | None:
    if event_type.startswith("invoice."):
        return _string_or_none(event_object.get("id"))
    if event_type.startswith("customer.subscription."):
        latest_invoice = event_object.get("latest_invoice")
        if isinstance(latest_invoice, dict):
            return _string_or_none(latest_invoice.get("id"))
        return _string_or_none(latest_invoice)
    return _string_or_none(event_object.get("invoice"))


def _latest_charge_id(*, event_type: str, event_object: dict[str, object]) -> str | None:
    if event_type.startswith("invoice."):
        return _string_or_none(event_object.get("charge")) or _string_or_none(
            _path(event_object, "payments", "data", 0, "payment", "charge")
        )
    if event_type.startswith("charge."):
        return _string_or_none(event_object.get("id"))
    if event_type.startswith("customer.subscription."):
        latest_invoice = event_object.get("latest_invoice")
        if isinstance(latest_invoice, dict):
            return _string_or_none(latest_invoice.get("charge")) or _string_or_none(
                _path(latest_invoice, "payments", "data", 0, "payment", "charge")
            )
    return None


def _revoke_reason_code(effect: ProviderEventEffect) -> str | None:
    if effect == "charge_refunded":
        return "refund"
    if effect == "charge_disputed":
        return "dispute"
    return None


def _path(value: object, *parts: object) -> object | None:
    current = value
    for part in parts:
        if isinstance(part, int):
            if not isinstance(current, list) or part >= len(current):
                return None
            current = current[part]
            continue
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def _required_text(value: object, name: str) -> str:
    normalized = _string_or_none(value)
    if normalized is None:
        raise PaymentProviderUnavailableError(f"Stripe response missing {name}.")
    return normalized


def _string_or_none(value: object) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _bool_or_none(value: object) -> bool | None:
    if isinstance(value, bool):
        return value
    return None


def _uuid_or_none(value: object) -> UUID | None:
    text = _string_or_none(value)
    if text is None:
        return None
    try:
        return UUID(text)
    except ValueError:
        return None


def _timestamp_to_datetime(value: object) -> datetime | None:
    if isinstance(value, datetime):
        return value.astimezone(UTC)
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=UTC)
    return None
