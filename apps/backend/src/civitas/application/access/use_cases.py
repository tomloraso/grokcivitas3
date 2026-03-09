from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from uuid import UUID

from civitas.application.access.dto import (
    AccountAccessState,
    CurrentAccountAccessDto,
    EntitlementGrantDto,
    PremiumProductDto,
)
from civitas.application.access.policies import get_access_requirement
from civitas.application.access.ports.entitlement_repository import EntitlementRepository
from civitas.application.access.ports.product_repository import ProductRepository
from civitas.domain.access.models import AccessDecision, EntitlementGrant, PremiumProduct
from civitas.domain.access.services import build_access_decision


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


Clock = Callable[[], datetime]


class GetCurrentAccountAccessUseCase:
    def __init__(
        self,
        *,
        entitlement_repository: EntitlementRepository,
        product_repository: ProductRepository,
        clock: Clock = _utc_now,
    ) -> None:
        self._entitlement_repository = entitlement_repository
        self._product_repository = product_repository
        self._clock = clock

    def execute(self, *, user_id: UUID | None) -> CurrentAccountAccessDto:
        if user_id is None:
            return CurrentAccountAccessDto(
                state="anonymous",
                user_id=None,
                capability_keys=(),
                entitlements=(),
            )

        now = self._clock()
        entitlements = self._entitlement_repository.list_user_entitlements(user_id=user_id)
        capability_keys = self._entitlement_repository.list_active_capability_keys(
            user_id=user_id,
            at=now,
        )
        entitlement_dtos = tuple(
            _to_entitlement_dto(
                entitlement=entitlement,
                product=_load_product(
                    product_repository=self._product_repository,
                    code=entitlement.product_code,
                ),
                at=now,
            )
            for entitlement in entitlements
        )
        state = _current_access_state(
            capability_keys=capability_keys,
            entitlements=entitlements,
            at=now,
        )
        return CurrentAccountAccessDto(
            state=state,
            user_id=user_id,
            capability_keys=capability_keys,
            entitlements=entitlement_dtos,
        )


class EvaluateAccessUseCase:
    def __init__(
        self,
        *,
        entitlement_repository: EntitlementRepository,
        product_repository: ProductRepository,
        clock: Clock = _utc_now,
    ) -> None:
        self._entitlement_repository = entitlement_repository
        self._product_repository = product_repository
        self._clock = clock

    def execute(
        self,
        *,
        requirement_key: str,
        user_id: UUID | None,
        allow_preview: bool = True,
    ) -> AccessDecision:
        requirement = get_access_requirement(requirement_key)
        now = self._clock()
        products = (
            self._product_repository.list_products_for_capability(
                capability_key=requirement.capability_key,
            )
            if requirement.capability_key is not None
            else ()
        )
        available_product_codes = tuple(product.code for product in products)
        active_capability_keys: tuple[str, ...] = ()
        relevant_entitlements: tuple[EntitlementGrant, ...] = ()
        if user_id is not None:
            active_capability_keys = self._entitlement_repository.list_active_capability_keys(
                user_id=user_id,
                at=now,
            )
            relevant_entitlements = tuple(
                entitlement
                for entitlement in self._entitlement_repository.list_user_entitlements(
                    user_id=user_id
                )
                if entitlement.product_code in available_product_codes
            )
        return build_access_decision(
            requirement=requirement,
            user_id=user_id,
            active_capability_keys=active_capability_keys,
            relevant_entitlements=relevant_entitlements,
            available_product_codes=available_product_codes,
            at=now,
            allow_preview=allow_preview,
        )


class ListAvailablePremiumProductsUseCase:
    def __init__(self, *, product_repository: ProductRepository) -> None:
        self._product_repository = product_repository

    def execute(self) -> tuple[PremiumProductDto, ...]:
        return tuple(
            _to_product_dto(product)
            for product in self._product_repository.list_available_products()
        )


class ListUserEntitlementsUseCase:
    def __init__(
        self,
        *,
        entitlement_repository: EntitlementRepository,
        product_repository: ProductRepository,
        clock: Clock = _utc_now,
    ) -> None:
        self._entitlement_repository = entitlement_repository
        self._product_repository = product_repository
        self._clock = clock

    def execute(self, *, user_id: UUID) -> tuple[EntitlementGrantDto, ...]:
        now = self._clock()
        return tuple(
            _to_entitlement_dto(
                entitlement=entitlement,
                product=_load_product(
                    product_repository=self._product_repository,
                    code=entitlement.product_code,
                ),
                at=now,
            )
            for entitlement in self._entitlement_repository.list_user_entitlements(user_id=user_id)
        )


def _to_product_dto(product: PremiumProduct) -> PremiumProductDto:
    return PremiumProductDto(
        code=product.code,
        display_name=product.display_name,
        description=product.description,
        billing_interval=product.billing_interval,
        duration_days=product.duration_days,
        provider_price_lookup_key=product.provider_price_lookup_key,
        capability_keys=product.capability_keys,
    )


def _to_entitlement_dto(
    *,
    entitlement: EntitlementGrant,
    product: PremiumProduct | None,
    at: datetime,
) -> EntitlementGrantDto:
    display_name = product.display_name if product is not None else entitlement.product_code
    capability_keys = product.capability_keys if product is not None else ()
    return EntitlementGrantDto(
        id=entitlement.id,
        user_id=entitlement.user_id,
        product_code=entitlement.product_code,
        product_display_name=display_name,
        capability_keys=capability_keys,
        status=entitlement.effective_status(at=at),
        starts_at=entitlement.starts_at,
        ends_at=entitlement.ends_at,
        revoked_at=entitlement.revoked_at,
        revoked_reason_code=entitlement.revoked_reason_code,
    )


def _load_product(
    *,
    product_repository: ProductRepository,
    code: str,
) -> PremiumProduct | None:
    return product_repository.get_product_by_code(code=code)


def _current_access_state(
    *,
    capability_keys: tuple[str, ...],
    entitlements: tuple[EntitlementGrant, ...],
    at: datetime,
) -> AccountAccessState:
    if capability_keys:
        return "premium"
    if any(entitlement.effective_status(at=at) == "pending" for entitlement in entitlements):
        return "pending"
    return "free"
