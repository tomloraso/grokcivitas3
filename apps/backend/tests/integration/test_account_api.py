from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi.testclient import TestClient

from civitas.api.dependencies import (
    get_current_account_access_use_case,
    require_authenticated_session,
)
from civitas.api.main import app
from civitas.application.access.dto import CurrentAccountAccessDto, EntitlementGrantDto
from civitas.application.identity.dto import SessionUserDto

client = TestClient(app)


class FakeCurrentAccountAccessUseCase:
    def __init__(self, result: CurrentAccountAccessDto) -> None:
        self._result = result
        self.calls: list[UUID | None] = []

    def execute(self, *, user_id: UUID | None) -> CurrentAccountAccessDto:
        self.calls.append(user_id)
        return self._result


def setup_function() -> None:
    app.dependency_overrides.clear()


def teardown_function() -> None:
    app.dependency_overrides.clear()


def test_get_account_access_returns_current_entitlements() -> None:
    user = SessionUserDto(
        id=UUID("a32d5bf0-0ec5-4dc9-bd40-636264a6fb96"),
        email="person@example.com",
    )
    fake_use_case = FakeCurrentAccountAccessUseCase(
        CurrentAccountAccessDto(
            state="premium",
            user_id=user.id,
            capability_keys=(
                "premium_ai_analyst",
                "premium_comparison",
            ),
            access_epoch="premium:premium_ai_analyst,premium_comparison",
            entitlements=(
                EntitlementGrantDto(
                    id=UUID("dcd0a7f1-521d-430f-80e5-db3be4f552a1"),
                    user_id=user.id,
                    product_code="premium_launch",
                    product_display_name="Premium",
                    capability_keys=("premium_ai_analyst", "premium_comparison"),
                    status="active",
                    starts_at=datetime(2026, 3, 1, 9, 0, tzinfo=timezone.utc),
                    ends_at=None,
                    revoked_at=None,
                    revoked_reason_code=None,
                ),
            ),
        )
    )
    app.dependency_overrides[require_authenticated_session] = lambda: user
    app.dependency_overrides[get_current_account_access_use_case] = lambda: fake_use_case

    response = client.get("/api/v1/account/access")

    assert response.status_code == 200
    assert response.json() == {
        "account_access_state": "premium",
        "capability_keys": ["premium_ai_analyst", "premium_comparison"],
        "access_epoch": "premium:premium_ai_analyst,premium_comparison",
        "entitlements": [
            {
                "id": "dcd0a7f1-521d-430f-80e5-db3be4f552a1",
                "product_code": "premium_launch",
                "product_display_name": "Premium",
                "capability_keys": ["premium_ai_analyst", "premium_comparison"],
                "status": "active",
                "starts_at": "2026-03-01T09:00:00Z",
                "ends_at": None,
                "revoked_at": None,
                "revoked_reason_code": None,
            }
        ],
    }
    assert fake_use_case.calls == [user.id]
