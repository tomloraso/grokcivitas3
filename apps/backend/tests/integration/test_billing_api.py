from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi.testclient import TestClient

from civitas.api.dependencies import (
    get_billing_provider_gateway,
    get_create_billing_portal_session_use_case,
    get_create_checkout_session_use_case,
    get_current_session_use_case,
    get_list_available_premium_products_use_case,
    get_reconcile_payment_event_use_case,
)
from civitas.api.main import app
from civitas.application.access.dto import PremiumProductDto
from civitas.application.billing.dto import (
    CreateBillingPortalSessionResultDto,
    CreateCheckoutSessionResultDto,
    ReconcilePaymentEventResultDto,
)
from civitas.application.identity.dto import CurrentSessionDto, SessionUserDto

client = TestClient(app)


class FakeListAvailablePremiumProductsUseCase:
    def execute(self) -> tuple[PremiumProductDto, ...]:
        return (
            PremiumProductDto(
                code="premium_launch",
                display_name="Premium",
                description="Launch bundle",
                billing_interval="monthly",
                duration_days=None,
                provider_price_lookup_key="premium_launch",
                capability_keys=(
                    "premium_ai_analyst",
                    "premium_comparison",
                    "premium_neighbourhood",
                ),
            ),
        )


class FakeCreateCheckoutSessionUseCase:
    def execute(
        self,
        *,
        user_id: UUID,
        user_email: str,
        product_code: str,
        success_path: str,
        cancel_path: str,
        public_origin: str,
    ) -> CreateCheckoutSessionResultDto:
        return CreateCheckoutSessionResultDto(
            checkout_id=UUID("0f4b5984-a6b1-47dd-a98d-6a6ab866d506"),
            product_code=product_code,
            status="open",
            redirect_url="https://checkout.stripe.test/session/cs_test_123",
            expires_at=datetime(2026, 3, 9, 20, 0, tzinfo=timezone.utc),
            account_access_state="free",
        )


class FakeCreateBillingPortalSessionUseCase:
    def execute(
        self,
        *,
        user_id: UUID,
        return_path: str | None,
        public_origin: str,
    ) -> CreateBillingPortalSessionResultDto:
        return CreateBillingPortalSessionResultDto(
            redirect_url="https://billing.stripe.test/session/bps_123"
        )


class FakeBillingProviderGateway:
    provider_name = "stripe"

    def verify_and_parse_webhook_event(
        self,
        *,
        payload: bytes,
        signature_header: str | None,
        received_at: datetime,
    ):
        return type(
            "ProviderWebhookEventDtoLike",
            (),
            {
                "provider_name": "stripe",
                "provider_event_id": "evt_paid_123",
                "event_type": "invoice.paid",
                "occurred_at": received_at,
                "received_at": received_at,
                "payload": {"id": "evt_paid_123"},
                "effect": "invoice_paid",
                "checkout_id": UUID("0f4b5984-a6b1-47dd-a98d-6a6ab866d506"),
                "user_id": UUID("1a8538b9-3099-4ee6-b14b-e8cb4a7af5ca"),
                "product_code": "premium_launch",
                "provider_customer_id": "cus_test_123",
                "provider_checkout_session_id": "cs_test_123",
                "provider_subscription_id": "sub_test_123",
                "subscription_status": "active",
                "current_period_starts_at": received_at,
                "current_period_ends_at": received_at,
                "cancel_at_period_end": False,
                "canceled_at": None,
                "latest_invoice_id": "in_test_123",
                "latest_charge_id": "ch_test_123",
                "revoke_reason_code": None,
            },
        )()


class FakeReconcilePaymentEventUseCase:
    def execute(self, *, provider_event) -> ReconcilePaymentEventResultDto:
        return ReconcilePaymentEventResultDto(
            provider_event_id=provider_event.provider_event_id,
            reconciliation_status="applied",
            checkout_id=provider_event.checkout_id,
            entitlement_id=UUID("4bfc8a77-7840-42fa-ad5f-60dafbdeafea"),
            account_access_state="premium",
        )


class FakeAuthenticatedSessionUseCase:
    def execute(self, *, session_token: str | None) -> CurrentSessionDto:
        return CurrentSessionDto.authenticated(
            user=SessionUserDto(
                id=UUID("1a8538b9-3099-4ee6-b14b-e8cb4a7af5ca"),
                email="person@example.com",
            ),
            expires_at=datetime(2026, 3, 20, 10, 0, tzinfo=timezone.utc),
        )


class FakeAnonymousSessionUseCase:
    def execute(self, *, session_token: str | None) -> CurrentSessionDto:
        return CurrentSessionDto.anonymous(reason="missing")


def setup_function() -> None:
    app.dependency_overrides.clear()
    client.cookies.clear()


def teardown_function() -> None:
    app.dependency_overrides.clear()
    client.cookies.clear()


def test_list_billing_products_returns_catalog_contract() -> None:
    app.dependency_overrides[get_list_available_premium_products_use_case] = lambda: (
        FakeListAvailablePremiumProductsUseCase()
    )

    response = client.get("/api/v1/billing/products")

    assert response.status_code == 200
    assert response.json() == {
        "products": [
            {
                "code": "premium_launch",
                "display_name": "Premium",
                "description": "Launch bundle",
                "billing_interval": "monthly",
                "duration_days": None,
                "capability_keys": [
                    "premium_ai_analyst",
                    "premium_comparison",
                    "premium_neighbourhood",
                ],
            }
        ]
    }


def test_create_checkout_session_requires_authenticated_session() -> None:
    app.dependency_overrides[get_current_session_use_case] = lambda: FakeAnonymousSessionUseCase()

    response = client.post(
        "/api/v1/billing/checkout-sessions",
        json={"product_code": "premium_launch"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "authentication required"}


def test_create_checkout_session_returns_redirect_payload() -> None:
    app.dependency_overrides[get_current_session_use_case] = lambda: (
        FakeAuthenticatedSessionUseCase()
    )
    app.dependency_overrides[get_create_checkout_session_use_case] = lambda: (
        FakeCreateCheckoutSessionUseCase()
    )

    response = client.post(
        "/api/v1/billing/checkout-sessions",
        headers={"origin": "http://testserver"},
        cookies={"civitas_session": "session-token"},
        json={
            "product_code": "premium_launch",
            "success_path": "/premium/success",
            "cancel_path": "/premium/cancel",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "open"
    assert response.json()["checkout_id"] == "0f4b5984-a6b1-47dd-a98d-6a6ab866d506"


def test_create_billing_portal_session_returns_redirect_url() -> None:
    app.dependency_overrides[get_current_session_use_case] = lambda: (
        FakeAuthenticatedSessionUseCase()
    )
    app.dependency_overrides[get_create_billing_portal_session_use_case] = lambda: (
        FakeCreateBillingPortalSessionUseCase()
    )

    response = client.post(
        "/api/v1/billing/portal-sessions",
        headers={"origin": "http://testserver"},
        cookies={"civitas_session": "session-token"},
        json={"return_path": "/account"},
    )

    assert response.status_code == 200
    assert response.json() == {"redirect_url": "https://billing.stripe.test/session/bps_123"}


def test_stripe_webhook_returns_reconciliation_payload() -> None:
    app.dependency_overrides[get_billing_provider_gateway] = lambda: FakeBillingProviderGateway()
    app.dependency_overrides[get_reconcile_payment_event_use_case] = lambda: (
        FakeReconcilePaymentEventUseCase()
    )

    response = client.post(
        "/api/v1/billing/webhooks/stripe",
        headers={"stripe-signature": "t=1,v1=test"},
        content=b"{}",
    )

    assert response.status_code == 200
    assert response.json() == {
        "provider_event_id": "evt_paid_123",
        "reconciliation_status": "applied",
        "checkout_id": "0f4b5984-a6b1-47dd-a98d-6a6ab866d506",
        "entitlement_id": "4bfc8a77-7840-42fa-ad5f-60dafbdeafea",
        "account_access_state": "premium",
    }
