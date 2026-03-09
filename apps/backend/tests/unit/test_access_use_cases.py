from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from civitas.application.access.use_cases import (
    EvaluateAccessUseCase,
    GetCurrentAccountAccessUseCase,
    ListAvailablePremiumProductsUseCase,
    ListUserEntitlementsUseCase,
)
from civitas.domain.access.models import EntitlementGrant, PremiumProduct

NOW = datetime(2026, 3, 9, 12, 0, tzinfo=timezone.utc)
USER_ID = UUID("e9c2d0b3-2f14-4efd-91fd-7d0ca080f19a")


class FakeEntitlementRepository:
    def __init__(self, entitlements: tuple[EntitlementGrant, ...] = ()) -> None:
        self._entitlements = entitlements
        self.list_user_calls: list[UUID] = []
        self.active_capability_calls: list[tuple[UUID, datetime]] = []

    def list_user_entitlements(self, *, user_id: UUID) -> tuple[EntitlementGrant, ...]:
        self.list_user_calls.append(user_id)
        return self._entitlements

    def list_active_capability_keys(
        self,
        *,
        user_id: UUID,
        at: datetime,
    ) -> tuple[str, ...]:
        self.active_capability_calls.append((user_id, at))
        product_codes = {
            entitlement.product_code
            for entitlement in self._entitlements
            if entitlement.user_id == user_id and entitlement.effective_status(at=at) == "active"
        }
        capability_keys: list[str] = []
        for product_code in product_codes:
            if product_code == "premium_launch":
                capability_keys.extend(
                    [
                        "premium_ai_analyst",
                        "premium_comparison",
                        "premium_neighbourhood",
                    ]
                )
        return tuple(sorted(set(capability_keys)))


class FakeProductRepository:
    def __init__(self, products: tuple[PremiumProduct, ...]) -> None:
        self._products = products
        self.list_calls = 0
        self.capability_calls: list[str] = []
        self.code_calls: list[str] = []

    def list_available_products(self) -> tuple[PremiumProduct, ...]:
        self.list_calls += 1
        return self._products

    def list_products_for_capability(
        self,
        *,
        capability_key: str,
    ) -> tuple[PremiumProduct, ...]:
        self.capability_calls.append(capability_key)
        return tuple(
            product
            for product in self._products
            if capability_key in product.capability_keys and product.is_active
        )

    def get_product_by_code(self, *, code: str) -> PremiumProduct | None:
        self.code_calls.append(code)
        for product in self._products:
            if product.code == code:
                return product
        return None


def _product(
    *,
    code: str = "premium_launch",
    capability_keys: tuple[str, ...] = (
        "premium_ai_analyst",
        "premium_comparison",
        "premium_neighbourhood",
    ),
) -> PremiumProduct:
    return PremiumProduct(
        code=code,
        display_name="Premium",
        description="Launch premium bundle",
        billing_interval=None,
        duration_days=None,
        provider_price_lookup_key=None,
        capability_keys=capability_keys,
        is_active=True,
        created_at=NOW - timedelta(days=7),
        updated_at=NOW - timedelta(days=1),
    )


def _entitlement(
    *,
    status: str = "active",
    starts_at: datetime | None = None,
    ends_at: datetime | None = None,
    revoked_at: datetime | None = None,
    revoked_reason_code: str | None = None,
) -> EntitlementGrant:
    return EntitlementGrant(
        id=uuid4(),
        user_id=USER_ID,
        product_code="premium_launch",
        status=status,
        starts_at=starts_at or (NOW - timedelta(days=1)),
        ends_at=ends_at,
        revoked_at=revoked_at,
        revoked_reason_code=revoked_reason_code,
        created_at=NOW - timedelta(days=2),
        updated_at=NOW - timedelta(hours=2),
    )


def test_entitlement_effective_status_derives_expiry_and_revocation() -> None:
    active = _entitlement(ends_at=NOW + timedelta(days=1))
    expired = _entitlement(ends_at=NOW - timedelta(seconds=1))
    pending = _entitlement(status="pending", starts_at=NOW + timedelta(hours=1))
    revoked = _entitlement(
        status="revoked",
        revoked_at=NOW - timedelta(minutes=5),
        revoked_reason_code="refund",
    )

    assert active.effective_status(at=NOW) == "active"
    assert expired.effective_status(at=NOW) == "expired"
    assert pending.effective_status(at=NOW) == "pending"
    assert revoked.effective_status(at=NOW) == "revoked"


def test_get_current_account_access_returns_anonymous_for_missing_user() -> None:
    use_case = GetCurrentAccountAccessUseCase(
        entitlement_repository=FakeEntitlementRepository(),
        product_repository=FakeProductRepository((_product(),)),
        clock=lambda: NOW,
    )

    result = use_case.execute(user_id=None)

    assert result.state == "anonymous"
    assert result.capability_keys == ()
    assert result.entitlements == ()


def test_get_current_account_access_returns_pending_before_activation() -> None:
    use_case = GetCurrentAccountAccessUseCase(
        entitlement_repository=FakeEntitlementRepository(
            (
                _entitlement(
                    status="pending",
                    starts_at=NOW + timedelta(minutes=30),
                    ends_at=NOW + timedelta(days=30),
                ),
            )
        ),
        product_repository=FakeProductRepository((_product(),)),
        clock=lambda: NOW,
    )

    result = use_case.execute(user_id=USER_ID)

    assert result.state == "pending"
    assert result.capability_keys == ()
    assert result.entitlements[0].status == "pending"
    assert result.entitlements[0].product_display_name == "Premium"


def test_get_current_account_access_returns_premium_with_capability_keys() -> None:
    use_case = GetCurrentAccountAccessUseCase(
        entitlement_repository=FakeEntitlementRepository(
            (
                _entitlement(ends_at=NOW + timedelta(days=30)),
                _entitlement(
                    status="revoked",
                    revoked_at=NOW - timedelta(days=1),
                    revoked_reason_code="refund",
                ),
            )
        ),
        product_repository=FakeProductRepository((_product(),)),
        clock=lambda: NOW,
    )

    result = use_case.execute(user_id=USER_ID)

    assert result.state == "premium"
    assert result.capability_keys == (
        "premium_ai_analyst",
        "premium_comparison",
        "premium_neighbourhood",
    )
    assert [entitlement.status for entitlement in result.entitlements] == ["active", "revoked"]


def test_evaluate_access_returns_free_for_ungated_requirement() -> None:
    use_case = EvaluateAccessUseCase(
        entitlement_repository=FakeEntitlementRepository(),
        product_repository=FakeProductRepository((_product(),)),
        clock=lambda: NOW,
    )

    result = use_case.execute(
        requirement_key="school_profile.overview",
        user_id=None,
    )

    assert result.access_level == "free"
    assert result.section_state == "available"
    assert result.reason_code == "free_baseline"
    assert result.capability_key is None
    assert result.requires_auth is False
    assert result.requires_purchase is False


def test_evaluate_access_returns_preview_only_for_anonymous_premium_viewer() -> None:
    use_case = EvaluateAccessUseCase(
        entitlement_repository=FakeEntitlementRepository(),
        product_repository=FakeProductRepository((_product(),)),
        clock=lambda: NOW,
    )

    result = use_case.execute(
        requirement_key="school_profile.ai_analyst",
        user_id=None,
    )

    assert result.access_level == "preview_only"
    assert result.section_state == "locked"
    assert result.reason_code == "anonymous_user"
    assert result.capability_key == "premium_ai_analyst"
    assert result.available_product_codes == ("premium_launch",)
    assert result.requires_auth is True
    assert result.requires_purchase is False


def test_evaluate_access_returns_preview_only_for_signed_in_user_without_capability() -> None:
    use_case = EvaluateAccessUseCase(
        entitlement_repository=FakeEntitlementRepository(),
        product_repository=FakeProductRepository((_product(),)),
        clock=lambda: NOW,
    )

    result = use_case.execute(
        requirement_key="school_compare.core",
        user_id=USER_ID,
    )

    assert result.access_level == "preview_only"
    assert result.section_state == "locked"
    assert result.reason_code == "premium_capability_missing"
    assert result.capability_key == "premium_comparison"
    assert result.requires_auth is False
    assert result.requires_purchase is True


def test_evaluate_access_can_return_strict_purchase_state_when_preview_disabled() -> None:
    use_case = EvaluateAccessUseCase(
        entitlement_repository=FakeEntitlementRepository(),
        product_repository=FakeProductRepository((_product(),)),
        clock=lambda: NOW,
    )

    result = use_case.execute(
        requirement_key="school_compare.core",
        user_id=USER_ID,
        allow_preview=False,
    )

    assert result.access_level == "requires_purchase"
    assert result.section_state == "locked"
    assert result.reason_code == "premium_capability_missing"


def test_evaluate_access_returns_premium_unlocked_for_active_capability() -> None:
    use_case = EvaluateAccessUseCase(
        entitlement_repository=FakeEntitlementRepository(
            (_entitlement(ends_at=NOW + timedelta(days=30)),)
        ),
        product_repository=FakeProductRepository((_product(),)),
        clock=lambda: NOW,
    )

    result = use_case.execute(
        requirement_key="school_profile.neighbourhood",
        user_id=USER_ID,
    )

    assert result.access_level == "premium_unlocked"
    assert result.section_state == "available"
    assert result.reason_code is None
    assert result.capability_key == "premium_neighbourhood"
    assert result.requires_purchase is False


def test_evaluate_access_prefers_revoked_and_expired_reason_codes_when_relevant() -> None:
    product_repository = FakeProductRepository((_product(),))

    expired_result = EvaluateAccessUseCase(
        entitlement_repository=FakeEntitlementRepository(
            (_entitlement(ends_at=NOW - timedelta(minutes=1)),)
        ),
        product_repository=product_repository,
        clock=lambda: NOW,
    ).execute(
        requirement_key="school_profile.ai_analyst",
        user_id=USER_ID,
    )

    revoked_result = EvaluateAccessUseCase(
        entitlement_repository=FakeEntitlementRepository(
            (
                _entitlement(
                    status="revoked",
                    revoked_at=NOW - timedelta(minutes=1),
                    revoked_reason_code="refund",
                ),
            )
        ),
        product_repository=product_repository,
        clock=lambda: NOW,
    ).execute(
        requirement_key="school_profile.ai_analyst",
        user_id=USER_ID,
    )

    assert expired_result.reason_code == "entitlement_expired"
    assert revoked_result.reason_code == "entitlement_revoked"


def test_list_available_products_returns_catalog_dto() -> None:
    use_case = ListAvailablePremiumProductsUseCase(
        product_repository=FakeProductRepository((_product(),))
    )

    result = use_case.execute()

    assert len(result) == 1
    assert result[0].code == "premium_launch"
    assert result[0].display_name == "Premium"
    assert result[0].capability_keys == (
        "premium_ai_analyst",
        "premium_comparison",
        "premium_neighbourhood",
    )


def test_list_user_entitlements_enriches_with_product_details() -> None:
    use_case = ListUserEntitlementsUseCase(
        entitlement_repository=FakeEntitlementRepository(
            (
                _entitlement(ends_at=NOW + timedelta(days=30)),
                _entitlement(ends_at=NOW - timedelta(days=1)),
            )
        ),
        product_repository=FakeProductRepository((_product(),)),
        clock=lambda: NOW,
    )

    result = use_case.execute(user_id=USER_ID)

    assert [item.status for item in result] == ["active", "expired"]
    assert all(item.product_display_name == "Premium" for item in result)
    assert all(
        item.capability_keys
        == (
            "premium_ai_analyst",
            "premium_comparison",
            "premium_neighbourhood",
        )
        for item in result
    )
