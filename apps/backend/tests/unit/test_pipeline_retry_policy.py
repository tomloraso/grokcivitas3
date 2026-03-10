from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from civitas.infrastructure.pipelines.base import (
    PipelineCheckpoint,
    PipelineCheckpointStatus,
    PipelineRunContext,
    PipelineRunStatus,
    PipelineSource,
    PipelineStep,
    StageResult,
)
from civitas.infrastructure.pipelines.runner import (
    PipelineRetryPolicy,
    PipelineRunCleanupResult,
    PipelineRunner,
)


@dataclass
class _CheckpointRecord:
    status: PipelineCheckpointStatus
    payload: dict[str, Any]
    error_message: str | None
    attempts: int
    retryable: bool


class _RecordingRunStore:
    def __init__(self) -> None:
        self.started_contexts: list[PipelineRunContext] = []
        self.finished: list[tuple[PipelineRunContext, object, datetime]] = []
        self.checkpoints: dict[tuple[UUID, PipelineSource, PipelineStep], _CheckpointRecord] = {}
        self.locked_sources: set[PipelineSource] = set()

    def record_started(self, context: PipelineRunContext) -> None:
        self.started_contexts.append(context)

    def record_resumed(self, context: PipelineRunContext) -> None:
        self.started_contexts.append(context)

    def record_finished(
        self, context: PipelineRunContext, result: object, finished_at: datetime
    ) -> None:
        self.finished.append((context, result, finished_at))

    def last_successful_bronze_path(
        self,
        source: PipelineSource,
        before_started_at: datetime,
    ) -> Path | None:
        _ = source, before_started_at
        return None

    def acquire_source_lock(self, *, source: PipelineSource, run_id: UUID) -> bool:
        _ = run_id
        if source in self.locked_sources:
            return False
        self.locked_sources.add(source)
        return True

    def release_source_lock(self, *, source: PipelineSource, run_id: UUID) -> None:
        _ = run_id
        self.locked_sources.discard(source)

    def save_checkpoint(self, checkpoint: PipelineCheckpoint) -> None:
        self.checkpoints[(checkpoint.run_id, checkpoint.source, checkpoint.step)] = (
            _CheckpointRecord(
                status=checkpoint.status,
                payload=dict(checkpoint.payload),
                error_message=checkpoint.error_message,
                attempts=checkpoint.attempts,
                retryable=checkpoint.retryable,
            )
        )

    def load_checkpoints(
        self,
        *,
        run_id: UUID,
        source: PipelineSource,
    ) -> dict[PipelineStep, PipelineCheckpoint]:
        checkpoints: dict[PipelineStep, PipelineCheckpoint] = {}
        for (checkpoint_run_id, checkpoint_source, step), record in self.checkpoints.items():
            if checkpoint_run_id != run_id or checkpoint_source != source:
                continue
            checkpoints[step] = PipelineCheckpoint(
                run_id=checkpoint_run_id,
                source=checkpoint_source,
                step=step,
                status=record.status,
                attempts=record.attempts,
                retryable=record.retryable,
                payload=dict(record.payload),
                error_message=record.error_message,
            )
        return checkpoints

    def load_run_context(self, *, run_id: UUID) -> PipelineRunContext | None:
        for context in self.started_contexts:
            if context.run_id == run_id:
                return context
        return None

    def latest_resumable_context(self, *, source: PipelineSource) -> PipelineRunContext | None:
        for context in reversed(self.started_contexts):
            if context.source == source:
                return context
        return None

    def cleanup_orphaned_runs(
        self,
        *,
        started_before: datetime,
        finished_at: datetime,
        source: PipelineSource | None = None,
        dry_run: bool = False,
    ) -> PipelineRunCleanupResult:
        _ = started_before, finished_at, source, dry_run
        return PipelineRunCleanupResult()


class _RetryAwarePipeline:
    source = PipelineSource.GIAS

    def __init__(
        self, *, transient_download_failures: int = 0, non_retryable_stage_failure: bool = False
    ):
        self._remaining_download_failures = transient_download_failures
        self._non_retryable_stage_failure = non_retryable_stage_failure
        self.download_calls = 0
        self.stage_calls = 0
        self.promote_calls = 0

    def download(self, context: PipelineRunContext) -> int:
        _ = context
        self.download_calls += 1
        if self._remaining_download_failures > 0:
            self._remaining_download_failures -= 1
            raise TimeoutError("source timeout")
        return 4

    def stage(self, context: PipelineRunContext) -> StageResult:
        _ = context
        self.stage_calls += 1
        if self._non_retryable_stage_failure:
            raise ValueError("schema mismatch")
        return StageResult(staged_rows=4, rejected_rows=0)

    def promote(self, context: PipelineRunContext) -> int:
        _ = context
        self.promote_calls += 1
        return 4


def test_runner_retries_transient_failures_and_succeeds(tmp_path: Path) -> None:
    pipeline = _RetryAwarePipeline(transient_download_failures=2)
    store = _RecordingRunStore()
    sleep_calls: list[float] = []
    runner = PipelineRunner(
        pipelines={PipelineSource.GIAS: pipeline},
        run_store=store,
        bronze_root=tmp_path,
        retry_policy=PipelineRetryPolicy(max_retries=2, backoff_seconds=0.1, jitter_factor=0.0),
        sleep=sleep_calls.append,
        random_fraction=lambda: 0.0,
    )

    result = runner.run_source(PipelineSource.GIAS)

    assert result.status == PipelineRunStatus.SUCCEEDED
    assert pipeline.download_calls == 3
    assert pipeline.stage_calls == 1
    assert pipeline.promote_calls == 1
    assert sleep_calls == [0.1, 0.2]

    run_id = store.started_contexts[0].run_id
    download_checkpoint = store.checkpoints[(run_id, PipelineSource.GIAS, PipelineStep.DOWNLOAD)]
    assert download_checkpoint.status == PipelineCheckpointStatus.COMPLETED
    assert download_checkpoint.attempts == 2


def test_runner_does_not_retry_non_retryable_failures(tmp_path: Path) -> None:
    pipeline = _RetryAwarePipeline(non_retryable_stage_failure=True)
    store = _RecordingRunStore()
    sleep_calls: list[float] = []
    runner = PipelineRunner(
        pipelines={PipelineSource.GIAS: pipeline},
        run_store=store,
        bronze_root=tmp_path,
        retry_policy=PipelineRetryPolicy(max_retries=5, backoff_seconds=0.1, jitter_factor=0.0),
        sleep=sleep_calls.append,
        random_fraction=lambda: 0.0,
    )

    result = runner.run_source(PipelineSource.GIAS)

    assert result.status == PipelineRunStatus.FAILED
    assert result.error_message == "schema mismatch"
    assert pipeline.download_calls == 1
    assert pipeline.stage_calls == 1
    assert pipeline.promote_calls == 0
    assert sleep_calls == []

    run_id = store.started_contexts[0].run_id
    stage_checkpoint = store.checkpoints[(run_id, PipelineSource.GIAS, PipelineStep.STAGE)]
    assert stage_checkpoint.status == PipelineCheckpointStatus.FAILED
    assert stage_checkpoint.retryable is False
    assert stage_checkpoint.attempts == 0
