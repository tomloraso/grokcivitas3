from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from civitas.domain.school_summaries.models import (
    SchoolSummary,
    SummaryGenerationRun,
    SummaryGenerationRunItem,
    SummaryKind,
    SummaryRunStatus,
    SummaryTrigger,
)


class SummaryRepository(Protocol):
    def get_summary(self, urn: str, summary_kind: SummaryKind) -> SchoolSummary | None: ...

    def list_summaries(
        self,
        *,
        summary_kind: SummaryKind,
        urns: Sequence[str] | None = None,
    ) -> list[SchoolSummary]: ...

    def upsert_summary(self, summary: SchoolSummary) -> None: ...

    def upsert_summaries(self, summaries: Sequence[SchoolSummary]) -> None: ...

    def create_run(
        self,
        trigger: SummaryTrigger,
        requested_count: int,
        summary_kind: SummaryKind,
    ) -> SummaryGenerationRun: ...

    def get_run(self, run_id: UUID) -> SummaryGenerationRun | None: ...

    def list_run_items(self, run_id: UUID) -> list[SummaryGenerationRunItem]: ...

    def list_pending_batch_run_items(
        self,
        summary_kind: SummaryKind,
        run_id: UUID | None = None,
    ) -> list[SummaryGenerationRunItem]: ...

    def upsert_run_item(self, item: SummaryGenerationRunItem) -> None: ...

    def upsert_run_items(self, items: Sequence[SummaryGenerationRunItem]) -> None: ...

    def finalize_run(self, run_id: UUID, status: SummaryRunStatus) -> SummaryGenerationRun: ...
