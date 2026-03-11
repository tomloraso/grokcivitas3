from typing import Protocol

from civitas.domain.subject_performance.models import (
    SchoolSubjectPerformanceLatest,
    SchoolSubjectPerformanceSeries,
)


class SubjectPerformanceRepository(Protocol):
    def get_latest_subject_performance(
        self,
        urn: str,
        *,
        include_16_to_18: bool = False,
    ) -> SchoolSubjectPerformanceLatest | None: ...

    def get_subject_performance_series(
        self,
        urn: str,
        *,
        include_16_to_18: bool = False,
    ) -> SchoolSubjectPerformanceSeries | None: ...
