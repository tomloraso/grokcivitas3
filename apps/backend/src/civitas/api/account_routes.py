from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from civitas.api.dependencies import (
    get_current_account_access_use_case,
    get_list_saved_schools_use_case,
    get_remove_saved_school_use_case,
    get_save_school_use_case,
    require_authenticated_session,
    require_valid_auth_origin,
)
from civitas.api.favourites_presenter import to_saved_school_state_response
from civitas.api.schemas.access import (
    AccountAccessResponse,
    AccountEntitlementResponse,
    SectionAccessResponse,
)
from civitas.api.schemas.favourites import (
    AccountFavouriteSchoolResponse,
    AccountFavouritesResponse,
    FavouriteSearchAcademicMetricResponse,
    FavouriteSearchLatestOfstedResponse,
    SavedSchoolStateResponse,
)
from civitas.application.access.dto import SectionAccessDto
from civitas.application.access.use_cases import GetCurrentAccountAccessUseCase
from civitas.application.favourites.errors import SavedSchoolNotFoundError
from civitas.application.favourites.use_cases import (
    ListSavedSchoolsUseCase,
    RemoveSavedSchoolUseCase,
    SaveSchoolUseCase,
)
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


@router.get(
    "/favourites",
    response_model=AccountFavouritesResponse,
)
def get_account_favourites(
    user: SessionUserDto = Depends(require_authenticated_session),
    use_case: ListSavedSchoolsUseCase = Depends(get_list_saved_schools_use_case),
) -> AccountFavouritesResponse:
    result = use_case.execute(user_id=user.id)
    return AccountFavouritesResponse(
        access=_to_section_access_response(result.access),
        count=result.count,
        schools=[
            AccountFavouriteSchoolResponse(
                urn=school.urn,
                name=school.name,
                type=school.school_type,
                phase=school.phase,
                postcode=school.postcode,
                pupil_count=school.pupil_count,
                latest_ofsted=FavouriteSearchLatestOfstedResponse(
                    label=school.latest_ofsted.label,
                    sort_rank=school.latest_ofsted.sort_rank,
                    availability=school.latest_ofsted.availability,
                ),
                academic_metric=FavouriteSearchAcademicMetricResponse(
                    metric_key=school.academic_metric.metric_key,
                    label=school.academic_metric.label,
                    display_value=school.academic_metric.display_value,
                    sort_value=school.academic_metric.sort_value,
                    availability=school.academic_metric.availability,
                ),
                saved_at=school.saved_at,
            )
            for school in result.schools
        ],
    )


@router.put(
    "/favourites/{urn}",
    response_model=SavedSchoolStateResponse,
)
def save_account_favourite(
    urn: str,
    _: None = Depends(require_valid_auth_origin),
    user: SessionUserDto = Depends(require_authenticated_session),
    use_case: SaveSchoolUseCase = Depends(get_save_school_use_case),
):
    try:
        result = use_case.execute(user_id=user.id, school_urn=urn)
    except SavedSchoolNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return to_saved_school_state_response(result)


@router.delete(
    "/favourites/{urn}",
    response_model=SavedSchoolStateResponse,
)
def remove_account_favourite(
    urn: str,
    _: None = Depends(require_valid_auth_origin),
    user: SessionUserDto = Depends(require_authenticated_session),
    use_case: RemoveSavedSchoolUseCase = Depends(get_remove_saved_school_use_case),
):
    result = use_case.execute(user_id=user.id, school_urn=urn)
    return to_saved_school_state_response(result)


def _to_section_access_response(value: SectionAccessDto) -> SectionAccessResponse:
    return SectionAccessResponse(
        state=value.state,
        capability_key=value.capability_key,
        reason_code=value.reason_code,
        product_codes=list(value.product_codes),
        requires_auth=value.requires_auth,
        requires_purchase=value.requires_purchase,
        school_name=value.school_name,
    )
