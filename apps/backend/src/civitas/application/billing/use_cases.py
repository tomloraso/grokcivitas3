from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from uuid import UUID, uuid4

from civitas.application.access.dto import AccountAccessState
from civitas.application.access.ports.entitlement_repository import EntitlementRepository
from civitas.application.access.ports.product_repository import ProductRepository
from civitas.application.billing.dto import (
    BillingReconciliationMutation,
    CheckoutStatusDto,
    CreateBillingPortalSessionResultDto,
    CreateCheckoutSessionResultDto,
    ProviderWebhookEventDto,
    ReconcilePaymentEventResultDto,
)
from civitas.application.billing.errors import (
    BillingCustomerNotFoundError,
    BillingProductNotConfiguredError,
    BillingProductNotFoundError,
    CheckoutSessionNotFoundError,
    PaymentProviderUnavailableError,
)
from civitas.application.billing.ports.billing_provider_gateway import BillingProviderGateway
from civitas.application.billing.ports.billing_state_repository import BillingStateRepository
from civitas.application.shared.utils.safe_redirects import normalize_return_to
from civitas.domain.access.models import EntitlementEvent, EntitlementGrant, PremiumProduct
from civitas.domain.access.value_objects import PersistedEntitlementStatus
from civitas.domain.billing.models import (
    BillingCheckoutSession,
    BillingSubscription,
    PaymentCustomer,
    PaymentEvent,
)
from civitas.domain.billing.services import (
    checkout_status_to_progress_status,
    product_is_already_covered,
)
from civitas.domain.billing.value_objects import (
    BillingSubscriptionStatus,
    PaymentEventReconciliationStatus,
    PaymentProviderName,
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


Clock = Callable[[], datetime]


class CreateCheckoutSessionUseCase:
    def __init__(
        self,
        *,
        billing_provider_gateway: BillingProviderGateway,
        billing_state_repository: BillingStateRepository,
        entitlement_repository: EntitlementRepository,
        product_repository: ProductRepository,
        clock: Clock = _utc_now,
    ) -> None:
        self._billing_provider_gateway = billing_provider_gateway
        self._billing_state_repository = billing_state_repository
        self._entitlement_repository = entitlement_repository
        self._product_repository = product_repository
        self._clock = clock

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
        now = self._clock()
        product = _load_billable_product(self._product_repository, product_code=product_code)
        account_access_state, active_capability_keys = _current_account_access_state(
            entitlement_repository=self._entitlement_repository,
            user_id=user_id,
            at=now,
        )
        if product_is_already_covered(
            required_capability_keys=product.capability_keys,
            active_capability_keys=active_capability_keys,
        ):
            return CreateCheckoutSessionResultDto(
                checkout_id=None,
                product_code=product.code,
                status="already_covered",
                redirect_url=None,
                expires_at=None,
                account_access_state=account_access_state,
            )

        existing_checkout = self._billing_state_repository.get_open_checkout_session(
            user_id=user_id,
            product_code=product.code,
            at=now,
        )
        if existing_checkout is not None and existing_checkout.checkout_url is not None:
            return CreateCheckoutSessionResultDto(
                checkout_id=existing_checkout.id,
                product_code=existing_checkout.product_code,
                status="open",
                redirect_url=existing_checkout.checkout_url,
                expires_at=existing_checkout.expires_at,
                account_access_state=account_access_state,
            )

        normalized_success_path = normalize_return_to(success_path)
        normalized_cancel_path = normalize_return_to(cancel_path)
        checkout = BillingCheckoutSession(
            id=uuid4(),
            user_id=user_id,
            product_code=product.code,
            provider_name=self._billing_provider_gateway.provider_name,
            provider_checkout_session_id=None,
            provider_customer_id=None,
            provider_subscription_id=None,
            status="pending_provider",
            checkout_url=None,
            success_path=normalized_success_path,
            cancel_path=normalized_cancel_path,
            requested_at=now,
            expires_at=None,
            completed_at=None,
            canceled_at=None,
            updated_at=now,
        )
        self._billing_state_repository.create_pending_checkout_session(checkout)

        payment_customer = self._billing_state_repository.get_payment_customer_by_user(
            user_id=user_id,
            provider_name=self._billing_provider_gateway.provider_name,
        )
        try:
            provider_checkout = self._billing_provider_gateway.create_checkout_session(
                checkout_id=checkout.id,
                product_code=product.code,
                product_price_lookup_key=_require_price_lookup_key(product),
                user_id=user_id,
                user_email=user_email,
                success_url=_absolute_public_url(
                    public_origin,
                    normalized_success_path,
                    checkout_id=str(checkout.id),
                    provider_session_id="{CHECKOUT_SESSION_ID}",
                ),
                cancel_url=_absolute_public_url(
                    public_origin,
                    normalized_cancel_path,
                    checkout_id=str(checkout.id),
                ),
                existing_customer_id=(
                    payment_customer.provider_customer_id if payment_customer is not None else None
                ),
            )
        except PaymentProviderUnavailableError:
            self._billing_state_repository.mark_checkout_session_failed(
                checkout_id=checkout.id,
                updated_at=self._clock(),
            )
            raise

        persisted_checkout = self._billing_state_repository.mark_checkout_session_open(
            checkout_id=checkout.id,
            provider_name=provider_checkout.provider_name,
            provider_checkout_session_id=provider_checkout.provider_checkout_session_id,
            provider_customer_id=provider_checkout.provider_customer_id,
            provider_subscription_id=provider_checkout.provider_subscription_id,
            checkout_url=provider_checkout.checkout_url,
            expires_at=provider_checkout.expires_at,
            updated_at=self._clock(),
        )
        resolved_checkout = persisted_checkout or checkout
        return CreateCheckoutSessionResultDto(
            checkout_id=resolved_checkout.id,
            product_code=resolved_checkout.product_code,
            status="open",
            redirect_url=provider_checkout.checkout_url,
            expires_at=provider_checkout.expires_at,
            account_access_state=account_access_state,
        )


class GetCheckoutStatusUseCase:
    def __init__(
        self,
        *,
        billing_state_repository: BillingStateRepository,
        entitlement_repository: EntitlementRepository,
        product_repository: ProductRepository,
        clock: Clock = _utc_now,
    ) -> None:
        self._billing_state_repository = billing_state_repository
        self._entitlement_repository = entitlement_repository
        self._product_repository = product_repository
        self._clock = clock

    def execute(
        self,
        *,
        user_id: UUID,
        checkout_id: UUID,
    ) -> CheckoutStatusDto:
        now = self._clock()
        checkout = self._billing_state_repository.get_checkout_session(checkout_id=checkout_id)
        if checkout is None or checkout.user_id != user_id:
            raise CheckoutSessionNotFoundError(str(checkout_id))

        account_access_state, active_capability_keys = _current_account_access_state(
            entitlement_repository=self._entitlement_repository,
            user_id=user_id,
            at=now,
        )
        status = checkout_status_to_progress_status(
            checkout_status=checkout.status,
            expires_at=checkout.expires_at,
            at=now,
        )
        product = self._product_repository.get_product_by_code(code=checkout.product_code)
        if (
            status == "processing_payment"
            and product is not None
            and product_is_already_covered(
                required_capability_keys=product.capability_keys,
                active_capability_keys=active_capability_keys,
            )
        ):
            status = "completed"

        return CheckoutStatusDto(
            checkout_id=checkout.id,
            product_code=checkout.product_code,
            status=status,
            redirect_url=checkout.checkout_url,
            expires_at=checkout.expires_at,
            account_access_state=account_access_state,
        )


class CreateBillingPortalSessionUseCase:
    def __init__(
        self,
        *,
        billing_provider_gateway: BillingProviderGateway,
        billing_state_repository: BillingStateRepository,
    ) -> None:
        self._billing_provider_gateway = billing_provider_gateway
        self._billing_state_repository = billing_state_repository

    def execute(
        self,
        *,
        user_id: UUID,
        return_path: str | None,
        public_origin: str,
    ) -> CreateBillingPortalSessionResultDto:
        payment_customer = self._billing_state_repository.get_payment_customer_by_user(
            user_id=user_id,
            provider_name=self._billing_provider_gateway.provider_name,
        )
        if payment_customer is None:
            raise BillingCustomerNotFoundError()

        redirect_url = self._billing_provider_gateway.create_billing_portal_session(
            provider_customer_id=payment_customer.provider_customer_id,
            return_url=_absolute_public_url(public_origin, normalize_return_to(return_path)),
        )
        return CreateBillingPortalSessionResultDto(redirect_url=redirect_url)


class ReconcilePaymentEventUseCase:
    def __init__(
        self,
        *,
        billing_state_repository: BillingStateRepository,
        entitlement_repository: EntitlementRepository,
        clock: Clock = _utc_now,
    ) -> None:
        self._billing_state_repository = billing_state_repository
        self._entitlement_repository = entitlement_repository
        self._clock = clock

    def execute(
        self,
        *,
        provider_event: ProviderWebhookEventDto,
    ) -> ReconcilePaymentEventResultDto:
        now = self._clock()
        checkout = _resolve_checkout(
            billing_state_repository=self._billing_state_repository,
            provider_event=provider_event,
        )
        subscription = _resolve_subscription(
            billing_state_repository=self._billing_state_repository,
            provider_event=provider_event,
            checkout=checkout,
        )
        user_id = (
            provider_event.user_id
            or (checkout.user_id if checkout is not None else None)
            or (subscription.user_id if subscription is not None else None)
        )
        product_code = (
            provider_event.product_code
            or (checkout.product_code if checkout is not None else None)
            or (subscription.product_code if subscription is not None else None)
        )

        payment_customer = _build_payment_customer(
            billing_state_repository=self._billing_state_repository,
            provider_event=provider_event,
            user_id=user_id,
        )
        mutation = _build_reconciliation_mutation(
            entitlement_repository=self._entitlement_repository,
            provider_event=provider_event,
            checkout=checkout,
            subscription=subscription,
            payment_customer=payment_customer,
            user_id=user_id,
            product_code=product_code,
            reconciled_at=now,
        )
        applied = self._billing_state_repository.apply_reconciliation(mutation)
        if not applied:
            return ReconcilePaymentEventResultDto(
                provider_event_id=provider_event.provider_event_id,
                reconciliation_status="duplicate",
                checkout_id=mutation.checkout_session.id if mutation.checkout_session else None,
                entitlement_id=mutation.entitlement.id if mutation.entitlement else None,
                account_access_state=(
                    _account_access_state(
                        entitlement_repository=self._entitlement_repository,
                        user_id=user_id,
                        at=now,
                    )
                    if user_id is not None
                    else None
                ),
            )

        reconciliation_status = mutation.payment_event.reconciliation_status
        if reconciliation_status == "pending":
            raise AssertionError("Reconciled payment events must not remain pending.")
        return ReconcilePaymentEventResultDto(
            provider_event_id=provider_event.provider_event_id,
            reconciliation_status=reconciliation_status,
            checkout_id=mutation.checkout_session.id if mutation.checkout_session else None,
            entitlement_id=mutation.entitlement.id if mutation.entitlement else None,
            account_access_state=(
                _account_access_state(
                    entitlement_repository=self._entitlement_repository,
                    user_id=user_id,
                    at=now,
                )
                if user_id is not None
                else None
            ),
        )


def _load_billable_product(
    product_repository: ProductRepository,
    *,
    product_code: str,
) -> PremiumProduct:
    product = product_repository.get_product_by_code(code=product_code)
    if product is None or not product.is_active:
        raise BillingProductNotFoundError(product_code)
    return product


def _require_price_lookup_key(product: PremiumProduct) -> str:
    if product.provider_price_lookup_key is None:
        raise BillingProductNotConfiguredError(product.code)
    return product.provider_price_lookup_key


def _current_account_access_state(
    *,
    entitlement_repository: EntitlementRepository,
    user_id: UUID,
    at: datetime,
) -> tuple[AccountAccessState, tuple[str, ...]]:
    entitlements = entitlement_repository.list_user_entitlements(user_id=user_id)
    active_capability_keys = entitlement_repository.list_active_capability_keys(
        user_id=user_id,
        at=at,
    )
    if active_capability_keys:
        return "premium", active_capability_keys
    if any(entitlement.effective_status(at=at) == "pending" for entitlement in entitlements):
        return "pending", active_capability_keys
    return "free", active_capability_keys


def _account_access_state(
    *,
    entitlement_repository: EntitlementRepository,
    user_id: UUID,
    at: datetime,
) -> AccountAccessState:
    state, _ = _current_account_access_state(
        entitlement_repository=entitlement_repository,
        user_id=user_id,
        at=at,
    )
    return state


def _build_reconciliation_mutation(
    *,
    entitlement_repository: EntitlementRepository,
    provider_event: ProviderWebhookEventDto,
    checkout: BillingCheckoutSession | None,
    subscription: BillingSubscription | None,
    payment_customer: PaymentCustomer | None,
    user_id: UUID | None,
    product_code: str | None,
    reconciled_at: datetime,
) -> BillingReconciliationMutation:
    if provider_event.effect == "ignored":
        return BillingReconciliationMutation(
            payment_event=_payment_event(
                provider_event=provider_event,
                reconciliation_status="ignored",
                reconciled_at=reconciled_at,
                checkout_id=checkout.id if checkout is not None else None,
                user_id=user_id,
                product_code=product_code,
            ),
            payment_customer=payment_customer,
            checkout_session=checkout,
            subscription=subscription,
            entitlement=None,
            entitlement_event=None,
        )

    if user_id is None or product_code is None:
        return BillingReconciliationMutation(
            payment_event=_payment_event(
                provider_event=provider_event,
                reconciliation_status="failed",
                reconciled_at=reconciled_at,
                checkout_id=checkout.id if checkout is not None else None,
                user_id=user_id,
                product_code=product_code,
            ),
            payment_customer=payment_customer,
            checkout_session=checkout,
            subscription=subscription,
            entitlement=None,
            entitlement_event=None,
        )

    entitlement = _resolve_entitlement(
        entitlement_repository=entitlement_repository,
        subscription=subscription,
        user_id=user_id,
        product_code=product_code,
    )
    updated_checkout = _build_checkout_session(
        provider_event=provider_event,
        checkout=checkout,
        user_id=user_id,
        product_code=product_code,
        provider_name=provider_event.provider_name,
    )
    updated_subscription = _build_subscription(
        provider_event=provider_event,
        subscription=subscription,
        checkout=updated_checkout,
        user_id=user_id,
        product_code=product_code,
        entitlement=entitlement,
    )
    updated_entitlement, entitlement_event = _build_entitlement_updates(
        provider_event=provider_event,
        entitlement=entitlement,
        subscription=updated_subscription,
        user_id=user_id,
        product_code=product_code,
        reconciled_at=reconciled_at,
    )
    final_subscription = updated_subscription
    if final_subscription is not None and updated_entitlement is not None:
        final_subscription = BillingSubscription(
            id=final_subscription.id,
            user_id=final_subscription.user_id,
            product_code=final_subscription.product_code,
            provider_name=final_subscription.provider_name,
            provider_subscription_id=final_subscription.provider_subscription_id,
            provider_customer_id=final_subscription.provider_customer_id,
            status=final_subscription.status,
            current_period_starts_at=final_subscription.current_period_starts_at,
            current_period_ends_at=final_subscription.current_period_ends_at,
            cancel_at_period_end=final_subscription.cancel_at_period_end,
            canceled_at=final_subscription.canceled_at,
            latest_checkout_session_id=final_subscription.latest_checkout_session_id,
            entitlement_id=updated_entitlement.id,
            latest_invoice_id=final_subscription.latest_invoice_id,
            latest_charge_id=final_subscription.latest_charge_id,
            created_at=final_subscription.created_at,
            updated_at=final_subscription.updated_at,
        )

    status: PaymentEventReconciliationStatus = (
        "applied" if entitlement_event is not None or final_subscription is not None else "ignored"
    )
    return BillingReconciliationMutation(
        payment_event=_payment_event(
            provider_event=provider_event,
            reconciliation_status=status,
            reconciled_at=reconciled_at,
            checkout_id=updated_checkout.id if updated_checkout is not None else None,
            user_id=user_id,
            product_code=product_code,
        ),
        payment_customer=payment_customer,
        checkout_session=updated_checkout,
        subscription=final_subscription,
        entitlement=updated_entitlement,
        entitlement_event=entitlement_event,
    )


def _resolve_checkout(
    *,
    billing_state_repository: BillingStateRepository,
    provider_event: ProviderWebhookEventDto,
) -> BillingCheckoutSession | None:
    if provider_event.checkout_id is not None:
        checkout = billing_state_repository.get_checkout_session(
            checkout_id=provider_event.checkout_id
        )
        if checkout is not None:
            return checkout
    if provider_event.provider_checkout_session_id is None:
        return None
    return billing_state_repository.get_checkout_session_by_provider_checkout_session_id(
        provider_name=provider_event.provider_name,
        provider_checkout_session_id=provider_event.provider_checkout_session_id,
    )


def _resolve_subscription(
    *,
    billing_state_repository: BillingStateRepository,
    provider_event: ProviderWebhookEventDto,
    checkout: BillingCheckoutSession | None,
) -> BillingSubscription | None:
    provider_subscription_id = provider_event.provider_subscription_id or (
        checkout.provider_subscription_id if checkout is not None else None
    )
    if provider_subscription_id is not None:
        subscription = billing_state_repository.get_subscription_by_provider_subscription_id(
            provider_name=provider_event.provider_name,
            provider_subscription_id=provider_subscription_id,
        )
        if subscription is not None:
            return subscription
    if provider_event.latest_charge_id is not None:
        subscription = billing_state_repository.get_subscription_by_latest_charge_id(
            provider_name=provider_event.provider_name,
            latest_charge_id=provider_event.latest_charge_id,
        )
        if subscription is not None:
            return subscription
    if provider_event.provider_customer_id is None:
        return None
    return billing_state_repository.get_latest_subscription_by_provider_customer_id(
        provider_name=provider_event.provider_name,
        provider_customer_id=provider_event.provider_customer_id,
        product_code=provider_event.product_code,
    )


def _build_payment_customer(
    *,
    billing_state_repository: BillingStateRepository,
    provider_event: ProviderWebhookEventDto,
    user_id: UUID | None,
) -> PaymentCustomer | None:
    if user_id is None or provider_event.provider_customer_id is None:
        return None

    existing = billing_state_repository.get_payment_customer_by_provider_customer_id(
        provider_name=provider_event.provider_name,
        provider_customer_id=provider_event.provider_customer_id,
    )
    if existing is not None:
        return existing

    return PaymentCustomer(
        user_id=user_id,
        provider_name=provider_event.provider_name,
        provider_customer_id=provider_event.provider_customer_id,
        created_at=provider_event.received_at,
        updated_at=provider_event.received_at,
    )


def _resolve_entitlement(
    *,
    entitlement_repository: EntitlementRepository,
    subscription: BillingSubscription | None,
    user_id: UUID,
    product_code: str,
) -> EntitlementGrant | None:
    if subscription is not None and subscription.entitlement_id is not None:
        entitlement = entitlement_repository.get_entitlement(
            entitlement_id=subscription.entitlement_id
        )
        if entitlement is not None:
            return entitlement

    matches = [
        entitlement
        for entitlement in entitlement_repository.list_user_entitlements(user_id=user_id)
        if entitlement.product_code == product_code
    ]
    if not matches:
        return None
    matches.sort(key=lambda item: (item.updated_at, item.created_at), reverse=True)
    return matches[0]


def _build_checkout_session(
    *,
    provider_event: ProviderWebhookEventDto,
    checkout: BillingCheckoutSession | None,
    user_id: UUID,
    product_code: str,
    provider_name: PaymentProviderName,
) -> BillingCheckoutSession | None:
    if checkout is None:
        if provider_event.effect != "checkout_completed" or provider_event.checkout_id is None:
            return None
        return BillingCheckoutSession(
            id=provider_event.checkout_id,
            user_id=user_id,
            product_code=product_code,
            provider_name=provider_name,
            provider_checkout_session_id=provider_event.provider_checkout_session_id,
            provider_customer_id=provider_event.provider_customer_id,
            provider_subscription_id=provider_event.provider_subscription_id,
            status="open",
            checkout_url=None,
            success_path="/",
            cancel_path="/",
            requested_at=provider_event.occurred_at,
            expires_at=None,
            completed_at=None,
            canceled_at=None,
            updated_at=provider_event.received_at,
        )

    status = checkout.status
    completed_at = checkout.completed_at
    canceled_at = checkout.canceled_at
    if provider_event.effect in {"invoice_paid", "subscription_updated"} and _should_unlock_access(
        effect=provider_event.effect,
        subscription_status=provider_event.subscription_status,
        current_period_ends_at=provider_event.current_period_ends_at,
        cancel_at_period_end=provider_event.cancel_at_period_end,
        at=provider_event.occurred_at,
    ):
        status = "completed"
        completed_at = provider_event.occurred_at
    if provider_event.effect == "subscription_deleted" and not _should_unlock_access(
        effect=provider_event.effect,
        subscription_status=provider_event.subscription_status,
        current_period_ends_at=provider_event.current_period_ends_at,
        cancel_at_period_end=provider_event.cancel_at_period_end,
        at=provider_event.occurred_at,
    ):
        status = "canceled"
        canceled_at = provider_event.canceled_at or provider_event.occurred_at
    if provider_event.effect in {"charge_refunded", "charge_disputed"}:
        status = "canceled"
        canceled_at = provider_event.occurred_at

    return BillingCheckoutSession(
        id=checkout.id,
        user_id=checkout.user_id,
        product_code=checkout.product_code,
        provider_name=checkout.provider_name,
        provider_checkout_session_id=(
            provider_event.provider_checkout_session_id or checkout.provider_checkout_session_id
        ),
        provider_customer_id=provider_event.provider_customer_id or checkout.provider_customer_id,
        provider_subscription_id=(
            provider_event.provider_subscription_id or checkout.provider_subscription_id
        ),
        status=status,
        checkout_url=checkout.checkout_url,
        success_path=checkout.success_path,
        cancel_path=checkout.cancel_path,
        requested_at=checkout.requested_at,
        expires_at=provider_event.current_period_ends_at or checkout.expires_at,
        completed_at=completed_at,
        canceled_at=canceled_at,
        updated_at=provider_event.received_at,
    )


def _build_subscription(
    *,
    provider_event: ProviderWebhookEventDto,
    subscription: BillingSubscription | None,
    checkout: BillingCheckoutSession | None,
    user_id: UUID,
    product_code: str,
    entitlement: EntitlementGrant | None,
) -> BillingSubscription | None:
    provider_subscription_id = (
        provider_event.provider_subscription_id
        or (subscription.provider_subscription_id if subscription is not None else None)
        or (checkout.provider_subscription_id if checkout is not None else None)
    )
    if provider_subscription_id is None:
        return subscription

    created_at = subscription.created_at if subscription is not None else provider_event.received_at
    subscription_status: BillingSubscriptionStatus = provider_event.subscription_status or (
        subscription.status if subscription is not None else "active"
    )
    return BillingSubscription(
        id=subscription.id if subscription is not None else uuid4(),
        user_id=user_id,
        product_code=product_code,
        provider_name=provider_event.provider_name,
        provider_subscription_id=provider_subscription_id,
        provider_customer_id=provider_event.provider_customer_id
        or (subscription.provider_customer_id if subscription is not None else None)
        or (checkout.provider_customer_id if checkout is not None else None),
        status=subscription_status,
        current_period_starts_at=provider_event.current_period_starts_at
        or (subscription.current_period_starts_at if subscription is not None else None),
        current_period_ends_at=provider_event.current_period_ends_at
        or (subscription.current_period_ends_at if subscription is not None else None),
        cancel_at_period_end=provider_event.cancel_at_period_end
        if provider_event.cancel_at_period_end is not None
        else (subscription.cancel_at_period_end if subscription is not None else False),
        canceled_at=provider_event.canceled_at
        or (subscription.canceled_at if subscription is not None else None),
        latest_checkout_session_id=checkout.id
        if checkout is not None
        else (subscription.latest_checkout_session_id if subscription is not None else None),
        entitlement_id=entitlement.id
        if entitlement is not None
        else (subscription.entitlement_id if subscription is not None else None),
        latest_invoice_id=provider_event.latest_invoice_id
        or (subscription.latest_invoice_id if subscription is not None else None),
        latest_charge_id=provider_event.latest_charge_id
        or (subscription.latest_charge_id if subscription is not None else None),
        created_at=created_at,
        updated_at=provider_event.received_at,
    )


def _build_entitlement_updates(
    *,
    provider_event: ProviderWebhookEventDto,
    entitlement: EntitlementGrant | None,
    subscription: BillingSubscription | None,
    user_id: UUID,
    product_code: str,
    reconciled_at: datetime,
) -> tuple[EntitlementGrant | None, EntitlementEvent | None]:
    if provider_event.effect == "checkout_completed":
        return entitlement, None
    if subscription is None:
        return entitlement, None

    entitlement_id = entitlement.id if entitlement is not None else uuid4()
    created_at = entitlement.created_at if entitlement is not None else reconciled_at
    effective_ends_at = subscription.current_period_ends_at
    should_unlock = _should_unlock_access(
        effect=provider_event.effect,
        subscription_status=subscription.status,
        current_period_ends_at=subscription.current_period_ends_at,
        cancel_at_period_end=subscription.cancel_at_period_end,
        at=provider_event.occurred_at,
    )
    is_revocation = provider_event.effect in {"charge_refunded", "charge_disputed"}
    status: PersistedEntitlementStatus = "revoked" if is_revocation else "active"
    starts_at = subscription.current_period_starts_at or (
        entitlement.starts_at if entitlement is not None else provider_event.occurred_at
    )
    revoked_at = provider_event.occurred_at if is_revocation else None
    revoked_reason_code = provider_event.revoke_reason_code if is_revocation else None
    if not should_unlock and not is_revocation:
        effective_ends_at = effective_ends_at or provider_event.occurred_at

    updated_entitlement = EntitlementGrant(
        id=entitlement_id,
        user_id=user_id,
        product_code=product_code,
        status=status,
        starts_at=starts_at,
        ends_at=effective_ends_at,
        revoked_at=revoked_at,
        revoked_reason_code=revoked_reason_code,
        created_at=created_at,
        updated_at=reconciled_at,
    )
    event_type, reason_code = _entitlement_event_type(
        provider_event=provider_event,
        entitlement=entitlement,
        should_unlock=should_unlock,
    )
    return updated_entitlement, EntitlementEvent(
        id=uuid4(),
        entitlement_id=updated_entitlement.id,
        user_id=user_id,
        product_code=product_code,
        event_type=event_type,
        occurred_at=provider_event.occurred_at,
        reason_code=reason_code,
        provider_name=provider_event.provider_name,
        provider_event_id=provider_event.provider_event_id,
        correlation_id=str(provider_event.checkout_id)
        if provider_event.checkout_id is not None
        else provider_event.provider_subscription_id,
    )


def _entitlement_event_type(
    *,
    provider_event: ProviderWebhookEventDto,
    entitlement: EntitlementGrant | None,
    should_unlock: bool,
) -> tuple[str, str | None]:
    if provider_event.effect == "invoice_paid":
        return ("grant_renewed" if entitlement is not None else "grant_activated", None)
    if provider_event.effect == "subscription_updated":
        if should_unlock:
            return ("grant_activated" if entitlement is None else "grant_updated", None)
        return ("grant_scheduled_to_expire", "subscription_updated")
    if provider_event.effect == "subscription_deleted":
        if should_unlock:
            return ("grant_scheduled_to_expire", "subscription_canceled")
        return ("grant_expired", "subscription_canceled")
    if provider_event.effect == "invoice_payment_failed":
        if should_unlock:
            return ("grant_scheduled_to_expire", "payment_failed")
        return ("grant_expired", "payment_failed")
    if provider_event.effect == "charge_refunded":
        return ("grant_revoked", provider_event.revoke_reason_code or "refund")
    if provider_event.effect == "charge_disputed":
        return ("grant_revoked", provider_event.revoke_reason_code or "dispute")
    return ("grant_updated", None)


def _should_unlock_access(
    *,
    effect: str,
    subscription_status: str | None,
    current_period_ends_at: datetime | None,
    cancel_at_period_end: bool | None,
    at: datetime,
) -> bool:
    if effect in {"charge_refunded", "charge_disputed"}:
        return False
    if current_period_ends_at is not None and current_period_ends_at <= at:
        return False
    if effect in {"invoice_payment_failed", "subscription_deleted"}:
        return current_period_ends_at is not None and current_period_ends_at > at
    normalized_status = (subscription_status or "").strip().casefold()
    if normalized_status in {"active", "trialing", "past_due"}:
        return True
    if cancel_at_period_end and current_period_ends_at is not None:
        return current_period_ends_at > at
    return effect == "checkout_completed"


def _payment_event(
    *,
    provider_event: ProviderWebhookEventDto,
    reconciliation_status: PaymentEventReconciliationStatus,
    reconciled_at: datetime | None,
    checkout_id: UUID | None,
    user_id: UUID | None,
    product_code: str | None,
) -> PaymentEvent:
    return PaymentEvent(
        id=uuid4(),
        provider_name=provider_event.provider_name,
        provider_event_id=provider_event.provider_event_id,
        event_type=provider_event.event_type,
        effect=provider_event.effect,
        occurred_at=provider_event.occurred_at,
        received_at=provider_event.received_at,
        payload=provider_event.payload,
        signature_verified=True,
        checkout_id=checkout_id,
        user_id=user_id,
        product_code=product_code,
        provider_customer_id=provider_event.provider_customer_id,
        provider_checkout_session_id=provider_event.provider_checkout_session_id,
        provider_subscription_id=provider_event.provider_subscription_id,
        latest_invoice_id=provider_event.latest_invoice_id,
        latest_charge_id=provider_event.latest_charge_id,
        reconciliation_status=reconciliation_status,
        reconciled_at=reconciled_at,
    )


def _absolute_public_url(public_origin: str, path: str, **params: str) -> str:
    normalized_origin = public_origin.rstrip("/")
    split = urlsplit(path)
    query_items = list(parse_qsl(split.query, keep_blank_values=True))
    query_items.extend(params.items())
    return (
        f"{normalized_origin}"
        f"{urlunsplit(('', '', split.path, urlencode(query_items), split.fragment))}"
    )
