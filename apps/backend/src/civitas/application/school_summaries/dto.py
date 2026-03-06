from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from civitas.domain.school_summaries.models import SummaryKind, SummaryRunStatus


@dataclass(frozen=True)
class SchoolSummaryDto:
    urn: str
    summary_kind: SummaryKind
    text: str
    data_version_hash: str
    prompt_version: str
    model_id: str
    generated_at: datetime
    generation_duration_ms: int | None


SchoolOverviewDto = SchoolSummaryDto


@dataclass(frozen=True)
class SummaryGenerationResultDto:
    run_id: UUID
    requested_count: int
    pending_count: int
    succeeded_count: int
    generation_failed_count: int
    validation_failed_count: int
    skipped_current_count: int
    status: SummaryRunStatus
