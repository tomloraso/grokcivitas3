from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Any, cast

from sqlalchemy import text
from sqlalchemy.engine import Engine, RowMapping

from civitas.application.access.ports.product_repository import ProductRepository
from civitas.domain.access.models import PremiumProduct
from civitas.domain.access.value_objects import BillingInterval


class PostgresProductRepository(ProductRepository):
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def get_product_by_code(self, *, code: str) -> PremiumProduct | None:
        statement = text(
            """
            SELECT
                products.code,
                products.display_name,
                products.description,
                products.billing_interval,
                products.duration_days,
                products.provider_price_lookup_key,
                products.is_active,
                products.created_at,
                products.updated_at,
                COALESCE(
                    array_agg(capabilities.capability_key ORDER BY capabilities.capability_key)
                    FILTER (WHERE capabilities.capability_key IS NOT NULL),
                    ARRAY[]::text[]
                ) AS capability_keys
            FROM premium_products AS products
            LEFT JOIN product_capabilities AS capabilities
                ON capabilities.product_code = products.code
            WHERE products.code = :code
            GROUP BY
                products.code,
                products.display_name,
                products.description,
                products.billing_interval,
                products.duration_days,
                products.provider_price_lookup_key,
                products.is_active,
                products.created_at,
                products.updated_at
            """
        )
        with self._engine.connect() as connection:
            row = connection.execute(statement, {"code": code}).mappings().first()
        return None if row is None else _to_premium_product(row)

    def list_available_products(self) -> tuple[PremiumProduct, ...]:
        statement = text(
            """
            SELECT
                products.code,
                products.display_name,
                products.description,
                products.billing_interval,
                products.duration_days,
                products.provider_price_lookup_key,
                products.is_active,
                products.created_at,
                products.updated_at,
                COALESCE(
                    array_agg(capabilities.capability_key ORDER BY capabilities.capability_key)
                    FILTER (WHERE capabilities.capability_key IS NOT NULL),
                    ARRAY[]::text[]
                ) AS capability_keys
            FROM premium_products AS products
            LEFT JOIN product_capabilities AS capabilities
                ON capabilities.product_code = products.code
            WHERE products.is_active = TRUE
            GROUP BY
                products.code,
                products.display_name,
                products.description,
                products.billing_interval,
                products.duration_days,
                products.provider_price_lookup_key,
                products.is_active,
                products.created_at,
                products.updated_at
            ORDER BY products.code ASC
            """
        )
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings()
            return tuple(_to_premium_product(row) for row in rows)

    def list_products_for_capability(
        self,
        *,
        capability_key: str,
    ) -> tuple[PremiumProduct, ...]:
        statement = text(
            """
            SELECT
                products.code,
                products.display_name,
                products.description,
                products.billing_interval,
                products.duration_days,
                products.provider_price_lookup_key,
                products.is_active,
                products.created_at,
                products.updated_at,
                COALESCE(
                    array_agg(all_capabilities.capability_key ORDER BY all_capabilities.capability_key)
                    FILTER (WHERE all_capabilities.capability_key IS NOT NULL),
                    ARRAY[]::text[]
                ) AS capability_keys
            FROM premium_products AS products
            INNER JOIN product_capabilities AS requested_capability
                ON requested_capability.product_code = products.code
            LEFT JOIN product_capabilities AS all_capabilities
                ON all_capabilities.product_code = products.code
            WHERE products.is_active = TRUE
              AND requested_capability.capability_key = :capability_key
            GROUP BY
                products.code,
                products.display_name,
                products.description,
                products.billing_interval,
                products.duration_days,
                products.provider_price_lookup_key,
                products.is_active,
                products.created_at,
                products.updated_at
            ORDER BY products.code ASC
            """
        )
        with self._engine.connect() as connection:
            rows = connection.execute(
                statement,
                {"capability_key": capability_key},
            ).mappings()
            return tuple(_to_premium_product(row) for row in rows)


def _to_premium_product(row: RowMapping) -> PremiumProduct:
    raw_capability_keys = row["capability_keys"]
    capability_keys: tuple[str, ...]
    if raw_capability_keys is None:
        capability_keys = ()
    else:
        capability_keys = tuple(str(value) for value in cast(Sequence[Any], raw_capability_keys))

    return PremiumProduct(
        code=str(row["code"]),
        display_name=str(row["display_name"]),
        description=None if row["description"] is None else str(row["description"]),
        billing_interval=_to_billing_interval(row["billing_interval"]),
        duration_days=None if row["duration_days"] is None else int(row["duration_days"]),
        provider_price_lookup_key=(
            None
            if row["provider_price_lookup_key"] is None
            else str(row["provider_price_lookup_key"])
        ),
        capability_keys=capability_keys,
        is_active=bool(row["is_active"]),
        created_at=_to_datetime(row["created_at"]),
        updated_at=_to_datetime(row["updated_at"]),
    )


def _to_datetime(value: object) -> datetime:
    if isinstance(value, datetime):
        return value
    raise TypeError(f"Expected datetime, got {type(value).__name__}.")


def _to_billing_interval(value: object) -> BillingInterval | None:
    if value is None:
        return None
    normalized = str(value)
    if normalized not in {"monthly", "annual", "one_time"}:
        raise ValueError(f"Unsupported billing interval '{normalized}'.")
    return cast(BillingInterval, normalized)
