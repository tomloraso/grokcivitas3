from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from civitas.application.access.dto import SectionAccessDto
from civitas.domain.access.value_objects import AccessDecisionReasonCode, CapabilityKey

SavedSchoolStateStatus = Literal["saved", "not_saved", "requires_auth", "locked"]


@dataclass(frozen=True)
class SavedSchoolStateDto:
    status: SavedSchoolStateStatus
    saved_at: datetime | None
    capability_key: CapabilityKey | None
    reason_code: AccessDecisionReasonCode | None


def anonymous_saved_school_state() -> SavedSchoolStateDto:
    return SavedSchoolStateDto(
        status="requires_auth",
        saved_at=None,
        capability_key=None,
        reason_code="anonymous_user",
    )


@dataclass(frozen=True)
class PostcodeSchoolSearchLatestOfstedDto:
    label: str | None
    sort_rank: int | None
    availability: str


@dataclass(frozen=True)
class PostcodeSchoolSearchAcademicMetricDto:
    metric_key: str | None
    label: str | None
    display_value: str | None
    sort_value: float | None
    availability: str


@dataclass(frozen=True)
class AccountFavouriteSchoolDto:
    urn: str
    name: str
    school_type: str | None
    phase: str | None
    postcode: str | None
    pupil_count: int | None
    latest_ofsted: PostcodeSchoolSearchLatestOfstedDto
    academic_metric: PostcodeSchoolSearchAcademicMetricDto
    saved_at: datetime


@dataclass(frozen=True)
class AccountFavouritesResponseDto:
    access: SectionAccessDto
    schools: tuple[AccountFavouriteSchoolDto, ...]

    @property
    def count(self) -> int:
        return len(self.schools)
