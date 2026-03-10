from civitas.api.schemas.favourites import SavedSchoolStateResponse
from civitas.application.favourites.dto import SavedSchoolStateDto


def to_saved_school_state_response(value: SavedSchoolStateDto) -> SavedSchoolStateResponse:
    return SavedSchoolStateResponse(
        status=value.status,
        saved_at=value.saved_at,
        capability_key=value.capability_key,
        reason_code=value.reason_code,
    )
