from collections.abc import Sequence
from typing import Protocol

from civitas.application.schools.dto import (
    PostcodeSchoolSearchItemDto,
    SchoolNameSearchItemDto,
)


class SchoolSearchRepository(Protocol):
    def search_within_radius(
        self,
        *,
        center_lat: float,
        center_lng: float,
        radius_miles: float,
        phase_filters: tuple[str, ...],
        sort: str,
    ) -> Sequence[PostcodeSchoolSearchItemDto]: ...

    def search_by_name(
        self,
        *,
        name: str,
        limit: int,
    ) -> Sequence[SchoolNameSearchItemDto]: ...
