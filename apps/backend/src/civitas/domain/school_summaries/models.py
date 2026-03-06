from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal
from uuid import UUID

SummaryKind = Literal["overview", "analyst"]
SummaryTrigger = Literal["pipeline", "manual"]
SummaryRunStatus = Literal["running", "succeeded", "failed", "partial"]
SummaryBatchStatus = Literal["submitted", "running", "completed", "failed", "cancelled", "expired"]
SummaryRunItemStatus = Literal[
    "submitted_batch",
    "succeeded",
    "generation_failed",
    "validation_failed",
    "skipped_current",
]


@dataclass(frozen=True)
class SchoolSummary:
    urn: str
    summary_kind: SummaryKind
    text: str
    data_version_hash: str
    prompt_version: str
    model_id: str
    generated_at: datetime
    generation_duration_ms: int | None


@dataclass(frozen=True)
class GeneratedSummary:
    text: str
    prompt_version: str
    model_id: str
    generation_duration_ms: int | None


@dataclass(frozen=True)
class BatchGeneratedSummaryResult:
    urn: str
    summary: GeneratedSummary | None
    error_code: str | None


@dataclass(frozen=True)
class SubmittedSummaryBatch:
    provider: str
    provider_batch_id: str
    prompt_version: str
    request_count: int
    submitted_at: datetime


@dataclass(frozen=True)
class PolledSummaryBatch:
    provider: str
    provider_batch_id: str
    status: SummaryBatchStatus
    results: tuple[BatchGeneratedSummaryResult, ...]
    error_code: str | None


@dataclass(frozen=True)
class SummaryGenerationFeedback:
    reason_codes: tuple[str, ...]
    previous_text: str


@dataclass(frozen=True)
class SchoolOverviewContext:
    urn: str
    name: str
    phase: str | None
    school_type: str | None
    status: str | None
    postcode: str | None
    website: str | None
    telephone: str | None
    head_name: str | None
    head_job_title: str | None
    statutory_low_age: int | None
    statutory_high_age: int | None
    gender: str | None
    religious_character: str | None
    admissions_policy: str | None
    sixth_form: str | None
    trust_name: str | None
    la_name: str | None
    urban_rural: str | None
    pupil_count: int | None
    capacity: int | None
    number_of_boys: int | None
    number_of_girls: int | None
    fsm_pct: float | None
    eal_pct: float | None
    sen_pct: float | None
    ehcp_pct: float | None
    progress_8: float | None
    attainment_8: float | None
    ks2_reading_met: float | None
    ks2_maths_met: float | None
    overall_effectiveness: str | None
    inspection_date: date | None
    imd_decile: int | None


@dataclass(frozen=True)
class MetricTrendPoint:
    year: str
    value: float | None


@dataclass(frozen=True)
class InspectionHistoryPoint:
    inspection_date: date
    overall_effectiveness: str | None


@dataclass(frozen=True)
class CrimeCategoryCount:
    category: str
    incident_count: int


@dataclass(frozen=True)
class SchoolAnalystContext(SchoolOverviewContext):
    fsm_pct_trend: tuple[MetricTrendPoint, ...] = ()
    eal_pct_trend: tuple[MetricTrendPoint, ...] = ()
    sen_pct_trend: tuple[MetricTrendPoint, ...] = ()
    progress_8_trend: tuple[MetricTrendPoint, ...] = ()
    attainment_8_trend: tuple[MetricTrendPoint, ...] = ()
    quality_of_education: str | None = None
    behaviour_and_attitudes: str | None = None
    personal_development: str | None = None
    leadership_and_management: str | None = None
    inspection_history: tuple[InspectionHistoryPoint, ...] = ()
    imd_rank: int | None = None
    idaci_decile: int | None = None
    total_incidents_12m: int | None = None
    top_crime_categories: tuple[CrimeCategoryCount, ...] = ()


SummaryContext = SchoolOverviewContext | SchoolAnalystContext


@dataclass(frozen=True)
class SummaryGenerationRun:
    id: UUID
    summary_kind: SummaryKind
    trigger: SummaryTrigger
    requested_count: int
    succeeded_count: int
    generation_failed_count: int
    validation_failed_count: int
    started_at: datetime
    completed_at: datetime | None
    status: SummaryRunStatus


@dataclass(frozen=True)
class SummaryGenerationRunItem:
    run_id: UUID
    urn: str
    status: SummaryRunItemStatus
    attempt_count: int
    failure_reason_codes: tuple[str, ...]
    completed_at: datetime | None
    data_version_hash: str | None = None
    provider_name: str | None = None
    provider_batch_id: str | None = None
    prompt_version: str | None = None
    submitted_at: datetime | None = None
