from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from civitas.api.schemas.access import SectionAccessResponse


class SavedSchoolStateResponse(BaseModel):
    status: Literal["saved", "not_saved", "requires_auth", "locked"]
    saved_at: datetime | None
    capability_key: str | None
    reason_code: (
        Literal[
            "free_baseline",
            "premium_capability_missing",
            "anonymous_user",
            "artefact_not_published",
            "artefact_not_supported",
            "entitlement_expired",
            "entitlement_revoked",
        ]
        | None
    )


class FavouriteSearchLatestOfstedResponse(BaseModel):
    label: str | None
    sort_rank: int | None
    availability: str


class FavouriteSearchAcademicMetricResponse(BaseModel):
    metric_key: str | None
    label: str | None
    display_value: str | None
    sort_value: float | None
    availability: str


class AccountFavouriteSchoolResponse(BaseModel):
    urn: str
    name: str
    type: str | None
    phase: str | None
    postcode: str | None
    pupil_count: int | None
    latest_ofsted: FavouriteSearchLatestOfstedResponse
    academic_metric: FavouriteSearchAcademicMetricResponse
    saved_at: datetime


class AccountFavouritesResponse(BaseModel):
    access: SectionAccessResponse
    count: int
    schools: list[AccountFavouriteSchoolResponse] = Field(default_factory=list)
