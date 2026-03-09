from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from uuid import UUID

import stripe

from civitas.infrastructure.payments.stripe_billing_provider_gateway import (
    StripeBillingProviderGateway,
)

NOW = datetime(2026, 3, 9, 19, 30, tzinfo=timezone.utc)
SECRET = "whsec_test_secret"


class FakeStripeObject:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = payload

    def to_dict_recursive(self) -> dict[str, object]:
        return self._payload


class FakePricesApi:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def list(self, params: dict[str, object]) -> object:
        self.calls.append(params)
        return type(
            "FakePriceList",
            (),
            {
                "data": [
                    FakeStripeObject(
                        {
                            "id": "price_test_123",
                            "lookup_key": "premium_launch",
                            "recurring": {"interval": "month"},
                        }
                    )
                ]
            },
        )()


class FakeCheckoutSessionsApi:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def create(self, params: dict[str, object]) -> FakeStripeObject:
        self.calls.append(params)
        return FakeStripeObject(
            {
                "id": "cs_test_123",
                "customer": "cus_test_123",
                "subscription": "sub_test_123",
                "url": "https://checkout.stripe.test/session/cs_test_123",
                "expires_at": int((NOW.timestamp() + 3600)),
            }
        )


class FakeBillingPortalSessionsApi:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def create(self, params: dict[str, object]) -> FakeStripeObject:
        self.calls.append(params)
        return FakeStripeObject({"url": "https://billing.stripe.test/session/bps_123"})


class FakeStripeClient:
    def __init__(self) -> None:
        self.v1 = type(
            "FakeStripeV1",
            (),
            {
                "prices": FakePricesApi(),
                "checkout": type(
                    "FakeCheckoutNamespace",
                    (),
                    {"sessions": FakeCheckoutSessionsApi()},
                )(),
                "billing_portal": type(
                    "FakeBillingPortalNamespace",
                    (),
                    {"sessions": FakeBillingPortalSessionsApi()},
                )(),
            },
        )()


def test_create_checkout_session_uses_subscription_metadata_and_lookup_key() -> None:
    client = FakeStripeClient()
    gateway = StripeBillingProviderGateway(
        secret_key="sk_test_123",
        webhook_secret=SECRET,
        client=client,
    )

    result = gateway.create_checkout_session(
        checkout_id=UUID("0f4b5984-a6b1-47dd-a98d-6a6ab866d506"),
        product_code="premium_launch",
        product_price_lookup_key="premium_launch",
        user_id=UUID("1a8538b9-3099-4ee6-b14b-e8cb4a7af5ca"),
        user_email="person@example.com",
        success_url="https://app.civitas.test/premium/success",
        cancel_url="https://app.civitas.test/premium/cancel",
        existing_customer_id=None,
    )

    assert result.provider_checkout_session_id == "cs_test_123"
    assert result.provider_customer_id == "cus_test_123"
    assert result.provider_subscription_id == "sub_test_123"
    price_call = client.v1.prices.calls[0]
    assert price_call["lookup_keys"] == ["premium_launch"]
    checkout_call = client.v1.checkout.sessions.calls[0]
    assert checkout_call["mode"] == "subscription"
    assert checkout_call["line_items"] == [{"price": "price_test_123", "quantity": 1}]
    assert checkout_call["metadata"]["product_code"] == "premium_launch"
    assert checkout_call["subscription_data"]["metadata"]["product_code"] == "premium_launch"
    assert checkout_call["customer_email"] == "person@example.com"


def test_verify_and_parse_webhook_event_maps_invoice_paid_metadata_and_periods() -> None:
    gateway = StripeBillingProviderGateway(
        secret_key="sk_test_123",
        webhook_secret=SECRET,
        client=FakeStripeClient(),
    )
    payload = {
        "id": "evt_paid_123",
        "type": "invoice.paid",
        "created": int(NOW.timestamp()),
        "data": {
            "object": {
                "id": "in_test_123",
                "customer": "cus_test_123",
                "subscription": "sub_test_123",
                "charge": "ch_test_123",
                "lines": {
                    "data": [
                        {
                            "period": {
                                "start": int((NOW.timestamp() - 86400)),
                                "end": int((NOW.timestamp() + 29 * 86400)),
                            }
                        }
                    ]
                },
                "subscription_details": {
                    "metadata": {
                        "checkout_id": "0f4b5984-a6b1-47dd-a98d-6a6ab866d506",
                        "user_id": "1a8538b9-3099-4ee6-b14b-e8cb4a7af5ca",
                        "product_code": "premium_launch",
                    }
                },
            }
        },
    }
    encoded_payload = json.dumps(payload, separators=(",", ":"))
    timestamp = int(time.time())
    signature = stripe.WebhookSignature._compute_signature(f"{timestamp}.{encoded_payload}", SECRET)
    header = f"t={timestamp},v1={signature}"

    result = gateway.verify_and_parse_webhook_event(
        payload=encoded_payload.encode("utf-8"),
        signature_header=header,
        received_at=NOW,
    )

    assert result.effect == "invoice_paid"
    assert result.provider_event_id == "evt_paid_123"
    assert result.checkout_id == UUID("0f4b5984-a6b1-47dd-a98d-6a6ab866d506")
    assert result.user_id == UUID("1a8538b9-3099-4ee6-b14b-e8cb4a7af5ca")
    assert result.product_code == "premium_launch"
    assert result.provider_subscription_id == "sub_test_123"
    assert result.latest_invoice_id == "in_test_123"
    assert result.latest_charge_id == "ch_test_123"
    assert result.current_period_starts_at == datetime.fromtimestamp(
        int(NOW.timestamp() - 86400),
        tz=timezone.utc,
    )
    assert result.current_period_ends_at == datetime.fromtimestamp(
        int(NOW.timestamp() + 29 * 86400),
        tz=timezone.utc,
    )
