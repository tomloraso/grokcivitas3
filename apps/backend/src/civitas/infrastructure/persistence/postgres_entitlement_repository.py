from __future__ import annotations

from datetime import datetime
from typing import cast
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.engine import Engine, RowMapping

from civitas.application.access.ports.entitlement_repository import EntitlementRepository
from civitas.domain.access.models import EntitlementEvent, EntitlementGrant
from civitas.domain.access.value_objects import PersistedEntitlementStatus


class PostgresEntitlementRepository(EntitlementRepository):
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def get_entitlement(self, *, entitlement_id: UUID) -> EntitlementGrant | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    text(
                        """
                        SELECT
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
                        FROM entitlements
                        WHERE id = :entitlement_id
                        """
                    ),
                    {"entitlement_id": entitlement_id},
                )
                .mappings()
                .first()
            )
        return None if row is None else _to_entitlement_grant(row)

    def list_user_entitlements(self, *, user_id: UUID) -> tuple[EntitlementGrant, ...]:
        with self._engine.connect() as connection:
            rows = connection.execute(
                text(
                    """
                    SELECT
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
                    FROM entitlements
                    WHERE user_id = :user_id
                    ORDER BY starts_at DESC, created_at DESC
                    """
                ),
                {"user_id": user_id},
            ).mappings()
            return tuple(_to_entitlement_grant(row) for row in rows)

    def list_active_capability_keys(
        self,
        *,
        user_id: UUID,
        at: datetime,
    ) -> tuple[str, ...]:
        with self._engine.connect() as connection:
            rows = connection.execute(
                text(
                    """
                    SELECT DISTINCT capabilities.capability_key
                    FROM entitlements
                    INNER JOIN product_capabilities AS capabilities
                        ON capabilities.product_code = entitlements.product_code
                    WHERE entitlements.user_id = :user_id
                      AND entitlements.status = 'active'
                      AND entitlements.revoked_at IS NULL
                      AND entitlements.starts_at <= :at
                      AND (entitlements.ends_at IS NULL OR entitlements.ends_at > :at)
                    ORDER BY capabilities.capability_key ASC
                    """
                ),
                {"user_id": user_id, "at": at},
            )
            return tuple(str(row[0]) for row in rows)

    def upsert_entitlement(self, entitlement: EntitlementGrant) -> EntitlementGrant:
        with self._engine.begin() as connection:
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
                {
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
                },
            )
        return entitlement

    def append_event(self, event: EntitlementEvent) -> EntitlementEvent:
        with self._engine.begin() as connection:
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
                {
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
                },
            )
        return event

    def list_entitlement_events(
        self,
        *,
        entitlement_id: UUID | None = None,
        user_id: UUID | None = None,
    ) -> tuple[EntitlementEvent, ...]:
        if entitlement_id is None and user_id is None:
            raise ValueError("entitlement_id or user_id is required")

        conditions: list[str] = []
        params: dict[str, object] = {}
        if entitlement_id is not None:
            conditions.append("entitlement_id = :entitlement_id")
            params["entitlement_id"] = entitlement_id
        if user_id is not None:
            conditions.append("user_id = :user_id")
            params["user_id"] = user_id

        where_clause = " AND ".join(conditions)
        statement = text(
            f"""
            SELECT
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
            FROM entitlement_events
            WHERE {where_clause}
            ORDER BY occurred_at DESC, created_at DESC
            """
        )
        with self._engine.connect() as connection:
            rows = connection.execute(statement, params).mappings()
            return tuple(_to_entitlement_event(row) for row in rows)


def _to_entitlement_grant(row: RowMapping) -> EntitlementGrant:
    return EntitlementGrant(
        id=_to_uuid(row["id"]),
        user_id=_to_uuid(row["user_id"]),
        product_code=str(row["product_code"]),
        status=_to_persisted_status(row["status"]),
        starts_at=_to_datetime(row["starts_at"]),
        ends_at=_to_optional_datetime(row["ends_at"]),
        revoked_at=_to_optional_datetime(row["revoked_at"]),
        revoked_reason_code=(
            None if row["revoked_reason_code"] is None else str(row["revoked_reason_code"])
        ),
        created_at=_to_datetime(row["created_at"]),
        updated_at=_to_datetime(row["updated_at"]),
    )


def _to_entitlement_event(row: RowMapping) -> EntitlementEvent:
    return EntitlementEvent(
        id=_to_uuid(row["id"]),
        entitlement_id=_to_uuid(row["entitlement_id"]),
        user_id=_to_uuid(row["user_id"]),
        product_code=str(row["product_code"]),
        event_type=str(row["event_type"]),
        occurred_at=_to_datetime(row["occurred_at"]),
        reason_code=None if row["reason_code"] is None else str(row["reason_code"]),
        provider_name=None if row["provider_name"] is None else str(row["provider_name"]),
        provider_event_id=(
            None if row["provider_event_id"] is None else str(row["provider_event_id"])
        ),
        correlation_id=(None if row["correlation_id"] is None else str(row["correlation_id"])),
    )


def _to_uuid(value: object) -> UUID:
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


def _to_datetime(value: object) -> datetime:
    if isinstance(value, datetime):
        return value
    raise TypeError(f"Expected datetime, got {type(value).__name__}.")


def _to_optional_datetime(value: object) -> datetime | None:
    if value is None:
        return None
    return _to_datetime(value)


def _to_persisted_status(value: object) -> PersistedEntitlementStatus:
    normalized = str(value)
    if normalized not in {"pending", "active", "revoked"}:
        raise ValueError(f"Unsupported entitlement status '{normalized}'.")
    return cast(PersistedEntitlementStatus, normalized)
