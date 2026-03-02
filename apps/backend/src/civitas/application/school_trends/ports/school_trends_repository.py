from typing import Protocol

from civitas.domain.school_trends.models import SchoolDemographicsSeries


class SchoolTrendsRepository(Protocol):
    def get_demographics_series(self, urn: str) -> SchoolDemographicsSeries | None: ...
