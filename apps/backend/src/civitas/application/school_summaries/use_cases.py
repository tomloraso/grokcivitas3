from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Sequence
from datetime import datetime, timezone
from typing import Generic, TypeVar, cast
from uuid import UUID

from civitas.application.school_summaries.dto import SchoolSummaryDto, SummaryGenerationResultDto
from civitas.application.school_summaries.ports.summary_context_repository import (
    SummaryContextRepository,
)
from civitas.application.school_summaries.ports.summary_generator import (
    AsyncBatchSummaryGenerator,
    BatchSummaryGenerator,
    SummaryGenerator,
)
from civitas.application.school_summaries.ports.summary_repository import SummaryRepository
from civitas.domain.school_summaries.models import (
    BatchGeneratedSummaryResult,
    GeneratedSummary,
    PolledSummaryBatch,
    SchoolAnalystContext,
    SchoolOverviewContext,
    SchoolSummary,
    SummaryGenerationFeedback,
    SummaryGenerationRun,
    SummaryGenerationRunItem,
    SummaryKind,
    SummaryRunStatus,
    SummaryTrigger,
)
from civitas.domain.school_summaries.services import (
    SummaryValidationResult,
    compute_data_version_hash,
    validate_analyst_summary,
    validate_generated_summary,
)

_TERMINAL_RUN_ITEM_STATUSES = {
    "succeeded",
    "generation_failed",
    "validation_failed",
    "skipped_current",
}

ContextT = TypeVar("ContextT", SchoolOverviewContext, SchoolAnalystContext)


class _GetSchoolSummaryUseCaseBase:
    def __init__(self, *, summary_repository: SummaryRepository, summary_kind: SummaryKind) -> None:
        self._summary_repository = summary_repository
        self._summary_kind = summary_kind

    def execute(self, *, urn: str) -> SchoolSummaryDto | None:
        summary = self._summary_repository.get_summary(urn.strip(), self._summary_kind)
        if summary is None:
            return None
        return _map_summary(summary)


class GetSchoolOverviewUseCase(_GetSchoolSummaryUseCaseBase):
    def __init__(self, summary_repository: SummaryRepository) -> None:
        super().__init__(summary_repository=summary_repository, summary_kind="overview")


class GetSchoolAnalystUseCase(_GetSchoolSummaryUseCaseBase):
    def __init__(self, summary_repository: SummaryRepository) -> None:
        super().__init__(summary_repository=summary_repository, summary_kind="analyst")


class _SchoolSummaryGenerationUseCaseBase(Generic[ContextT]):
    def __init__(
        self,
        *,
        context_repository: SummaryContextRepository,
        summary_generator: SummaryGenerator,
        summary_repository: SummaryRepository,
        summary_kind: SummaryKind,
        context_loader: Callable[[Sequence[str] | None], list[ContextT]],
        validator: Callable[[str, ContextT], SummaryValidationResult],
        batch_size: int = 1,
    ) -> None:
        self._context_repository = context_repository
        self._summary_generator = summary_generator
        self._summary_repository = summary_repository
        self._summary_kind = summary_kind
        self._context_loader: Callable[[Sequence[str] | None], list[ContextT]] = context_loader
        self._validator: Callable[[str, ContextT], SummaryValidationResult] = validator
        self._batch_size = max(batch_size, 1)

    def _resolve_run(
        self,
        *,
        trigger: SummaryTrigger,
        requested_count: int,
        resume_run_id: UUID | None,
    ) -> tuple[SummaryGenerationRun, list[SummaryGenerationRunItem]]:
        if resume_run_id is None:
            run = self._summary_repository.create_run(
                trigger=trigger,
                requested_count=requested_count,
                summary_kind=self._summary_kind,
            )
            return run, []

        existing_run = self._summary_repository.get_run(resume_run_id)
        if existing_run is None:
            raise KeyError(f"No AI generation run found for run_id '{resume_run_id}'.")
        if existing_run.summary_kind != self._summary_kind:
            raise KeyError(
                f"AI generation run '{resume_run_id}' is for summary kind "
                f"'{existing_run.summary_kind}', not '{self._summary_kind}'."
            )
        existing_items = self._summary_repository.list_run_items(resume_run_id)
        return existing_run, existing_items

    def _prepare_pending_contexts(
        self,
        *,
        contexts: Sequence[ContextT],
        existing_items: Sequence[SummaryGenerationRunItem],
        current_summaries: dict[str, SchoolSummary],
        run_id: UUID,
        force: bool,
        include_submitted_as_handled: bool,
    ) -> list[tuple[ContextT, str]]:
        handled_statuses = set(_TERMINAL_RUN_ITEM_STATUSES)
        if include_submitted_as_handled:
            handled_statuses.add("submitted_batch")

        handled_by_urn = {
            item.urn: item for item in existing_items if item.status in handled_statuses
        }

        pending_contexts: list[tuple[ContextT, str]] = []
        for context in contexts:
            if context.urn in handled_by_urn:
                continue
            data_version_hash = compute_data_version_hash(context)
            current_summary = current_summaries.get(context.urn)
            if (
                not force
                and current_summary is not None
                and current_summary.data_version_hash == data_version_hash
            ):
                self._summary_repository.upsert_run_item(
                    SummaryGenerationRunItem(
                        run_id=run_id,
                        urn=context.urn,
                        status="skipped_current",
                        attempt_count=0,
                        failure_reason_codes=(),
                        completed_at=_utc_now(),
                        data_version_hash=data_version_hash,
                    )
                )
                continue
            pending_contexts.append((context, data_version_hash))

        return pending_contexts

    def _process_pending_contexts(
        self,
        *,
        run_id: UUID,
        pending_contexts: Sequence[tuple[ContextT, str]],
    ) -> None:
        if not pending_contexts:
            return

        if (
            self._batch_size > 1
            and len(pending_contexts) > 1
            and isinstance(self._summary_generator, BatchSummaryGenerator)
        ):
            batch_generator = cast(BatchSummaryGenerator, self._summary_generator)
            for chunk in _chunked(pending_contexts, self._batch_size):
                self._process_batch_chunk(
                    run_id=run_id,
                    chunk=chunk,
                    batch_generator=batch_generator,
                )
            return

        for context, data_version_hash in pending_contexts:
            self._process_context(
                run_id=run_id,
                context=context,
                data_version_hash=data_version_hash,
            )

    def _process_batch_chunk(
        self,
        *,
        run_id: UUID,
        chunk: Sequence[tuple[ContextT, str]],
        batch_generator: BatchSummaryGenerator,
    ) -> None:
        contexts = [context for context, _ in chunk]
        try:
            batch_results = batch_generator.generate_batch(
                contexts,
                summary_kind=self._summary_kind,
            )
        except Exception:
            for context, data_version_hash in chunk:
                self._process_context(
                    run_id=run_id,
                    context=context,
                    data_version_hash=data_version_hash,
                )
            return

        self._process_batch_results(
            run_id=run_id,
            chunk=chunk,
            batch_results=batch_results,
        )

    def _process_batch_results(
        self,
        *,
        run_id: UUID,
        chunk: Sequence[tuple[ContextT, str]],
        batch_results: Sequence[BatchGeneratedSummaryResult],
    ) -> None:
        results_by_urn = {result.urn: result for result in batch_results}
        for context, data_version_hash in chunk:
            batch_result = results_by_urn.get(context.urn)
            if batch_result is None or batch_result.summary is None:
                self._process_context(
                    run_id=run_id,
                    context=context,
                    data_version_hash=data_version_hash,
                )
                continue
            self._handle_generated_summary(
                run_id=run_id,
                context=context,
                data_version_hash=data_version_hash,
                generated_summary=batch_result.summary,
                attempt_count=1,
            )

    def _process_context(
        self,
        *,
        run_id: UUID,
        context: ContextT,
        data_version_hash: str,
        attempt_count: int = 1,
    ) -> None:
        try:
            first_attempt = self._summary_generator.generate(
                context,
                summary_kind=self._summary_kind,
            )
        except Exception as exc:  # pragma: no cover - exercised by unit tests with mocks
            self._record_generation_failure(
                run_id=run_id,
                urn=context.urn,
                attempt_count=attempt_count,
                reason_code=exc.__class__.__name__.casefold(),
                data_version_hash=data_version_hash,
            )
            return

        self._handle_generated_summary(
            run_id=run_id,
            context=context,
            data_version_hash=data_version_hash,
            generated_summary=first_attempt,
            attempt_count=attempt_count,
        )

    def _handle_generated_summary(
        self,
        *,
        run_id: UUID,
        context: ContextT,
        data_version_hash: str,
        generated_summary: GeneratedSummary,
        attempt_count: int,
    ) -> None:
        validation = self._validator(generated_summary.text, context)
        if validation.is_valid:
            self._persist_success(
                run_id=run_id,
                context=context,
                data_version_hash=data_version_hash,
                generated_summary=generated_summary,
                attempt_count=attempt_count,
            )
            return

        try:
            retry_summary = self._summary_generator.generate(
                context,
                summary_kind=self._summary_kind,
                feedback=SummaryGenerationFeedback(
                    reason_codes=validation.reason_codes,
                    previous_text=generated_summary.text,
                ),
            )
        except Exception as exc:  # pragma: no cover - exercised by unit tests with mocks
            self._record_generation_failure(
                run_id=run_id,
                urn=context.urn,
                attempt_count=attempt_count + 1,
                reason_code=exc.__class__.__name__.casefold(),
                data_version_hash=data_version_hash,
            )
            return

        retry_validation = self._validator(retry_summary.text, context)
        if retry_validation.is_valid:
            self._persist_success(
                run_id=run_id,
                context=context,
                data_version_hash=data_version_hash,
                generated_summary=retry_summary,
                attempt_count=attempt_count + 1,
            )
            return

        self._summary_repository.upsert_run_item(
            SummaryGenerationRunItem(
                run_id=run_id,
                urn=context.urn,
                status="validation_failed",
                attempt_count=attempt_count + 1,
                failure_reason_codes=retry_validation.reason_codes,
                completed_at=_utc_now(),
                data_version_hash=data_version_hash,
            )
        )

    def _persist_success(
        self,
        *,
        run_id: UUID,
        context: ContextT,
        data_version_hash: str,
        generated_summary: GeneratedSummary,
        attempt_count: int,
    ) -> None:
        self._summary_repository.upsert_summary(
            SchoolSummary(
                urn=context.urn,
                summary_kind=self._summary_kind,
                text=generated_summary.text.strip(),
                data_version_hash=data_version_hash,
                prompt_version=generated_summary.prompt_version,
                model_id=generated_summary.model_id,
                generated_at=_utc_now(),
                generation_duration_ms=generated_summary.generation_duration_ms,
            )
        )
        self._summary_repository.upsert_run_item(
            SummaryGenerationRunItem(
                run_id=run_id,
                urn=context.urn,
                status="succeeded",
                attempt_count=attempt_count,
                failure_reason_codes=(),
                completed_at=_utc_now(),
                data_version_hash=data_version_hash,
            )
        )

    def _record_generation_failure(
        self,
        *,
        run_id: UUID,
        urn: str,
        attempt_count: int,
        reason_code: str,
        data_version_hash: str | None = None,
    ) -> None:
        self._summary_repository.upsert_run_item(
            SummaryGenerationRunItem(
                run_id=run_id,
                urn=urn,
                status="generation_failed",
                attempt_count=attempt_count,
                failure_reason_codes=(reason_code,),
                completed_at=_utc_now(),
                data_version_hash=data_version_hash,
            )
        )

    def _build_result_for_run(self, run: SummaryGenerationRun) -> SummaryGenerationResultDto:
        items = self._summary_repository.list_run_items(run.id)
        if (
            any(item.status == "submitted_batch" for item in items)
            or len(items) < run.requested_count
        ):
            latest_run = self._summary_repository.get_run(run.id) or run
            return _build_result(latest_run, items)

        finalized_run = self._summary_repository.finalize_run(run.id, _derive_run_status(items))
        return _build_result(finalized_run, items)


class GenerateSchoolOverviewsUseCase(_SchoolSummaryGenerationUseCaseBase[SchoolOverviewContext]):
    def __init__(
        self,
        *,
        context_repository: SummaryContextRepository,
        summary_generator: SummaryGenerator,
        summary_repository: SummaryRepository,
        batch_size: int = 1,
    ) -> None:
        super().__init__(
            context_repository=context_repository,
            summary_generator=summary_generator,
            summary_repository=summary_repository,
            summary_kind="overview",
            context_loader=context_repository.list_overview_contexts,
            validator=validate_generated_summary,
            batch_size=batch_size,
        )

    def execute(
        self,
        *,
        urns: Sequence[str] | None = None,
        trigger: SummaryTrigger = "manual",
        force: bool = False,
        resume_run_id: UUID | None = None,
    ) -> SummaryGenerationResultDto:
        return _generate_summaries(
            base=self,
            urns=urns,
            trigger=trigger,
            force=force,
            resume_run_id=resume_run_id,
        )


class GenerateSchoolAnalystSummariesUseCase(
    _SchoolSummaryGenerationUseCaseBase[SchoolAnalystContext]
):
    def __init__(
        self,
        *,
        context_repository: SummaryContextRepository,
        summary_generator: SummaryGenerator,
        summary_repository: SummaryRepository,
        batch_size: int = 1,
    ) -> None:
        super().__init__(
            context_repository=context_repository,
            summary_generator=summary_generator,
            summary_repository=summary_repository,
            summary_kind="analyst",
            context_loader=context_repository.list_analyst_contexts,
            validator=validate_analyst_summary,
            batch_size=batch_size,
        )

    def execute(
        self,
        *,
        urns: Sequence[str] | None = None,
        trigger: SummaryTrigger = "manual",
        force: bool = False,
        resume_run_id: UUID | None = None,
    ) -> SummaryGenerationResultDto:
        return _generate_summaries(
            base=self,
            urns=urns,
            trigger=trigger,
            force=force,
            resume_run_id=resume_run_id,
        )


class _SchoolSummaryBatchSubmissionUseCaseBase(_SchoolSummaryGenerationUseCaseBase[ContextT]):
    def execute(
        self,
        *,
        urns: Sequence[str] | None = None,
        trigger: SummaryTrigger = "manual",
        force: bool = False,
        resume_run_id: UUID | None = None,
    ) -> SummaryGenerationResultDto:
        return _submit_summary_batches(
            base=self,
            urns=urns,
            trigger=trigger,
            force=force,
            resume_run_id=resume_run_id,
        )


class SubmitSchoolOverviewBatchesUseCase(
    _SchoolSummaryBatchSubmissionUseCaseBase[SchoolOverviewContext]
):
    def __init__(
        self,
        *,
        context_repository: SummaryContextRepository,
        summary_generator: SummaryGenerator,
        summary_repository: SummaryRepository,
        batch_size: int = 1,
    ) -> None:
        super().__init__(
            context_repository=context_repository,
            summary_generator=summary_generator,
            summary_repository=summary_repository,
            summary_kind="overview",
            context_loader=context_repository.list_overview_contexts,
            validator=validate_generated_summary,
            batch_size=batch_size,
        )


class SubmitSchoolAnalystBatchesUseCase(
    _SchoolSummaryBatchSubmissionUseCaseBase[SchoolAnalystContext]
):
    def __init__(
        self,
        *,
        context_repository: SummaryContextRepository,
        summary_generator: SummaryGenerator,
        summary_repository: SummaryRepository,
        batch_size: int = 1,
    ) -> None:
        super().__init__(
            context_repository=context_repository,
            summary_generator=summary_generator,
            summary_repository=summary_repository,
            summary_kind="analyst",
            context_loader=context_repository.list_analyst_contexts,
            validator=validate_analyst_summary,
            batch_size=batch_size,
        )


class _SchoolSummaryBatchPollingUseCaseBase(_SchoolSummaryGenerationUseCaseBase[ContextT]):
    def execute(
        self,
        *,
        run_id: UUID | None = None,
    ) -> tuple[SummaryGenerationResultDto, ...]:
        return _poll_summary_batches(base=self, run_id=run_id)


class PollSchoolOverviewBatchesUseCase(
    _SchoolSummaryBatchPollingUseCaseBase[SchoolOverviewContext]
):
    def __init__(
        self,
        *,
        context_repository: SummaryContextRepository,
        summary_generator: SummaryGenerator,
        summary_repository: SummaryRepository,
        batch_size: int = 1,
    ) -> None:
        super().__init__(
            context_repository=context_repository,
            summary_generator=summary_generator,
            summary_repository=summary_repository,
            summary_kind="overview",
            context_loader=context_repository.list_overview_contexts,
            validator=validate_generated_summary,
            batch_size=batch_size,
        )


class PollSchoolAnalystBatchesUseCase(_SchoolSummaryBatchPollingUseCaseBase[SchoolAnalystContext]):
    def __init__(
        self,
        *,
        context_repository: SummaryContextRepository,
        summary_generator: SummaryGenerator,
        summary_repository: SummaryRepository,
        batch_size: int = 1,
    ) -> None:
        super().__init__(
            context_repository=context_repository,
            summary_generator=summary_generator,
            summary_repository=summary_repository,
            summary_kind="analyst",
            context_loader=context_repository.list_analyst_contexts,
            validator=validate_analyst_summary,
            batch_size=batch_size,
        )


def _generate_summaries(
    *,
    base: _SchoolSummaryGenerationUseCaseBase[ContextT],
    urns: Sequence[str] | None,
    trigger: SummaryTrigger,
    force: bool,
    resume_run_id: UUID | None,
) -> SummaryGenerationResultDto:
    contexts = base._context_loader(urns)
    run, existing_items = base._resolve_run(
        trigger=trigger,
        requested_count=len(contexts),
        resume_run_id=resume_run_id,
    )
    current_summaries = _load_current_summaries(base=base, contexts=contexts)
    pending_contexts = base._prepare_pending_contexts(
        contexts=contexts,
        existing_items=existing_items,
        current_summaries=current_summaries,
        run_id=run.id,
        force=force,
        include_submitted_as_handled=False,
    )
    base._process_pending_contexts(
        run_id=run.id,
        pending_contexts=pending_contexts,
    )
    return base._build_result_for_run(run)


def _submit_summary_batches(
    *,
    base: _SchoolSummaryGenerationUseCaseBase[ContextT],
    urns: Sequence[str] | None,
    trigger: SummaryTrigger,
    force: bool,
    resume_run_id: UUID | None,
) -> SummaryGenerationResultDto:
    if not isinstance(base._summary_generator, AsyncBatchSummaryGenerator):
        return _generate_summaries(
            base=base,
            urns=urns,
            trigger=trigger,
            force=force,
            resume_run_id=resume_run_id,
        )

    contexts = base._context_loader(urns)
    run, existing_items = base._resolve_run(
        trigger=trigger,
        requested_count=len(contexts),
        resume_run_id=resume_run_id,
    )
    current_summaries = _load_current_summaries(base=base, contexts=contexts)
    pending_contexts = base._prepare_pending_contexts(
        contexts=contexts,
        existing_items=existing_items,
        current_summaries=current_summaries,
        run_id=run.id,
        force=force,
        include_submitted_as_handled=True,
    )

    async_generator = cast(AsyncBatchSummaryGenerator, base._summary_generator)
    for chunk in _chunked(pending_contexts, base._batch_size):
        contexts_chunk = [context for context, _ in chunk]
        try:
            submitted_batch = async_generator.submit_batch(
                contexts_chunk,
                summary_kind=base._summary_kind,
            )
        except Exception as exc:
            raise RuntimeError(
                "Async batch submission failed; resume the run after the provider issue is resolved."
            ) from exc

        for context, data_version_hash in chunk:
            base._summary_repository.upsert_run_item(
                SummaryGenerationRunItem(
                    run_id=run.id,
                    urn=context.urn,
                    status="submitted_batch",
                    attempt_count=1,
                    failure_reason_codes=(),
                    completed_at=None,
                    data_version_hash=data_version_hash,
                    provider_name=submitted_batch.provider,
                    provider_batch_id=submitted_batch.provider_batch_id,
                    prompt_version=submitted_batch.prompt_version,
                    submitted_at=submitted_batch.submitted_at,
                )
            )

    return base._build_result_for_run(run)


def _poll_summary_batches(
    *,
    base: _SchoolSummaryGenerationUseCaseBase[ContextT],
    run_id: UUID | None,
) -> tuple[SummaryGenerationResultDto, ...]:
    if not isinstance(base._summary_generator, AsyncBatchSummaryGenerator):
        return ()

    pending_items = base._summary_repository.list_pending_batch_run_items(
        base._summary_kind, run_id
    )
    if not pending_items:
        return ()

    async_generator = cast(AsyncBatchSummaryGenerator, base._summary_generator)
    pending_by_run_and_batch: dict[tuple[UUID, str, str], list[SummaryGenerationRunItem]] = (
        defaultdict(list)
    )
    for item in pending_items:
        if item.provider_batch_id is None or item.prompt_version is None:
            base._record_generation_failure(
                run_id=item.run_id,
                urn=item.urn,
                attempt_count=max(item.attempt_count, 1),
                reason_code="invalid_pending_batch_item",
                data_version_hash=item.data_version_hash,
            )
            continue
        pending_by_run_and_batch[(item.run_id, item.provider_batch_id, item.prompt_version)].append(
            item
        )

    touched_run_ids = {item.run_id for item in pending_items}
    for (
        pending_run_id,
        provider_batch_id,
        prompt_version,
    ), batch_items in pending_by_run_and_batch.items():
        polled_batch = async_generator.poll_batch(
            provider_batch_id=provider_batch_id,
            prompt_version=prompt_version,
        )
        if polled_batch.status in {"submitted", "running"}:
            continue

        contexts = base._context_loader([item.urn for item in batch_items])
        contexts_by_urn = {context.urn: context for context in contexts}
        if polled_batch.status == "completed":
            _handle_completed_polled_batch(
                base=base,
                batch_items=batch_items,
                contexts_by_urn=contexts_by_urn,
                polled_batch=polled_batch,
            )
            continue

        failure_reason = polled_batch.error_code or f"batch_{polled_batch.status}"
        for item in batch_items:
            base._record_generation_failure(
                run_id=pending_run_id,
                urn=item.urn,
                attempt_count=max(item.attempt_count, 1),
                reason_code=failure_reason,
                data_version_hash=item.data_version_hash,
            )

    results = []
    for pending_run_id in sorted(touched_run_ids, key=str):
        run = base._summary_repository.get_run(pending_run_id)
        if run is None:
            continue
        results.append(base._build_result_for_run(run))
    return tuple(results)


def _handle_completed_polled_batch(
    *,
    base: _SchoolSummaryGenerationUseCaseBase[ContextT],
    batch_items: Sequence[SummaryGenerationRunItem],
    contexts_by_urn: dict[str, ContextT],
    polled_batch: PolledSummaryBatch,
) -> None:
    results_by_urn = {result.urn: result for result in polled_batch.results}
    for item in batch_items:
        context = contexts_by_urn.get(item.urn)
        if context is None:
            base._record_generation_failure(
                run_id=item.run_id,
                urn=item.urn,
                attempt_count=max(item.attempt_count, 1),
                reason_code="missing_context",
                data_version_hash=item.data_version_hash,
            )
            continue

        batch_result = results_by_urn.get(item.urn)
        if batch_result is None:
            base._record_generation_failure(
                run_id=item.run_id,
                urn=item.urn,
                attempt_count=max(item.attempt_count, 1),
                reason_code="missing_batch_result",
                data_version_hash=item.data_version_hash,
            )
            continue

        if batch_result.summary is None:
            base._record_generation_failure(
                run_id=item.run_id,
                urn=item.urn,
                attempt_count=max(item.attempt_count, 1),
                reason_code=batch_result.error_code or polled_batch.error_code or "provider_error",
                data_version_hash=item.data_version_hash,
            )
            continue

        base._handle_generated_summary(
            run_id=item.run_id,
            context=context,
            data_version_hash=item.data_version_hash or compute_data_version_hash(context),
            generated_summary=batch_result.summary,
            attempt_count=max(item.attempt_count, 1),
        )


def _load_current_summaries(
    *,
    base: _SchoolSummaryGenerationUseCaseBase[ContextT],
    contexts: Sequence[ContextT],
) -> dict[str, SchoolSummary]:
    if not contexts:
        return {}
    current_summaries = base._summary_repository.list_summaries(
        summary_kind=base._summary_kind,
        urns=[context.urn for context in contexts],
    )
    return {summary.urn: summary for summary in current_summaries}


def _map_summary(summary: SchoolSummary) -> SchoolSummaryDto:
    return SchoolSummaryDto(
        urn=summary.urn,
        summary_kind=summary.summary_kind,
        text=summary.text,
        data_version_hash=summary.data_version_hash,
        prompt_version=summary.prompt_version,
        model_id=summary.model_id,
        generated_at=summary.generated_at,
        generation_duration_ms=summary.generation_duration_ms,
    )


def _build_result(
    run: SummaryGenerationRun,
    items: Sequence[SummaryGenerationRunItem],
) -> SummaryGenerationResultDto:
    return SummaryGenerationResultDto(
        run_id=run.id,
        requested_count=run.requested_count,
        pending_count=sum(1 for item in items if item.status == "submitted_batch"),
        succeeded_count=sum(1 for item in items if item.status == "succeeded"),
        generation_failed_count=sum(1 for item in items if item.status == "generation_failed"),
        validation_failed_count=sum(1 for item in items if item.status == "validation_failed"),
        skipped_current_count=sum(1 for item in items if item.status == "skipped_current"),
        status=run.status,
    )


def _derive_run_status(items: Sequence[SummaryGenerationRunItem]) -> SummaryRunStatus:
    successful_count = sum(1 for item in items if item.status in {"succeeded", "skipped_current"})
    failure_count = sum(
        1 for item in items if item.status in {"generation_failed", "validation_failed"}
    )
    if failure_count == 0:
        return "succeeded"
    if successful_count == 0:
        return "failed"
    return "partial"


def _chunked(
    items: Sequence[tuple[ContextT, str]],
    chunk_size: int,
) -> list[tuple[tuple[ContextT, str], ...]]:
    normalized_chunk_size = max(chunk_size, 1)
    return [
        tuple(items[index : index + normalized_chunk_size])
        for index in range(0, len(items), normalized_chunk_size)
    ]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)
