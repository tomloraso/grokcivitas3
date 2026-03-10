from __future__ import annotations

from fastapi import APIRouter, Depends

from civitas.api.dependencies import (
    get_current_account_access_use_case,
    require_authenticated_session,
)
from civitas.api.schemas.access import AccountAccessResponse, AccountEntitlementResponse
from civitas.application.access.use_cases import GetCurrentAccountAccessUseCase
from civitas.application.identity.dto import SessionUserDto

router = APIRouter(prefix="/api/v1/account", tags=["account"])


@router.get(
    "/access",
    response_model=AccountAccessResponse,
)
def get_account_access(
    user: SessionUserDto = Depends(require_authenticated_session),
    use_case: GetCurrentAccountAccessUseCase = Depends(get_current_account_access_use_case),
) -> AccountAccessResponse:
    result = use_case.execute(user_id=user.id)
    return AccountAccessResponse(
        account_access_state=result.state,
        capability_keys=list(result.capability_keys),
        access_epoch=result.access_epoch,
        entitlements=[
            AccountEntitlementResponse(
                id=entitlement.id,
                product_code=entitlement.product_code,
                product_display_name=entitlement.product_display_name,
                capability_keys=list(entitlement.capability_keys),
                status=entitlement.status,
                starts_at=entitlement.starts_at,
                ends_at=entitlement.ends_at,
                revoked_at=entitlement.revoked_at,
                revoked_reason_code=entitlement.revoked_reason_code,
            )
            for entitlement in result.entitlements
        ],
    )
