from typing import Protocol

from civitas.domain.school_trends.models import (
    SchoolAttendanceSeries,
    SchoolBehaviourSeries,
    SchoolDemographicsSeries,
    SchoolMetricBenchmarkSeries,
    SchoolWorkforceSeries,
)


class SchoolTrendsRepository(Protocol):
    def get_demographics_series(self, urn: str) -> SchoolDemographicsSeries | None: ...

    def get_attendance_series(self, urn: str) -> SchoolAttendanceSeries | None: ...

    def get_behaviour_series(self, urn: str) -> SchoolBehaviourSeries | None: ...

    def get_workforce_series(self, urn: str) -> SchoolWorkforceSeries | None: ...

    def get_metric_benchmark_series(self, urn: str) -> SchoolMetricBenchmarkSeries | None: ...
