from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class SchoolSubjectSummaryResponse(BaseModel):
    academic_year: str
    key_stage: Literal["ks4", "16_to_18"]
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


class SchoolSubjectPerformanceGroupRowResponse(BaseModel):
    academic_year: str
    key_stage: Literal["ks4", "16_to_18"]
    qualification_family: str
    exam_cohort: str | None
    subjects: list[SchoolSubjectSummaryResponse] = Field(default_factory=list)


class SchoolSubjectPerformanceLatestResponse(BaseModel):
    strongest_subjects: list[SchoolSubjectSummaryResponse] = Field(default_factory=list)
    weakest_subjects: list[SchoolSubjectSummaryResponse] = Field(default_factory=list)
    stage_breakdowns: list[SchoolSubjectPerformanceGroupRowResponse] = Field(default_factory=list)
    latest_updated_at: datetime | None


class SchoolSubjectPerformanceSeriesResponse(BaseModel):
    rows: list[SchoolSubjectPerformanceGroupRowResponse] = Field(default_factory=list)
    latest_updated_at: datetime | None
