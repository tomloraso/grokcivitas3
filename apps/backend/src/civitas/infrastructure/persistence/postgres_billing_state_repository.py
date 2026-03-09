from __future__ import annotations

import json
from datetime import datetime
from typing import cast
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.engine import Engine, RowMapping

from civitas.application.billing.dto import BillingReconciliationMutation
from civitas.application.billing.ports.billing_state_repository import BillingStateRepository
from civitas.domain.access.models import EntitlementEvent, EntitlementGrant
from civitas.domain.access.value_objects import PersistedEntitlementStatus
from civitas.domain.billing.models import (
    BillingCheckoutSession,
    BillingSubscription,
    PaymentCustomer,
)
from civitas.domain.billing.value_objects import (
    BillingSubscriptionStatus,
    CheckoutSessionStatus,
    normalize_provider_name,
)


class PostgresBillingStateRepository(BillingStateRepository):
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def get_checkout_session(self, *, checkout_id: UUID) -> BillingCheckoutSession | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    text(
                        """
                        SELECT
                            id,
                            user_id,
                            product_code,
                            provider_name,
                            provider_checkout_session_id,
                            provider_customer_id,
                            provider_subscription_id,
                            status,
                            checkout_url,
                            success_path,
                            cancel_path,
                            requested_at,
                            expires_at,
                            completed_at,
                            canceled_at,
                            updated_at
                        FROM checkout_sessions
                        WHERE id = :checkout_id
                        """
                    ),
                    {"checkout_id": checkout_id},
                )
                .mappings()
                .first()
            )
        return None if row is None else _to_checkout_session(row)

    def get_open_checkout_session(
        self,
        *,
        user_id: UUID,
        product_code: str,
        at: datetime,
    ) -> BillingCheckoutSession | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    text(
                        """
                        SELECT
                            id,
                            user_id,
                            product_code,
                            provider_name,
                            provider_checkout_session_id,
                            provider_customer_id,
                            provider_subscription_id,
                            status,
                            checkout_url,
                            success_path,
                            cancel_path,
                            requested_at,
                            expires_at,
                            completed_at,
                            canceled_at,
                            updated_at
                        FROM checkout_sessions
                        WHERE user_id = :user_id
                          AND product_code = :product_code
                          AND status = 'open'
                          AND completed_at IS NULL
                          AND canceled_at IS NULL
                          AND (expires_at IS NULL OR expires_at > :at)
                        ORDER BY requested_at DESC
                        LIMIT 1
                        """
                    ),
                    {"user_id": user_id, "product_code": product_code, "at": at},
                )
                .mappings()
                .first()
            )
        return None if row is None else _to_checkout_session(row)

    def create_pending_checkout_session(
        self,
        checkout_session: BillingCheckoutSession,
    ) -> BillingCheckoutSession:
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO checkout_sessions (
                        id,
                        user_id,
                        product_code,
                        provider_name,
                        provider_checkout_session_id,
                        provider_customer_id,
                        provider_subscription_id,
                        status,
                        checkout_url,
                        success_path,
                        cancel_path,
                        requested_at,
                        expires_at,
                        completed_at,
                        canceled_at,
                        updated_at
                    ) VALUES (
                        :id,
                        :user_id,
                        :product_code,
                        :provider_name,
                        :provider_checkout_session_id,
                        :provider_customer_id,
                        :provider_subscription_id,
                        :status,
                        :checkout_url,
                        :success_path,
                        :cancel_path,
                        :requested_at,
                        :expires_at,
                        :completed_at,
                        :canceled_at,
                        :updated_at
                    )
                    """
                ),
                _checkout_session_params(checkout_session),
            )
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
        with self._engine.begin() as connection:
            row = (
                connection.execute(
                    text(
                        """
                        UPDATE checkout_sessions
                        SET
                            provider_name = :provider_name,
                            provider_checkout_session_id = :provider_checkout_session_id,
                            provider_customer_id = :provider_customer_id,
                            provider_subscription_id = :provider_subscription_id,
                            status = 'open',
                            checkout_url = :checkout_url,
                            expires_at = :expires_at,
                            updated_at = :updated_at
                        WHERE id = :checkout_id
                        RETURNING
                            id,
                            user_id,
                            product_code,
                            provider_name,
                            provider_checkout_session_id,
                            provider_customer_id,
                            provider_subscription_id,
                            status,
                            checkout_url,
                            success_path,
                            cancel_path,
                            requested_at,
                            expires_at,
                            completed_at,
                            canceled_at,
                            updated_at
                        """
                    ),
                    {
                        "checkout_id": checkout_id,
                        "provider_name": provider_name,
                        "provider_checkout_session_id": provider_checkout_session_id,
                        "provider_customer_id": provider_customer_id,
                        "provider_subscription_id": provider_subscription_id,
                        "checkout_url": checkout_url,
                        "expires_at": expires_at,
                        "updated_at": updated_at,
                    },
                )
                .mappings()
                .first()
            )
        return None if row is None else _to_checkout_session(row)

    def mark_checkout_session_failed(
        self,
        *,
        checkout_id: UUID,
        updated_at: datetime,
    ) -> BillingCheckoutSession | None:
        with self._engine.begin() as connection:
            row = (
                connection.execute(
                    text(
                        """
                        UPDATE checkout_sessions
                        SET status = 'failed', updated_at = :updated_at
                        WHERE id = :checkout_id
                        RETURNING
                            id,
                            user_id,
                            product_code,
                            provider_name,
                            provider_checkout_session_id,
                            provider_customer_id,
                            provider_subscription_id,
                            status,
                            checkout_url,
                            success_path,
                            cancel_path,
                            requested_at,
                            expires_at,
                            completed_at,
                            canceled_at,
                            updated_at
                        """
                    ),
                    {"checkout_id": checkout_id, "updated_at": updated_at},
                )
                .mappings()
                .first()
            )
        return None if row is None else _to_checkout_session(row)

    def get_payment_customer_by_user(
        self,
        *,
        user_id: UUID,
        provider_name: str,
    ) -> PaymentCustomer | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    text(
                        """
                        SELECT
                            user_id,
                            provider_name,
                            provider_customer_id,
                            created_at,
                            updated_at
                        FROM payment_customers
                        WHERE user_id = :user_id
                          AND provider_name = :provider_name
                        """
                    ),
                    {"user_id": user_id, "provider_name": provider_name},
                )
                .mappings()
                .first()
            )
        return None if row is None else _to_payment_customer(row)

    def get_payment_customer_by_provider_customer_id(
        self,
        *,
        provider_name: str,
        provider_customer_id: str,
    ) -> PaymentCustomer | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    text(
                        """
                        SELECT
                            user_id,
                            provider_name,
                            provider_customer_id,
                            created_at,
                            updated_at
                        FROM payment_customers
                        WHERE provider_name = :provider_name
                          AND provider_customer_id = :provider_customer_id
                        """
                    ),
                    {
                        "provider_name": provider_name,
                        "provider_customer_id": provider_customer_id,
                    },
                )
                .mappings()
                .first()
            )
        return None if row is None else _to_payment_customer(row)

    def get_subscription_by_provider_subscription_id(
        self,
        *,
        provider_name: str,
        provider_subscription_id: str,
    ) -> BillingSubscription | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    text(
                        """
                        SELECT
                            id,
                            user_id,
                            product_code,
                            provider_name,
                            provider_subscription_id,
                            provider_customer_id,
                            status,
                            current_period_starts_at,
                            current_period_ends_at,
                            cancel_at_period_end,
                            canceled_at,
                            latest_checkout_session_id,
                            entitlement_id,
                            latest_invoice_id,
                            latest_charge_id,
                            created_at,
                            updated_at
                        FROM billing_subscriptions
                        WHERE provider_name = :provider_name
                          AND provider_subscription_id = :provider_subscription_id
                        """
                    ),
                    {
                        "provider_name": provider_name,
                        "provider_subscription_id": provider_subscription_id,
                    },
                )
                .mappings()
                .first()
            )
        return None if row is None else _to_billing_subscription(row)

    def get_subscription_by_latest_charge_id(
        self,
        *,
        provider_name: str,
        latest_charge_id: str,
    ) -> BillingSubscription | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    text(
                        """
                        SELECT
                            id,
                            user_id,
                            product_code,
                            provider_name,
                            provider_subscription_id,
                            provider_customer_id,
                            status,
                            current_period_starts_at,
                            current_period_ends_at,
                            cancel_at_period_end,
                            canceled_at,
                            latest_checkout_session_id,
                            entitlement_id,
                            latest_invoice_id,
                            latest_charge_id,
                            created_at,
                            updated_at
                        FROM billing_subscriptions
                        WHERE provider_name = :provider_name
                          AND latest_charge_id = :latest_charge_id
                        """
                    ),
                    {
                        "provider_name": provider_name,
                        "latest_charge_id": latest_charge_id,
                    },
                )
                .mappings()
                .first()
            )
        return None if row is None else _to_billing_subscription(row)

    def get_latest_subscription_by_provider_customer_id(
        self,
        *,
        provider_name: str,
        provider_customer_id: str,
        product_code: str | None = None,
    ) -> BillingSubscription | None:
        statement = text(
            """
            SELECT
                id,
                user_id,
                product_code,
                provider_name,
                provider_subscription_id,
                provider_customer_id,
                status,
                current_period_starts_at,
                current_period_ends_at,
                cancel_at_period_end,
                canceled_at,
                latest_checkout_session_id,
                entitlement_id,
                latest_invoice_id,
                latest_charge_id,
                created_at,
                updated_at
            FROM billing_subscriptions
            WHERE provider_name = :provider_name
              AND provider_customer_id = :provider_customer_id
              AND (:product_code IS NULL OR product_code = :product_code)
            ORDER BY updated_at DESC, created_at DESC
            LIMIT 1
            """
        )
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    statement,
                    {
                        "provider_name": provider_name,
                        "provider_customer_id": provider_customer_id,
                        "product_code": product_code,
                    },
                )
                .mappings()
                .first()
            )
        return None if row is None else _to_billing_subscription(row)

    def get_checkout_session_by_provider_checkout_session_id(
        self,
        *,
        provider_name: str,
        provider_checkout_session_id: str,
    ) -> BillingCheckoutSession | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    text(
                        """
                        SELECT
                            id,
                            user_id,
                            product_code,
                            provider_name,
                            provider_checkout_session_id,
                            provider_customer_id,
                            provider_subscription_id,
                            status,
                            checkout_url,
                            success_path,
                            cancel_path,
                            requested_at,
                            expires_at,
                            completed_at,
                            canceled_at,
                            updated_at
                        FROM checkout_sessions
                        WHERE provider_name = :provider_name
                          AND provider_checkout_session_id = :provider_checkout_session_id
                        """
                    ),
                    {
                        "provider_name": provider_name,
                        "provider_checkout_session_id": provider_checkout_session_id,
                    },
                )
                .mappings()
                .first()
            )
        return None if row is None else _to_checkout_session(row)

    def apply_reconciliation(self, mutation: BillingReconciliationMutation) -> bool:
        with self._engine.begin() as connection:
            inserted_event = connection.execute(
                text(
                    """
                    INSERT INTO payment_events (
                        id,
                        provider_name,
                        provider_event_id,
                        event_type,
                        effect,
                        occurred_at,
                        received_at,
                        payload,
                        signature_verified,
                        checkout_id,
                        user_id,
                        product_code,
                        provider_customer_id,
                        provider_checkout_session_id,
                        provider_subscription_id,
                        latest_invoice_id,
                        latest_charge_id,
                        reconciliation_status,
                        reconciled_at
                    ) VALUES (
                        :id,
                        :provider_name,
                        :provider_event_id,
                        :event_type,
                        :effect,
                        :occurred_at,
                        :received_at,
                        CAST(:payload AS JSONB),
                        :signature_verified,
                        :checkout_id,
                        :user_id,
                        :product_code,
                        :provider_customer_id,
                        :provider_checkout_session_id,
                        :provider_subscription_id,
                        :latest_invoice_id,
                        :latest_charge_id,
                        :reconciliation_status,
                        :reconciled_at
                    )
                    ON CONFLICT (provider_name, provider_event_id) DO NOTHING
                    RETURNING provider_event_id
                    """
                ),
                _payment_event_params(mutation),
            ).scalar_one_or_none()
            if inserted_event is None:
                return False

            if mutation.payment_customer is not None:
                connection.execute(
                    text(
                        """
                        INSERT INTO payment_customers (
                            user_id,
                            provider_name,
                            provider_customer_id,
                            created_at,
                            updated_at
                        ) VALUES (
                            :user_id,
                            :provider_name,
                            :provider_customer_id,
                            :created_at,
                            :updated_at
                        )
                        ON CONFLICT (provider_name, user_id) DO UPDATE SET
                            provider_customer_id = EXCLUDED.provider_customer_id,
                            updated_at = EXCLUDED.updated_at
                        """
                    ),
                    _payment_customer_params(mutation.payment_customer),
                )

            if mutation.checkout_session is not None:
                connection.execute(
                    text(
                        """
                        INSERT INTO checkout_sessions (
                            id,
                            user_id,
                            product_code,
                            provider_name,
                            provider_checkout_session_id,
                            provider_customer_id,
                            provider_subscription_id,
                            status,
                            checkout_url,
                            success_path,
                            cancel_path,
                            requested_at,
                            expires_at,
                            completed_at,
                            canceled_at,
                            updated_at
                        ) VALUES (
                            :id,
                            :user_id,
                            :product_code,
                            :provider_name,
                            :provider_checkout_session_id,
                            :provider_customer_id,
                            :provider_subscription_id,
                            :status,
                            :checkout_url,
                            :success_path,
                            :cancel_path,
                            :requested_at,
                            :expires_at,
                            :completed_at,
                            :canceled_at,
                            :updated_at
                        )
                        ON CONFLICT (id) DO UPDATE SET
                            provider_name = EXCLUDED.provider_name,
                            provider_checkout_session_id = EXCLUDED.provider_checkout_session_id,
                            provider_customer_id = EXCLUDED.provider_customer_id,
                            provider_subscription_id = EXCLUDED.provider_subscription_id,
                            status = EXCLUDED.status,
                            checkout_url = EXCLUDED.checkout_url,
                            success_path = EXCLUDED.success_path,
                            cancel_path = EXCLUDED.cancel_path,
                            requested_at = EXCLUDED.requested_at,
                            expires_at = EXCLUDED.expires_at,
                            completed_at = EXCLUDED.completed_at,
                            canceled_at = EXCLUDED.canceled_at,
                            updated_at = EXCLUDED.updated_at
                        """
                    ),
                    _checkout_session_params(mutation.checkout_session),
                )

            if mutation.subscription is not None:
                connection.execute(
                    text(
                        """
                        INSERT INTO billing_subscriptions (
                            id,
                            user_id,
                            product_code,
                            provider_name,
                            provider_subscription_id,
                            provider_customer_id,
                            status,
                            current_period_starts_at,
                            current_period_ends_at,
                            cancel_at_period_end,
                            canceled_at,
                            latest_checkout_session_id,
                            entitlement_id,
                            latest_invoice_id,
                            latest_charge_id,
                            created_at,
                            updated_at
                        ) VALUES (
                            :id,
                            :user_id,
                            :product_code,
                            :provider_name,
                            :provider_subscription_id,
                            :provider_customer_id,
                            :status,
                            :current_period_starts_at,
                            :current_period_ends_at,
                            :cancel_at_period_end,
                            :canceled_at,
                            :latest_checkout_session_id,
                            :entitlement_id,
                            :latest_invoice_id,
                            :latest_charge_id,
                            :created_at,
                            :updated_at
                        )
                        ON CONFLICT (provider_name, provider_subscription_id) DO UPDATE SET
                            user_id = EXCLUDED.user_id,
                            product_code = EXCLUDED.product_code,
                            provider_customer_id = EXCLUDED.provider_customer_id,
                            status = EXCLUDED.status,
                            current_period_starts_at = EXCLUDED.current_period_starts_at,
                            current_period_ends_at = EXCLUDED.current_period_ends_at,
                            cancel_at_period_end = EXCLUDED.cancel_at_period_end,
                            canceled_at = EXCLUDED.canceled_at,
                            latest_checkout_session_id = EXCLUDED.latest_checkout_session_id,
                            entitlement_id = EXCLUDED.entitlement_id,
                            latest_invoice_id = EXCLUDED.latest_invoice_id,
                            latest_charge_id = EXCLUDED.latest_charge_id,
                            updated_at = EXCLUDED.updated_at
                        """
                    ),
                    _billing_subscription_params(mutation.subscription),
                )

            if mutation.entitlement is not None:
                connection.execute(
                    text(
                        """
                        INSERT INTO entitlements (
                            id,
                            user_id,
                            product_code,
                            status,
                            starts_at,
                            ends_at,
                            revoked_at,
                            revoked_reason_code,
                            created_at,
                            updated_at
                        ) VALUES (
                            :id,
                            :user_id,
                            :product_code,
                            :status,
                            :starts_at,
                            :ends_at,
                            :revoked_at,
                            :revoked_reason_code,
                            :created_at,
                            :updated_at
                        )
                        ON CONFLICT (id) DO UPDATE SET
                            user_id = EXCLUDED.user_id,
                            product_code = EXCLUDED.product_code,
                            status = EXCLUDED.status,
                            starts_at = EXCLUDED.starts_at,
                            ends_at = EXCLUDED.ends_at,
                            revoked_at = EXCLUDED.revoked_at,
                            revoked_reason_code = EXCLUDED.revoked_reason_code,
                            updated_at = EXCLUDED.updated_at
                        """
                    ),
                    _entitlement_params(mutation.entitlement),
                )

            if mutation.entitlement_event is not None:
                connection.execute(
                    text(
                        """
                        INSERT INTO entitlement_events (
                            id,
                            entitlement_id,
                            user_id,
                            product_code,
                            event_type,
                            occurred_at,
                            reason_code,
                            provider_name,
                            provider_event_id,
                            correlation_id
                        ) VALUES (
                            :id,
                            :entitlement_id,
                            :user_id,
                            :product_code,
                            :event_type,
                            :occurred_at,
                            :reason_code,
                            :provider_name,
                            :provider_event_id,
                            :correlation_id
                        )
                        """
                    ),
                    _entitlement_event_params(mutation.entitlement_event),
                )
        return True


def _checkout_session_params(checkout_session: BillingCheckoutSession) -> dict[str, object]:
    return {
        "id": checkout_session.id,
        "user_id": checkout_session.user_id,
        "product_code": checkout_session.product_code,
        "provider_name": checkout_session.provider_name,
        "provider_checkout_session_id": checkout_session.provider_checkout_session_id,
        "provider_customer_id": checkout_session.provider_customer_id,
        "provider_subscription_id": checkout_session.provider_subscription_id,
        "status": checkout_session.status,
        "checkout_url": checkout_session.checkout_url,
        "success_path": checkout_session.success_path,
        "cancel_path": checkout_session.cancel_path,
        "requested_at": checkout_session.requested_at,
        "expires_at": checkout_session.expires_at,
        "completed_at": checkout_session.completed_at,
        "canceled_at": checkout_session.canceled_at,
        "updated_at": checkout_session.updated_at,
    }


def _payment_customer_params(payment_customer: PaymentCustomer) -> dict[str, object]:
    return {
        "user_id": payment_customer.user_id,
        "provider_name": payment_customer.provider_name,
        "provider_customer_id": payment_customer.provider_customer_id,
        "created_at": payment_customer.created_at,
        "updated_at": payment_customer.updated_at,
    }


def _billing_subscription_params(subscription: BillingSubscription) -> dict[str, object]:
    return {
        "id": subscription.id,
        "user_id": subscription.user_id,
        "product_code": subscription.product_code,
        "provider_name": subscription.provider_name,
        "provider_subscription_id": subscription.provider_subscription_id,
        "provider_customer_id": subscription.provider_customer_id,
        "status": subscription.status,
        "current_period_starts_at": subscription.current_period_starts_at,
        "current_period_ends_at": subscription.current_period_ends_at,
        "cancel_at_period_end": subscription.cancel_at_period_end,
        "canceled_at": subscription.canceled_at,
        "latest_checkout_session_id": subscription.latest_checkout_session_id,
        "entitlement_id": subscription.entitlement_id,
        "latest_invoice_id": subscription.latest_invoice_id,
        "latest_charge_id": subscription.latest_charge_id,
        "created_at": subscription.created_at,
        "updated_at": subscription.updated_at,
    }


def _entitlement_params(entitlement: EntitlementGrant) -> dict[str, object]:
    return {
        "id": entitlement.id,
        "user_id": entitlement.user_id,
        "product_code": entitlement.product_code,
        "status": entitlement.status,
        "starts_at": entitlement.starts_at,
        "ends_at": entitlement.ends_at,
        "revoked_at": entitlement.revoked_at,
        "revoked_reason_code": entitlement.revoked_reason_code,
        "created_at": entitlement.created_at,
        "updated_at": entitlement.updated_at,
    }


def _entitlement_event_params(event: EntitlementEvent) -> dict[str, object]:
    return {
        "id": event.id,
        "entitlement_id": event.entitlement_id,
        "user_id": event.user_id,
        "product_code": event.product_code,
        "event_type": event.event_type,
        "occurred_at": event.occurred_at,
        "reason_code": event.reason_code,
        "provider_name": event.provider_name,
        "provider_event_id": event.provider_event_id,
        "correlation_id": event.correlation_id,
    }


def _payment_event_params(mutation: BillingReconciliationMutation) -> dict[str, object]:
    payment_event = mutation.payment_event
    return {
        "id": payment_event.id,
        "provider_name": payment_event.provider_name,
        "provider_event_id": payment_event.provider_event_id,
        "event_type": payment_event.event_type,
        "effect": payment_event.effect,
        "occurred_at": payment_event.occurred_at,
        "received_at": payment_event.received_at,
        "payload": json.dumps(payment_event.payload),
        "signature_verified": payment_event.signature_verified,
        "checkout_id": payment_event.checkout_id,
        "user_id": payment_event.user_id,
        "product_code": payment_event.product_code,
        "provider_customer_id": payment_event.provider_customer_id,
        "provider_checkout_session_id": payment_event.provider_checkout_session_id,
        "provider_subscription_id": payment_event.provider_subscription_id,
        "latest_invoice_id": payment_event.latest_invoice_id,
        "latest_charge_id": payment_event.latest_charge_id,
        "reconciliation_status": payment_event.reconciliation_status,
        "reconciled_at": payment_event.reconciled_at,
    }


def _to_checkout_session(row: RowMapping) -> BillingCheckoutSession:
    return BillingCheckoutSession(
        id=_to_uuid(row["id"]),
        user_id=_to_uuid(row["user_id"]),
        product_code=str(row["product_code"]),
        provider_name=normalize_provider_name(str(row["provider_name"])),
        provider_checkout_session_id=_to_optional_text(row["provider_checkout_session_id"]),
        provider_customer_id=_to_optional_text(row["provider_customer_id"]),
        provider_subscription_id=_to_optional_text(row["provider_subscription_id"]),
        status=_to_checkout_status(row["status"]),
        checkout_url=_to_optional_text(row["checkout_url"]),
        success_path=str(row["success_path"]),
        cancel_path=str(row["cancel_path"]),
        requested_at=_to_datetime(row["requested_at"]),
        expires_at=_to_optional_datetime(row["expires_at"]),
        completed_at=_to_optional_datetime(row["completed_at"]),
        canceled_at=_to_optional_datetime(row["canceled_at"]),
        updated_at=_to_datetime(row["updated_at"]),
    )


def _to_payment_customer(row: RowMapping) -> PaymentCustomer:
    return PaymentCustomer(
        user_id=_to_uuid(row["user_id"]),
        provider_name=normalize_provider_name(str(row["provider_name"])),
        provider_customer_id=str(row["provider_customer_id"]),
        created_at=_to_datetime(row["created_at"]),
        updated_at=_to_datetime(row["updated_at"]),
    )


def _to_billing_subscription(row: RowMapping) -> BillingSubscription:
    return BillingSubscription(
        id=_to_uuid(row["id"]),
        user_id=_to_uuid(row["user_id"]),
        product_code=str(row["product_code"]),
        provider_name=normalize_provider_name(str(row["provider_name"])),
        provider_subscription_id=str(row["provider_subscription_id"]),
        provider_customer_id=_to_optional_text(row["provider_customer_id"]),
        status=_to_billing_subscription_status(row["status"]),
        current_period_starts_at=_to_optional_datetime(row["current_period_starts_at"]),
        current_period_ends_at=_to_optional_datetime(row["current_period_ends_at"]),
        cancel_at_period_end=bool(row["cancel_at_period_end"]),
        canceled_at=_to_optional_datetime(row["canceled_at"]),
        latest_checkout_session_id=_to_optional_uuid(row["latest_checkout_session_id"]),
        entitlement_id=_to_optional_uuid(row["entitlement_id"]),
        latest_invoice_id=_to_optional_text(row["latest_invoice_id"]),
        latest_charge_id=_to_optional_text(row["latest_charge_id"]),
        created_at=_to_datetime(row["created_at"]),
        updated_at=_to_datetime(row["updated_at"]),
    )


def _to_uuid(value: object) -> UUID:
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


def _to_optional_uuid(value: object) -> UUID | None:
    if value is None:
        return None
    return _to_uuid(value)


def _to_datetime(value: object) -> datetime:
    if isinstance(value, datetime):
        return value
    raise TypeError(f"Expected datetime, got {type(value).__name__}.")


def _to_optional_datetime(value: object) -> datetime | None:
    if value is None:
        return None
    return _to_datetime(value)


def _to_optional_text(value: object) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _to_checkout_status(value: object) -> CheckoutSessionStatus:
    normalized = str(value)
    if normalized not in {"pending_provider", "open", "completed", "expired", "canceled", "failed"}:
        raise ValueError(f"Unsupported checkout session status '{normalized}'.")
    return cast(CheckoutSessionStatus, normalized)


def _to_billing_subscription_status(value: object) -> BillingSubscriptionStatus:
    normalized = str(value)
    if normalized not in {
        "incomplete",
        "incomplete_expired",
        "trialing",
        "active",
        "past_due",
        "canceled",
        "unpaid",
        "paused",
    }:
        raise ValueError(f"Unsupported billing subscription status '{normalized}'.")
    return cast(BillingSubscriptionStatus, normalized)


def _to_persisted_status(value: object) -> PersistedEntitlementStatus:
    normalized = str(value)
    if normalized not in {"pending", "active", "revoked"}:
        raise ValueError(f"Unsupported entitlement status '{normalized}'.")
    return cast(PersistedEntitlementStatus, normalized)
