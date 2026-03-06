from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from datetime import date, datetime, timezone
from uuid import UUID

import pytest

from civitas.application.school_summaries.use_cases import (
    GenerateSchoolAnalystSummariesUseCase,
    GenerateSchoolOverviewsUseCase,
    PollSchoolAnalystBatchesUseCase,
    PollSchoolOverviewBatchesUseCase,
    SubmitSchoolAnalystBatchesUseCase,
    SubmitSchoolOverviewBatchesUseCase,
)
from civitas.domain.school_summaries.models import (
    BatchGeneratedSummaryResult,
    GeneratedSummary,
    MetricTrendPoint,
    PolledSummaryBatch,
    SchoolAnalystContext,
    SchoolOverviewContext,
    SchoolSummary,
    SubmittedSummaryBatch,
    SummaryGenerationRun,
    SummaryGenerationRunItem,
)
from civitas.domain.school_summaries.services import compute_data_version_hash


class FakeSummaryContextRepository:
    def __init__(
        self,
        overview_contexts: Sequence[SchoolOverviewContext] | None = None,
        analyst_contexts: Sequence[SchoolAnalystContext] | None = None,
    ) -> None:
        self.overview_contexts = list(overview_contexts or [])
        self.analyst_contexts = list(analyst_contexts or [])

    def list_overview_contexts(
        self,
        urns: Sequence[str] | None = None,
    ) -> list[SchoolOverviewContext]:
        if urns is None:
            return list(self.overview_contexts)
        return [context for context in self.overview_contexts if context.urn in urns]

    def list_analyst_contexts(
        self,
        urns: Sequence[str] | None = None,
    ) -> list[SchoolAnalystContext]:
        if urns is None:
            return list(self.analyst_contexts)
        return [context for context in self.analyst_contexts if context.urn in urns]


class FakeSummaryGenerator:
    def __init__(self, results: Sequence[GeneratedSummary | Exception]) -> None:
        self._results = list(results)
        self.calls: list[tuple[str, str, tuple[str, ...] | None]] = []

    def generate(
        self,
        context: SchoolOverviewContext | SchoolAnalystContext,
        *,
        summary_kind: str,
        feedback=None,
    ) -> GeneratedSummary:
        self.calls.append(
            (context.urn, summary_kind, None if feedback is None else feedback.reason_codes)
        )
        result = self._results.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


class FakeBatchSummaryGenerator(FakeSummaryGenerator):
    def __init__(
        self,
        results: Sequence[GeneratedSummary | Exception],
        batch_results: Sequence[Sequence[BatchGeneratedSummaryResult] | Exception],
        async_submissions: Sequence[SubmittedSummaryBatch | Exception] | None = None,
        polled_batches: Sequence[PolledSummaryBatch | Exception] | None = None,
    ) -> None:
        super().__init__(results)
        self._batch_results = list(batch_results)
        self._async_submissions = list(async_submissions or [])
        self._polled_batches = list(polled_batches or [])
        self.batch_calls: list[tuple[str, tuple[str, ...]]] = []
        self.submit_calls: list[tuple[str, tuple[str, ...]]] = []
        self.poll_calls: list[tuple[str, str]] = []

    def generate_batch(
        self,
        contexts: Sequence[SchoolOverviewContext | SchoolAnalystContext],
        *,
        summary_kind: str,
    ) -> Sequence[BatchGeneratedSummaryResult]:
        self.batch_calls.append((summary_kind, tuple(context.urn for context in contexts)))
        result = self._batch_results.pop(0)
        if isinstance(result, Exception):
            raise result
        return result

    def batch_provider_name(self) -> str:
        return "grok"

    def submit_batch(
        self,
        contexts: Sequence[SchoolOverviewContext | SchoolAnalystContext],
        *,
        summary_kind: str,
    ) -> SubmittedSummaryBatch:
        self.submit_calls.append((summary_kind, tuple(context.urn for context in contexts)))
        result = self._async_submissions.pop(0)
        if isinstance(result, Exception):
            raise result
        return result

    def poll_batch(
        self,
        *,
        provider_batch_id: str,
        prompt_version: str,
    ) -> PolledSummaryBatch:
        self.poll_calls.append((provider_batch_id, prompt_version))
        result = self._polled_batches.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


class FakeSummaryRepository:
    def __init__(
        self,
        summaries: Sequence[SchoolSummary] | None = None,
        items: Sequence[SummaryGenerationRunItem] | None = None,
    ) -> None:
        self.summaries = {
            (summary.summary_kind, summary.urn): summary for summary in summaries or []
        }
        self.items = {(item.run_id, item.urn): item for item in items or []}
        self.runs: dict[UUID, SummaryGenerationRun] = {}

    def get_summary(self, urn: str, summary_kind: str) -> SchoolSummary | None:
        return self.summaries.get((summary_kind, urn))

    def list_summaries(
        self,
        *,
        summary_kind: str,
        urns: Sequence[str] | None = None,
    ) -> list[SchoolSummary]:
        values = [
            summary for summary in self.summaries.values() if summary.summary_kind == summary_kind
        ]
        if urns is None:
            return values
        return [summary for summary in values if summary.urn in urns]

    def upsert_summary(self, summary: SchoolSummary) -> None:
        self.summaries[(summary.summary_kind, summary.urn)] = summary

    def create_run(
        self,
        trigger: str,
        requested_count: int,
        summary_kind: str,
    ) -> SummaryGenerationRun:
        run = SummaryGenerationRun(
            id=UUID("6f3f1a49-ecfb-4889-9efd-2913f6f821cc"),
            summary_kind=summary_kind,
            trigger=trigger,
            requested_count=requested_count,
            succeeded_count=0,
            generation_failed_count=0,
            validation_failed_count=0,
            started_at=datetime(2026, 3, 6, 12, 0, tzinfo=timezone.utc),
            completed_at=None,
            status="running",
        )
        self.runs[run.id] = run
        return run

    def get_run(self, run_id: UUID) -> SummaryGenerationRun | None:
        return self.runs.get(run_id)

    def list_run_items(self, run_id: UUID) -> list[SummaryGenerationRunItem]:
        return [item for (stored_run_id, _), item in self.items.items() if stored_run_id == run_id]

    def list_pending_batch_run_items(
        self,
        summary_kind: str,
        run_id: UUID | None = None,
    ) -> list[SummaryGenerationRunItem]:
        return [
            item
            for (stored_run_id, _), item in self.items.items()
            if item.status == "submitted_batch"
            and self.runs[stored_run_id].summary_kind == summary_kind
            and (run_id is None or stored_run_id == run_id)
        ]

    def upsert_run_item(self, item: SummaryGenerationRunItem) -> None:
        existing = self.items.get((item.run_id, item.urn))
        if existing is None:
            self.items[(item.run_id, item.urn)] = item
            return

        self.items[(item.run_id, item.urn)] = replace(
            existing,
            status=item.status,
            attempt_count=item.attempt_count,
            failure_reason_codes=item.failure_reason_codes,
            completed_at=item.completed_at,
            data_version_hash=item.data_version_hash or existing.data_version_hash,
            provider_name=item.provider_name or existing.provider_name,
            provider_batch_id=item.provider_batch_id or existing.provider_batch_id,
            prompt_version=item.prompt_version or existing.prompt_version,
            submitted_at=item.submitted_at or existing.submitted_at,
        )

    def finalize_run(self, run_id: UUID, status: str) -> SummaryGenerationRun:
        items = self.list_run_items(run_id)
        run = SummaryGenerationRun(
            id=run_id,
            summary_kind=self.runs[run_id].summary_kind,
            trigger=self.runs[run_id].trigger,
            requested_count=self.runs[run_id].requested_count,
            succeeded_count=sum(1 for item in items if item.status == "succeeded"),
            generation_failed_count=sum(1 for item in items if item.status == "generation_failed"),
            validation_failed_count=sum(1 for item in items if item.status == "validation_failed"),
            started_at=self.runs[run_id].started_at,
            completed_at=datetime(2026, 3, 6, 12, 1, tzinfo=timezone.utc),
            status=status,
        )
        self.runs[run_id] = run
        return run


def test_generate_school_overviews_skips_current_summary() -> None:
    context = _context()
    repository = FakeSummaryRepository(summaries=[_stored_summary()])
    result = GenerateSchoolOverviewsUseCase(
        context_repository=FakeSummaryContextRepository(overview_contexts=[context]),
        summary_generator=FakeSummaryGenerator([]),
        summary_repository=repository,
    ).execute()

    assert result.skipped_current_count == 1
    assert repository.list_run_items(result.run_id)[0].status == "skipped_current"


def test_generate_school_overviews_retries_after_validation_failure() -> None:
    repository = FakeSummaryRepository()
    generator = FakeSummaryGenerator(
        [
            GeneratedSummary(
                text="Too short.",
                prompt_version="overview.v1",
                model_id="test-model",
                generation_duration_ms=100,
            ),
            GeneratedSummary(
                text=_valid_text(),
                prompt_version="overview.v1",
                model_id="test-model",
                generation_duration_ms=120,
            ),
        ]
    )
    result = GenerateSchoolOverviewsUseCase(
        context_repository=FakeSummaryContextRepository(overview_contexts=[_context()]),
        summary_generator=generator,
        summary_repository=repository,
    ).execute()

    assert result.succeeded_count == 1
    assert generator.calls[1][2] == ("word_count_too_short",)
    assert repository.get_summary("100001", "overview") is not None


def test_generate_school_overviews_records_validation_failure_after_retry() -> None:
    repository = FakeSummaryRepository()
    generator = FakeSummaryGenerator(
        [
            GeneratedSummary(
                text="Too short.",
                prompt_version="overview.v1",
                model_id="test-model",
                generation_duration_ms=100,
            ),
            GeneratedSummary(
                text="Still too short.",
                prompt_version="overview.v1",
                model_id="test-model",
                generation_duration_ms=110,
            ),
        ]
    )
    result = GenerateSchoolOverviewsUseCase(
        context_repository=FakeSummaryContextRepository(overview_contexts=[_context()]),
        summary_generator=generator,
        summary_repository=repository,
    ).execute()

    assert result.validation_failed_count == 1
    assert repository.get_summary("100001", "overview") is None


def test_generate_school_overviews_uses_batch_generation_when_available() -> None:
    repository = FakeSummaryRepository()
    generator = FakeBatchSummaryGenerator(
        results=[],
        batch_results=[
            [
                BatchGeneratedSummaryResult(
                    urn="100001",
                    summary=GeneratedSummary(
                        text=_valid_text(),
                        prompt_version="overview.v1",
                        model_id="test-model",
                        generation_duration_ms=100,
                    ),
                    error_code=None,
                ),
                BatchGeneratedSummaryResult(
                    urn="100002",
                    summary=GeneratedSummary(
                        text=_valid_text().replace("Test School", "Second School"),
                        prompt_version="overview.v1",
                        model_id="test-model",
                        generation_duration_ms=110,
                    ),
                    error_code=None,
                ),
            ]
        ],
    )
    contexts = [_context(), _context(urn="100002", name="Second School")]

    result = GenerateSchoolOverviewsUseCase(
        context_repository=FakeSummaryContextRepository(overview_contexts=contexts),
        summary_generator=generator,
        summary_repository=repository,
        batch_size=10,
    ).execute()

    assert result.succeeded_count == 2
    assert generator.batch_calls == [("overview", ("100001", "100002"))]
    assert generator.calls == []
    assert repository.get_summary("100002", "overview") is not None


def test_generate_school_overviews_falls_back_to_individual_requests_when_batch_fails() -> None:
    repository = FakeSummaryRepository()
    generator = FakeBatchSummaryGenerator(
        results=[
            GeneratedSummary(
                text=_valid_text(),
                prompt_version="overview.v1",
                model_id="test-model",
                generation_duration_ms=100,
            ),
            GeneratedSummary(
                text=_valid_text().replace("Test School", "Second School"),
                prompt_version="overview.v1",
                model_id="test-model",
                generation_duration_ms=110,
            ),
        ],
        batch_results=[RuntimeError("batch unavailable")],
    )
    contexts = [_context(), _context(urn="100002", name="Second School")]

    result = GenerateSchoolOverviewsUseCase(
        context_repository=FakeSummaryContextRepository(overview_contexts=contexts),
        summary_generator=generator,
        summary_repository=repository,
        batch_size=10,
    ).execute()

    assert result.succeeded_count == 2
    assert generator.batch_calls == [("overview", ("100001", "100002"))]
    assert [(call[0], call[1]) for call in generator.calls] == [
        ("100001", "overview"),
        ("100002", "overview"),
    ]


def test_generate_school_overviews_falls_back_to_individual_requests_for_partial_batch_results() -> (
    None
):
    repository = FakeSummaryRepository()
    generator = FakeBatchSummaryGenerator(
        results=[
            GeneratedSummary(
                text=_valid_text().replace("Test School", "Second School"),
                prompt_version="overview.v1",
                model_id="test-model",
                generation_duration_ms=110,
            ),
        ],
        batch_results=[
            [
                BatchGeneratedSummaryResult(
                    urn="100001",
                    summary=GeneratedSummary(
                        text=_valid_text(),
                        prompt_version="overview.v1",
                        model_id="test-model",
                        generation_duration_ms=100,
                    ),
                    error_code=None,
                ),
                BatchGeneratedSummaryResult(
                    urn="100002",
                    summary=None,
                    error_code="provider_error",
                ),
            ]
        ],
    )
    contexts = [_context(), _context(urn="100002", name="Second School")]

    result = GenerateSchoolOverviewsUseCase(
        context_repository=FakeSummaryContextRepository(overview_contexts=contexts),
        summary_generator=generator,
        summary_repository=repository,
        batch_size=10,
    ).execute()

    assert result.succeeded_count == 2
    assert generator.batch_calls == [("overview", ("100001", "100002"))]
    assert [(call[0], call[1]) for call in generator.calls] == [("100002", "overview")]


def test_submit_school_overview_batches_marks_chunk_as_pending() -> None:
    repository = FakeSummaryRepository()
    generator = FakeBatchSummaryGenerator(
        results=[],
        batch_results=[],
        async_submissions=[
            SubmittedSummaryBatch(
                provider="grok",
                provider_batch_id="batch-1",
                prompt_version="overview.v1",
                request_count=2,
                submitted_at=datetime(2026, 3, 6, 12, 0, tzinfo=timezone.utc),
            )
        ],
    )
    contexts = [_context(), _context(urn="100002", name="Second School")]

    result = SubmitSchoolOverviewBatchesUseCase(
        context_repository=FakeSummaryContextRepository(overview_contexts=contexts),
        summary_generator=generator,
        summary_repository=repository,
        batch_size=10,
    ).execute()

    assert result.status == "running"
    assert result.pending_count == 2
    assert generator.submit_calls == [("overview", ("100001", "100002"))]
    pending_items = repository.list_pending_batch_run_items("overview", result.run_id)
    assert [item.provider_batch_id for item in pending_items] == ["batch-1", "batch-1"]


def test_submit_school_overview_batches_fails_fast_when_async_submission_errors() -> None:
    repository = FakeSummaryRepository()
    generator = FakeBatchSummaryGenerator(
        results=[],
        batch_results=[],
        async_submissions=[RuntimeError("provider unavailable")],
    )
    contexts = [_context(), _context(urn="100002", name="Second School")]

    with pytest.raises(
        RuntimeError,
        match="Async batch submission failed; resume the run after the provider issue is resolved.",
    ):
        SubmitSchoolOverviewBatchesUseCase(
            context_repository=FakeSummaryContextRepository(overview_contexts=contexts),
            summary_generator=generator,
            summary_repository=repository,
            batch_size=10,
        ).execute()

    assert generator.submit_calls == [("overview", ("100001", "100002"))]
    assert generator.calls == []
    run = next(iter(repository.runs.values()))
    assert run.status == "running"
    assert repository.list_run_items(run.id) == []


def test_poll_school_overview_batches_finalizes_completed_batch() -> None:
    repository = FakeSummaryRepository()
    generator = FakeBatchSummaryGenerator(
        results=[],
        batch_results=[],
        async_submissions=[
            SubmittedSummaryBatch(
                provider="grok",
                provider_batch_id="batch-1",
                prompt_version="overview.v1",
                request_count=2,
                submitted_at=datetime(2026, 3, 6, 12, 0, tzinfo=timezone.utc),
            )
        ],
        polled_batches=[
            PolledSummaryBatch(
                provider="grok",
                provider_batch_id="batch-1",
                status="completed",
                results=(
                    BatchGeneratedSummaryResult(
                        urn="100001",
                        summary=GeneratedSummary(
                            text=_valid_text(),
                            prompt_version="overview.v1",
                            model_id="test-model",
                            generation_duration_ms=None,
                        ),
                        error_code=None,
                    ),
                    BatchGeneratedSummaryResult(
                        urn="100002",
                        summary=GeneratedSummary(
                            text=_valid_text().replace("Test School", "Second School"),
                            prompt_version="overview.v1",
                            model_id="test-model",
                            generation_duration_ms=None,
                        ),
                        error_code=None,
                    ),
                ),
                error_code=None,
            )
        ],
    )
    contexts = [_context(), _context(urn="100002", name="Second School")]

    submitted = SubmitSchoolOverviewBatchesUseCase(
        context_repository=FakeSummaryContextRepository(overview_contexts=contexts),
        summary_generator=generator,
        summary_repository=repository,
        batch_size=10,
    ).execute()
    results = PollSchoolOverviewBatchesUseCase(
        context_repository=FakeSummaryContextRepository(overview_contexts=contexts),
        summary_generator=generator,
        summary_repository=repository,
        batch_size=10,
    ).execute(run_id=submitted.run_id)

    assert generator.poll_calls == [("batch-1", "overview.v1")]
    assert len(results) == 1
    assert results[0].pending_count == 0
    assert results[0].succeeded_count == 2
    assert repository.get_summary("100001", "overview") is not None


def test_poll_school_overview_batches_keeps_run_running_until_all_requested_items_exist() -> None:
    repository = FakeSummaryRepository()
    generator = FakeBatchSummaryGenerator(
        results=[],
        batch_results=[],
        async_submissions=[
            SubmittedSummaryBatch(
                provider="grok",
                provider_batch_id="batch-1",
                prompt_version="overview.v1",
                request_count=2,
                submitted_at=datetime(2026, 3, 6, 12, 0, tzinfo=timezone.utc),
            )
        ],
        polled_batches=[
            PolledSummaryBatch(
                provider="grok",
                provider_batch_id="batch-1",
                status="completed",
                results=(
                    BatchGeneratedSummaryResult(
                        urn="100001",
                        summary=GeneratedSummary(
                            text=_valid_text(),
                            prompt_version="overview.v1",
                            model_id="test-model",
                            generation_duration_ms=None,
                        ),
                        error_code=None,
                    ),
                    BatchGeneratedSummaryResult(
                        urn="100002",
                        summary=GeneratedSummary(
                            text=_valid_text().replace("Test School", "Second School"),
                            prompt_version="overview.v1",
                            model_id="test-model",
                            generation_duration_ms=None,
                        ),
                        error_code=None,
                    ),
                ),
                error_code=None,
            )
        ],
    )
    contexts = [_context(), _context(urn="100002", name="Second School")]

    submitted = SubmitSchoolOverviewBatchesUseCase(
        context_repository=FakeSummaryContextRepository(overview_contexts=contexts),
        summary_generator=generator,
        summary_repository=repository,
        batch_size=10,
    ).execute()
    repository.runs[submitted.run_id] = replace(
        repository.runs[submitted.run_id], requested_count=3
    )

    results = PollSchoolOverviewBatchesUseCase(
        context_repository=FakeSummaryContextRepository(overview_contexts=contexts),
        summary_generator=generator,
        summary_repository=repository,
        batch_size=10,
    ).execute(run_id=submitted.run_id)

    assert len(results) == 1
    assert results[0].status == "running"
    assert results[0].pending_count == 0
    assert results[0].succeeded_count == 2
    assert repository.get_run(submitted.run_id).status == "running"


def test_poll_school_overview_batches_preserves_batch_metadata_on_validation_failure() -> None:
    repository = FakeSummaryRepository()
    generator = FakeBatchSummaryGenerator(
        results=[
            GeneratedSummary(
                text="Retry output still names the wrong place and remains invalid.",
                prompt_version="overview.v1",
                model_id="test-model",
                generation_duration_ms=50,
            )
        ],
        batch_results=[],
        async_submissions=[
            SubmittedSummaryBatch(
                provider="grok",
                provider_batch_id="batch-1",
                prompt_version="overview.v1",
                request_count=1,
                submitted_at=datetime(2026, 3, 6, 12, 0, tzinfo=timezone.utc),
            )
        ],
        polled_batches=[
            PolledSummaryBatch(
                provider="grok",
                provider_batch_id="batch-1",
                status="completed",
                results=(
                    BatchGeneratedSummaryResult(
                        urn="100001",
                        summary=GeneratedSummary(
                            text="Too short.",
                            prompt_version="overview.v1",
                            model_id="test-model",
                            generation_duration_ms=None,
                        ),
                        error_code=None,
                    ),
                ),
                error_code=None,
            )
        ],
    )

    submitted = SubmitSchoolOverviewBatchesUseCase(
        context_repository=FakeSummaryContextRepository(overview_contexts=[_context()]),
        summary_generator=generator,
        summary_repository=repository,
        batch_size=10,
    ).execute()
    PollSchoolOverviewBatchesUseCase(
        context_repository=FakeSummaryContextRepository(overview_contexts=[_context()]),
        summary_generator=generator,
        summary_repository=repository,
        batch_size=10,
    ).execute(run_id=submitted.run_id)

    item = repository.list_run_items(submitted.run_id)[0]
    assert item.status == "validation_failed"
    assert item.provider_name == "grok"
    assert item.provider_batch_id == "batch-1"
    assert item.prompt_version == "overview.v1"


def test_generate_school_analyst_summaries_uses_analyst_kind() -> None:
    repository = FakeSummaryRepository()
    generator = FakeSummaryGenerator(
        [
            GeneratedSummary(
                text=_valid_analyst_text(),
                prompt_version="analyst.v1",
                model_id="test-model",
                generation_duration_ms=100,
            )
        ]
    )

    result = GenerateSchoolAnalystSummariesUseCase(
        context_repository=FakeSummaryContextRepository(analyst_contexts=[_analyst_context()]),
        summary_generator=generator,
        summary_repository=repository,
    ).execute()

    assert result.succeeded_count == 1
    assert generator.calls == [("100001", "analyst", None)]
    assert repository.get_summary("100001", "analyst") is not None


def test_submit_and_poll_school_analyst_batches_use_analyst_kind() -> None:
    repository = FakeSummaryRepository()
    generator = FakeBatchSummaryGenerator(
        results=[],
        batch_results=[],
        async_submissions=[
            SubmittedSummaryBatch(
                provider="grok",
                provider_batch_id="batch-analyst-1",
                prompt_version="analyst.v1",
                request_count=1,
                submitted_at=datetime(2026, 3, 6, 12, 0, tzinfo=timezone.utc),
            )
        ],
        polled_batches=[
            PolledSummaryBatch(
                provider="grok",
                provider_batch_id="batch-analyst-1",
                status="completed",
                results=(
                    BatchGeneratedSummaryResult(
                        urn="100001",
                        summary=GeneratedSummary(
                            text=_valid_analyst_text(),
                            prompt_version="analyst.v1",
                            model_id="test-model",
                            generation_duration_ms=None,
                        ),
                        error_code=None,
                    ),
                ),
                error_code=None,
            )
        ],
    )

    submitted = SubmitSchoolAnalystBatchesUseCase(
        context_repository=FakeSummaryContextRepository(analyst_contexts=[_analyst_context()]),
        summary_generator=generator,
        summary_repository=repository,
        batch_size=10,
    ).execute()
    results = PollSchoolAnalystBatchesUseCase(
        context_repository=FakeSummaryContextRepository(analyst_contexts=[_analyst_context()]),
        summary_generator=generator,
        summary_repository=repository,
        batch_size=10,
    ).execute(run_id=submitted.run_id)

    assert generator.submit_calls == [("analyst", ("100001",))]
    assert generator.poll_calls == [("batch-analyst-1", "analyst.v1")]
    assert len(results) == 1
    assert results[0].succeeded_count == 1
    assert repository.get_summary("100001", "analyst") is not None


def _context(*, urn: str = "100001", name: str = "Test School") -> SchoolOverviewContext:
    return SchoolOverviewContext(
        urn=urn,
        name=name,
        phase="Secondary",
        school_type="Academy",
        status="Open",
        postcode="SW1A 1AA",
        website="https://example.test",
        telephone="020 7946 0999",
        head_name="Alex Smith",
        head_job_title="Headteacher",
        statutory_low_age=11,
        statutory_high_age=16,
        gender="Mixed",
        religious_character=None,
        admissions_policy="Not applicable",
        sixth_form="Does not have a sixth form",
        trust_name="Example Trust",
        la_name="Westminster",
        urban_rural="Urban city and town",
        pupil_count=900,
        capacity=1000,
        number_of_boys=450,
        number_of_girls=450,
        fsm_pct=18.2,
        eal_pct=22.4,
        sen_pct=14.0,
        ehcp_pct=3.1,
        progress_8=0.31,
        attainment_8=51.2,
        ks2_reading_met=None,
        ks2_maths_met=None,
        overall_effectiveness="Good",
        inspection_date=date(2024, 1, 10),
        imd_decile=7,
    )


def _stored_summary() -> SchoolSummary:
    context = _context()
    return SchoolSummary(
        urn=context.urn,
        summary_kind="overview",
        text=_valid_text(),
        data_version_hash=compute_data_version_hash(context),
        prompt_version="overview.v1",
        model_id="test-model",
        generated_at=datetime(2026, 3, 6, 11, 0, tzinfo=timezone.utc),
        generation_duration_ms=100,
    )


def _valid_text() -> str:
    return (
        "Test School is an open secondary academy in Westminster for pupils aged 11 to 16. "
        "It operates in an urban city and town setting and has about 900 pupils on roll against "
        "reported capacity of 1,000, with an even split between boys and girls. Published pupil "
        "indicators show free school meals at 18.2%, English as an additional language at 22.4%, "
        "special educational needs at 14.0%, and EHCP at 3.1%. The latest published performance "
        "figures show Progress 8 at 0.31 and Attainment 8 at 51.2. Ofsted rated the school Good "
        "following an inspection on 2024-01-10. The school is part of Example Trust, does not "
        "have a sixth form, and sits in an area with IMD decile 7 according to the available "
        "context used to generate this overview."
    )


def _analyst_context() -> SchoolAnalystContext:
    return SchoolAnalystContext(
        **_context().__dict__,
        fsm_pct_trend=(
            MetricTrendPoint(year="2022/23", value=19.1),
            MetricTrendPoint(year="2023/24", value=18.7),
            MetricTrendPoint(year="2024/25", value=18.2),
        ),
        eal_pct_trend=(
            MetricTrendPoint(year="2022/23", value=21.8),
            MetricTrendPoint(year="2023/24", value=22.0),
            MetricTrendPoint(year="2024/25", value=22.4),
        ),
        sen_pct_trend=(
            MetricTrendPoint(year="2022/23", value=13.3),
            MetricTrendPoint(year="2023/24", value=13.7),
            MetricTrendPoint(year="2024/25", value=14.0),
        ),
        progress_8_trend=(
            MetricTrendPoint(year="2022/23", value=0.12),
            MetricTrendPoint(year="2023/24", value=0.21),
            MetricTrendPoint(year="2024/25", value=0.31),
        ),
        attainment_8_trend=(
            MetricTrendPoint(year="2022/23", value=49.6),
            MetricTrendPoint(year="2023/24", value=50.5),
            MetricTrendPoint(year="2024/25", value=51.2),
        ),
        quality_of_education="Good",
        behaviour_and_attitudes="Good",
        personal_development="Good",
        leadership_and_management="Good",
        imd_rank=4825,
        idaci_decile=2,
        total_incidents_12m=486,
    )


def _valid_analyst_text() -> str:
    return (
        "Test School presents a broadly steady published profile rather than a sharply uneven one. "
        "The latest secondary performance figures show Progress 8 at 0.31 and Attainment 8 at "
        "51.2, and the available trend points indicate both measures have moved up over the recent "
        "published years rather than slipping back. Ofsted rated the school Good following an "
        "inspection on 2024-01-10, which keeps the inspection picture aligned with the current "
        "performance profile. Published pupil indicators show FSM at 18.2%, EAL at 22.4%, SEN at "
        "14.0%, and EHCP at 3.1%, suggesting a mixed intake with a moderate level of additional "
        "need in the available data. The school operates in an urban Westminster setting, is part "
        "of Example Trust, and sits in IMD decile 7 with 486 incidents recorded across the latest "
        "12 months of local crime context. Overall, the current dataset points to a balanced school "
        "profile with credible strengths and no single dominant warning signal in the published "
        "evidence."
    )
