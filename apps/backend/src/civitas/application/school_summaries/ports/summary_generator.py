from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from civitas.domain.school_summaries.models import (
    BatchGeneratedSummaryResult,
    GeneratedSummary,
    PolledSummaryBatch,
    SubmittedSummaryBatch,
    SummaryContext,
    SummaryGenerationFeedback,
    SummaryKind,
)


class SummaryGenerator(Protocol):
    def generate(
        self,
        context: SummaryContext,
        *,
        summary_kind: SummaryKind,
        feedback: SummaryGenerationFeedback | None = None,
    ) -> GeneratedSummary: ...


@runtime_checkable
class BatchSummaryGenerator(Protocol):
    def generate_batch(
        self,
        contexts: Sequence[SummaryContext],
        *,
        summary_kind: SummaryKind,
    ) -> Sequence[BatchGeneratedSummaryResult]: ...


@runtime_checkable
class AsyncBatchSummaryGenerator(Protocol):
    def batch_provider_name(self) -> str: ...

    def submit_batch(
        self,
        contexts: Sequence[SummaryContext],
        *,
        summary_kind: SummaryKind,
        provider_batch_id: str | None = None,
    ) -> SubmittedSummaryBatch: ...

    def poll_batch(
        self,
        *,
        provider_batch_id: str,
        prompt_version: str,
    ) -> PolledSummaryBatch: ...
