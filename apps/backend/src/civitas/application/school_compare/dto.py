from dataclasses import dataclass
from datetime import date

from civitas.application.access.dto import SectionAccessDto
from civitas.domain.school_compare.models import (
    CompareAvailability,
    CompareCompletenessReasonCode,
    CompareCompletenessStatus,
    CompareMetricUnit,
    CompareSectionKey,
)
from civitas.domain.school_trends.models import BenchmarkScope


@dataclass(frozen=True)
class SchoolCompareSchoolDto:
    urn: str
    name: str
    postcode: str | None
    phase: str | None
    school_type: str | None
    age_range_label: str


@dataclass(frozen=True)
class SchoolCompareBenchmarkDto:
    academic_year: str
    school_value: float | int | None
    national_value: float | None
    local_value: float | None
    school_vs_national_delta: float | None
    school_vs_local_delta: float | None
    local_scope: BenchmarkScope
    local_area_code: str
    local_area_label: str


@dataclass(frozen=True)
class SchoolCompareCellDto:
    urn: str
    value_text: str | None
    value_numeric: float | int | None
    year_label: str | None
    snapshot_date: date | None
    availability: CompareAvailability
    completeness_status: CompareCompletenessStatus
    completeness_reason_code: CompareCompletenessReasonCode | None
    benchmark: SchoolCompareBenchmarkDto | None


@dataclass(frozen=True)
class SchoolCompareRowDto:
    metric_key: str
    label: str
    unit: CompareMetricUnit
    cells: tuple[SchoolCompareCellDto, ...]


@dataclass(frozen=True)
class SchoolCompareSectionDto:
    key: CompareSectionKey
    label: str
    rows: tuple[SchoolCompareRowDto, ...]


@dataclass(frozen=True)
class SchoolCompareResponseDto:
    access: SectionAccessDto
    schools: tuple[SchoolCompareSchoolDto, ...]
    sections: tuple[SchoolCompareSectionDto, ...]
