from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from civitas.application.billing.dto import ProviderCheckoutSessionDto, ProviderWebhookEventDto
from civitas.application.billing.use_cases import (
    CreateCheckoutSessionUseCase,
    ReconcilePaymentEventUseCase,
)
from civitas.domain.access.models import EntitlementGrant, PremiumProduct
from civitas.domain.billing.models import (
    BillingCheckoutSession,
    BillingSubscription,
    PaymentCustomer,
)

NOW = datetime(2026, 3, 9, 19, 0, tzinfo=timezone.utc)
USER_ID = UUID("1a8538b9-3099-4ee6-b14b-e8cb4a7af5ca")
CHECKOUT_ID = UUID("0f4b5984-a6b1-47dd-a98d-6a6ab866d506")
ENTITLEMENT_ID = UUID("4bfc8a77-7840-42fa-ad5f-60dafbdeafea")
SUBSCRIPTION_ID = UUID("c7cb0354-e6e5-4f74-a2a9-7bdc7f6f2f18")


class FakeBillingProviderGateway:
    provider_name = "stripe"

    def __init__(self) -> None:
        self.checkout_calls: list[dict[str, object]] = []

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
        self.checkout_calls.append(
            {
                "checkout_id": checkout_id,
                "product_code": product_code,
                "product_price_lookup_key": product_price_lookup_key,
                "user_id": user_id,
                "user_email": user_email,
                "success_url": success_url,
                "cancel_url": cancel_url,
                "existing_customer_id": existing_customer_id,
            }
        )
        return ProviderCheckoutSessionDto(
            provider_name="stripe",
            provider_checkout_session_id="cs_test_123",
            provider_customer_id="cus_test_123",
            provider_subscription_id="sub_test_123",
            checkout_url="https://checkout.stripe.test/session/cs_test_123",
            expires_at=NOW + timedelta(hours=1),
        )

    def create_billing_portal_session(
        self,
        *,
        provider_customer_id: str,
        return_url: str,
    ) -> str:
        return f"https://billing.stripe.test/{provider_customer_id}"

    def verify_and_parse_webhook_event(
        self,
        *,
        payload: bytes,
        signature_header: str | None,
        received_at: datetime,
    ) -> ProviderWebhookEventDto:
        raise AssertionError("not used in these tests")


class FakeProductRepository:
    def __init__(self, products: tuple[PremiumProduct, ...]) -> None:
        self._products = {product.code: product for product in products}

    def get_product_by_code(self, *, code: str) -> PremiumProduct | None:
        return self._products.get(code)

    def list_available_products(self) -> tuple[PremiumProduct, ...]:
        return tuple(self._products.values())

    def list_products_for_capability(
        self,
        *,
        capability_key: str,
    ) -> tuple[PremiumProduct, ...]:
        return tuple(
            product
            for product in self._products.values()
            if capability_key in product.capability_keys
        )


class FakeEntitlementRepository:
    def __init__(self, entitlements: tuple[EntitlementGrant, ...] = ()) -> None:
        self._entitlements = {entitlement.id: entitlement for entitlement in entitlements}

    def get_entitlement(self, *, entitlement_id: UUID) -> EntitlementGrant | None:
        return self._entitlements.get(entitlement_id)

    def list_user_entitlements(self, *, user_id: UUID) -> tuple[EntitlementGrant, ...]:
        return tuple(
            entitlement
            for entitlement in self._entitlements.values()
            if entitlement.user_id == user_id
        )

    def list_active_capability_keys(
        self,
        *,
        user_id: UUID,
        at: datetime,
    ) -> tuple[str, ...]:
        capability_keys: set[str] = set()
        for entitlement in self.list_user_entitlements(user_id=user_id):
            if (
                entitlement.effective_status(at=at) == "active"
                and entitlement.product_code == "premium_launch"
            ):
                capability_keys.update(
                    {
                        "premium_ai_analyst",
                        "premium_comparison",
                        "premium_neighbourhood",
                    }
                )
        return tuple(sorted(capability_keys))

    def apply_entitlement(self, entitlement: EntitlementGrant | None) -> None:
        if entitlement is None:
            return
        self._entitlements[entitlement.id] = entitlement


class FakeBillingStateRepository:
    def __init__(
        self,
        *,
        entitlement_repository: FakeEntitlementRepository,
        checkouts: tuple[BillingCheckoutSession, ...] = (),
        subscriptions: tuple[BillingSubscription, ...] = (),
        payment_customers: tuple[PaymentCustomer, ...] = (),
        apply_reconciliation_result: bool = True,
    ) -> None:
        self._entitlement_repository = entitlement_repository
        self._checkouts = {checkout.id: checkout for checkout in checkouts}
        self._subscriptions = {subscription.id: subscription for subscription in subscriptions}
        self._payment_customers = {
            (customer.provider_name, customer.user_id): customer for customer in payment_customers
        }
        self._subscriptions_by_provider = {
            (subscription.provider_name, subscription.provider_subscription_id): subscription
            for subscription in subscriptions
        }
        self._subscriptions_by_charge = {
            (subscription.provider_name, subscription.latest_charge_id): subscription
            for subscription in subscriptions
            if subscription.latest_charge_id is not None
        }
        self.created_checkouts: list[BillingCheckoutSession] = []
        self.applied_mutations = []
        self._apply_reconciliation_result = apply_reconciliation_result

    def get_checkout_session(self, *, checkout_id: UUID) -> BillingCheckoutSession | None:
        return self._checkouts.get(checkout_id)

    def get_open_checkout_session(
        self,
        *,
        user_id: UUID,
        product_code: str,
        at: datetime,
    ) -> BillingCheckoutSession | None:
        for checkout in self._checkouts.values():
            if (
                checkout.user_id == user_id
                and checkout.product_code == product_code
                and checkout.is_open_at(at=at)
            ):
                return checkout
        return None

    def create_pending_checkout_session(
        self,
        checkout_session: BillingCheckoutSession,
    ) -> BillingCheckoutSession:
        self._checkouts[checkout_session.id] = checkout_session
        self.created_checkouts.append(checkout_session)
        return checkout_session

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
    ) -> BillingCheckoutSession | None:
        checkout = self._checkouts.get(checkout_id)
        if checkout is None:
            return None
        updated = BillingCheckoutSession(
            id=checkout.id,
            user_id=checkout.user_id,
            product_code=checkout.product_code,
            provider_name=provider_name,
            provider_checkout_session_id=provider_checkout_session_id,
            provider_customer_id=provider_customer_id,
            provider_subscription_id=provider_subscription_id,
            status="open",
            checkout_url=checkout_url,
            success_path=checkout.success_path,
            cancel_path=checkout.cancel_path,
            requested_at=checkout.requested_at,
            expires_at=expires_at,
            completed_at=None,
            canceled_at=None,
            updated_at=updated_at,
        )
        self._checkouts[checkout_id] = updated
        return updated

    def mark_checkout_session_failed(
        self,
        *,
        checkout_id: UUID,
        updated_at: datetime,
    ) -> BillingCheckoutSession | None:
        checkout = self._checkouts.get(checkout_id)
        if checkout is None:
            return None
        updated = BillingCheckoutSession(
            id=checkout.id,
            user_id=checkout.user_id,
            product_code=checkout.product_code,
            provider_name=checkout.provider_name,
            provider_checkout_session_id=checkout.provider_checkout_session_id,
            provider_customer_id=checkout.provider_customer_id,
            provider_subscription_id=checkout.provider_subscription_id,
            status="failed",
            checkout_url=checkout.checkout_url,
            success_path=checkout.success_path,
            cancel_path=checkout.cancel_path,
            requested_at=checkout.requested_at,
            expires_at=checkout.expires_at,
            completed_at=checkout.completed_at,
            canceled_at=checkout.canceled_at,
            updated_at=updated_at,
        )
        self._checkouts[checkout_id] = updated
        return updated

    def get_payment_customer_by_user(
        self,
        *,
        user_id: UUID,
        provider_name: str,
    ) -> PaymentCustomer | None:
        return self._payment_customers.get((provider_name, user_id))

    def get_payment_customer_by_provider_customer_id(
        self,
        *,
        provider_name: str,
        provider_customer_id: str,
    ) -> PaymentCustomer | None:
        for customer in self._payment_customers.values():
            if (
                customer.provider_name == provider_name
                and customer.provider_customer_id == provider_customer_id
            ):
                return customer
        return None

    def get_subscription_by_provider_subscription_id(
        self,
        *,
        provider_name: str,
        provider_subscription_id: str,
    ) -> BillingSubscription | None:
        return self._subscriptions_by_provider.get((provider_name, provider_subscription_id))

    def get_subscription_by_latest_charge_id(
        self,
        *,
        provider_name: str,
        latest_charge_id: str,
    ) -> BillingSubscription | None:
        return self._subscriptions_by_charge.get((provider_name, latest_charge_id))

    def get_latest_subscription_by_provider_customer_id(
        self,
        *,
        provider_name: str,
        provider_customer_id: str,
        product_code: str | None = None,
    ) -> BillingSubscription | None:
        for subscription in self._subscriptions.values():
            if (
                subscription.provider_name == provider_name
                and subscription.provider_customer_id == provider_customer_id
                and (product_code is None or subscription.product_code == product_code)
            ):
                return subscription
        return None

    def get_checkout_session_by_provider_checkout_session_id(
        self,
        *,
        provider_name: str,
        provider_checkout_session_id: str,
    ) -> BillingCheckoutSession | None:
        for checkout in self._checkouts.values():
            if (
                checkout.provider_name == provider_name
                and checkout.provider_checkout_session_id == provider_checkout_session_id
            ):
                return checkout
        return None

    def apply_reconciliation(self, mutation) -> bool:
        self.applied_mutations.append(mutation)
        if not self._apply_reconciliation_result:
            return False
        if mutation.payment_customer is not None:
            self._payment_customers[
                (mutation.payment_customer.provider_name, mutation.payment_customer.user_id)
            ] = mutation.payment_customer
        if mutation.checkout_session is not None:
            self._checkouts[mutation.checkout_session.id] = mutation.checkout_session
        if mutation.subscription is not None:
            self._subscriptions[mutation.subscription.id] = mutation.subscription
            self._subscriptions_by_provider[
                (
                    mutation.subscription.provider_name,
                    mutation.subscription.provider_subscription_id,
                )
            ] = mutation.subscription
            if mutation.subscription.latest_charge_id is not None:
                self._subscriptions_by_charge[
                    (
                        mutation.subscription.provider_name,
                        mutation.subscription.latest_charge_id,
                    )
                ] = mutation.subscription
        self._entitlement_repository.apply_entitlement(mutation.entitlement)
        return True


def _product() -> PremiumProduct:
    return PremiumProduct(
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
        is_active=True,
        created_at=NOW - timedelta(days=10),
        updated_at=NOW - timedelta(days=1),
    )


def _entitlement(
    *,
    ends_at: datetime | None,
    status: str = "active",
    revoked_at: datetime | None = None,
    revoked_reason_code: str | None = None,
) -> EntitlementGrant:
    return EntitlementGrant(
        id=ENTITLEMENT_ID,
        user_id=USER_ID,
        product_code="premium_launch",
        status=status,
        starts_at=NOW - timedelta(days=1),
        ends_at=ends_at,
        revoked_at=revoked_at,
        revoked_reason_code=revoked_reason_code,
        created_at=NOW - timedelta(days=2),
        updated_at=NOW - timedelta(hours=2),
    )


def _checkout(
    *,
    status: str = "open",
) -> BillingCheckoutSession:
    return BillingCheckoutSession(
        id=CHECKOUT_ID,
        user_id=USER_ID,
        product_code="premium_launch",
        provider_name="stripe",
        provider_checkout_session_id="cs_test_123",
        provider_customer_id="cus_test_123",
        provider_subscription_id="sub_test_123",
        status=status,
        checkout_url="https://checkout.stripe.test/session/cs_test_123",
        success_path="/premium/success",
        cancel_path="/premium/cancel",
        requested_at=NOW - timedelta(minutes=5),
        expires_at=NOW + timedelta(minutes=55),
        completed_at=None,
        canceled_at=None,
        updated_at=NOW - timedelta(minutes=5),
    )


def _subscription(
    *,
    entitlement_id: UUID | None,
    latest_charge_id: str | None = "ch_test_123",
) -> BillingSubscription:
    return BillingSubscription(
        id=SUBSCRIPTION_ID,
        user_id=USER_ID,
        product_code="premium_launch",
        provider_name="stripe",
        provider_subscription_id="sub_test_123",
        provider_customer_id="cus_test_123",
        status="active",
        current_period_starts_at=NOW - timedelta(days=1),
        current_period_ends_at=NOW + timedelta(days=29),
        cancel_at_period_end=False,
        canceled_at=None,
        latest_checkout_session_id=CHECKOUT_ID,
        entitlement_id=entitlement_id,
        latest_invoice_id="in_test_123",
        latest_charge_id=latest_charge_id,
        created_at=NOW - timedelta(days=1),
        updated_at=NOW - timedelta(hours=1),
    )


def _invoice_paid_event() -> ProviderWebhookEventDto:
    return ProviderWebhookEventDto(
        provider_name="stripe",
        provider_event_id="evt_paid_123",
        event_type="invoice.paid",
        occurred_at=NOW,
        received_at=NOW,
        payload={"id": "evt_paid_123"},
        effect="invoice_paid",
        checkout_id=CHECKOUT_ID,
        user_id=USER_ID,
        product_code="premium_launch",
        provider_customer_id="cus_test_123",
        provider_checkout_session_id="cs_test_123",
        provider_subscription_id="sub_test_123",
        subscription_status="active",
        current_period_starts_at=NOW - timedelta(days=1),
        current_period_ends_at=NOW + timedelta(days=29),
        cancel_at_period_end=False,
        canceled_at=None,
        latest_invoice_id="in_test_123",
        latest_charge_id="ch_test_123",
        revoke_reason_code=None,
    )


def _refund_event() -> ProviderWebhookEventDto:
    return ProviderWebhookEventDto(
        provider_name="stripe",
        provider_event_id="evt_refund_123",
        event_type="charge.refunded",
        occurred_at=NOW,
        received_at=NOW,
        payload={"id": "evt_refund_123"},
        effect="charge_refunded",
        checkout_id=CHECKOUT_ID,
        user_id=None,
        product_code=None,
        provider_customer_id="cus_test_123",
        provider_checkout_session_id=None,
        provider_subscription_id="sub_test_123",
        subscription_status=None,
        current_period_starts_at=None,
        current_period_ends_at=None,
        cancel_at_period_end=None,
        canceled_at=None,
        latest_invoice_id=None,
        latest_charge_id="ch_test_123",
        revoke_reason_code="refund",
    )


def test_create_checkout_session_returns_already_covered_for_active_entitlement() -> None:
    entitlement_repository = FakeEntitlementRepository(
        (_entitlement(ends_at=NOW + timedelta(days=30)),)
    )
    gateway = FakeBillingProviderGateway()
    use_case = CreateCheckoutSessionUseCase(
        billing_provider_gateway=gateway,
        billing_state_repository=FakeBillingStateRepository(
            entitlement_repository=entitlement_repository
        ),
        entitlement_repository=entitlement_repository,
        product_repository=FakeProductRepository((_product(),)),
        clock=lambda: NOW,
    )

    result = use_case.execute(
        user_id=USER_ID,
        user_email="person@example.com",
        product_code="premium_launch",
        success_path="/premium/success",
        cancel_path="/premium/cancel",
        public_origin="https://app.civitas.test",
    )

    assert result.status == "already_covered"
    assert result.checkout_id is None
    assert result.account_access_state == "premium"
    assert gateway.checkout_calls == []


def test_create_checkout_session_reuses_existing_open_checkout() -> None:
    entitlement_repository = FakeEntitlementRepository()
    existing_checkout = _checkout()
    gateway = FakeBillingProviderGateway()
    use_case = CreateCheckoutSessionUseCase(
        billing_provider_gateway=gateway,
        billing_state_repository=FakeBillingStateRepository(
            entitlement_repository=entitlement_repository,
            checkouts=(existing_checkout,),
        ),
        entitlement_repository=entitlement_repository,
        product_repository=FakeProductRepository((_product(),)),
        clock=lambda: NOW,
    )

    result = use_case.execute(
        user_id=USER_ID,
        user_email="person@example.com",
        product_code="premium_launch",
        success_path="/premium/success",
        cancel_path="/premium/cancel",
        public_origin="https://app.civitas.test",
    )

    assert result.status == "open"
    assert result.checkout_id == existing_checkout.id
    assert result.redirect_url == existing_checkout.checkout_url
    assert gateway.checkout_calls == []


def test_reconcile_payment_event_activates_access_on_invoice_paid() -> None:
    entitlement_repository = FakeEntitlementRepository()
    billing_state_repository = FakeBillingStateRepository(
        entitlement_repository=entitlement_repository,
        checkouts=(_checkout(status="open"),),
    )
    use_case = ReconcilePaymentEventUseCase(
        billing_state_repository=billing_state_repository,
        entitlement_repository=entitlement_repository,
        clock=lambda: NOW,
    )

    result = use_case.execute(provider_event=_invoice_paid_event())

    assert result.reconciliation_status == "applied"
    assert result.checkout_id == CHECKOUT_ID
    assert result.account_access_state == "premium"
    mutation = billing_state_repository.applied_mutations[0]
    assert mutation.subscription is not None
    assert mutation.subscription.provider_subscription_id == "sub_test_123"
    assert mutation.entitlement is not None
    assert mutation.entitlement.status == "active"
    assert mutation.entitlement.ends_at == NOW + timedelta(days=29)


def test_reconcile_payment_event_revokes_access_on_refund() -> None:
    entitlement_repository = FakeEntitlementRepository(
        (_entitlement(ends_at=NOW + timedelta(days=29)),)
    )
    billing_state_repository = FakeBillingStateRepository(
        entitlement_repository=entitlement_repository,
        checkouts=(_checkout(status="completed"),),
        subscriptions=(_subscription(entitlement_id=ENTITLEMENT_ID),),
    )
    use_case = ReconcilePaymentEventUseCase(
        billing_state_repository=billing_state_repository,
        entitlement_repository=entitlement_repository,
        clock=lambda: NOW,
    )

    result = use_case.execute(provider_event=_refund_event())

    assert result.reconciliation_status == "applied"
    assert result.account_access_state == "free"
    mutation = billing_state_repository.applied_mutations[0]
    assert mutation.entitlement is not None
    assert mutation.entitlement.status == "revoked"
    assert mutation.entitlement.revoked_reason_code == "refund"
