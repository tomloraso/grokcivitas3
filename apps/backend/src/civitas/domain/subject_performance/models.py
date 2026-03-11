from dataclasses import dataclass
from datetime import datetime
from typing import Literal

SubjectPerformanceKeyStage = Literal["ks4", "16_to_18"]


@dataclass(frozen=True)
class SchoolSubjectSummary:
    academic_year: str
    key_stage: SubjectPerformanceKeyStage
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
class SchoolSubjectPerformanceGroupRow:
    academic_year: str
    key_stage: SubjectPerformanceKeyStage
    qualification_family: str
    exam_cohort: str | None
    subjects: tuple[SchoolSubjectSummary, ...]


@dataclass(frozen=True)
class SchoolSubjectPerformanceLatest:
    urn: str
    strongest_subjects: tuple[SchoolSubjectSummary, ...]
    weakest_subjects: tuple[SchoolSubjectSummary, ...]
    stage_breakdowns: tuple[SchoolSubjectPerformanceGroupRow, ...]
    latest_updated_at: datetime | None


@dataclass(frozen=True)
class SchoolSubjectPerformanceSeries:
    urn: str
    rows: tuple[SchoolSubjectPerformanceGroupRow, ...]
    latest_updated_at: datetime | None
