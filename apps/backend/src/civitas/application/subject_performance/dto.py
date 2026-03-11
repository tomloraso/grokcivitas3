from dataclasses import dataclass
from datetime import datetime
from typing import Literal

SubjectPerformanceKeyStageDto = Literal["ks4", "16_to_18"]


@dataclass(frozen=True)
class SchoolSubjectSummaryDto:
    academic_year: str
    key_stage: SubjectPerformanceKeyStageDto
    qualification_family: str
    exam_cohort: str | None
    subject: str
    source_version: str
    entries_count_total: int
    high_grade_count: int | None
    high_grade_share_pct: float | None
    pass_grade_count: int | None
    pass_grade_share_pct: float | None
    ranking_eligible: bool


@dataclass(frozen=True)
class SchoolSubjectPerformanceGroupRowDto:
    academic_year: str
    key_stage: SubjectPerformanceKeyStageDto
    qualification_family: str
    exam_cohort: str | None
    subjects: tuple[SchoolSubjectSummaryDto, ...]


@dataclass(frozen=True)
class SchoolSubjectPerformanceLatestDto:
    strongest_subjects: tuple[SchoolSubjectSummaryDto, ...]
    weakest_subjects: tuple[SchoolSubjectSummaryDto, ...]
    stage_breakdowns: tuple[SchoolSubjectPerformanceGroupRowDto, ...]
    latest_updated_at: datetime | None


@dataclass(frozen=True)
class SchoolSubjectPerformanceSeriesDto:
    rows: tuple[SchoolSubjectPerformanceGroupRowDto, ...]
    latest_updated_at: datetime | None
