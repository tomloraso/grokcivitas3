from collections.abc import Sequence
from typing import Protocol

from civitas.domain.schools.models import SchoolSearchResult


class SchoolSearchRepository(Protocol):
    def search_within_radius(
        self,
        *,
        center_lat: float,
        center_lng: float,
        radius_miles: float,
    ) -> Sequence[SchoolSearchResult]: ...
