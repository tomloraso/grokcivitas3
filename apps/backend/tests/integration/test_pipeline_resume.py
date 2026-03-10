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
from civitas.infrastructure.pipelines.runner import PipelineRunCleanupResult, PipelineRunner


@dataclass
class _CheckpointRecord:
    status: PipelineCheckpointStatus
    payload: dict[str, Any]
    error_message: str | None
    attempts: int
    retryable: bool


class _CheckpointingStore:
    def __init__(self) -> None:
        self.started_contexts: list[PipelineRunContext] = []
        self.finished_statuses: list[PipelineRunStatus] = []
        self.checkpoints: dict[tuple[UUID, PipelineSource, PipelineStep], _CheckpointRecord] = {}
        self.locked_sources: set[PipelineSource] = set()

    def record_started(self, context: PipelineRunContext) -> None:
        self.started_contexts.append(context)

    def record_resumed(self, context: PipelineRunContext) -> None:
        self.started_contexts.append(context)

    def record_finished(
        self,
        context: PipelineRunContext,
        result: object,
        finished_at: datetime,
    ) -> None:
        _ = context, finished_at
        self.finished_statuses.append(result.status)

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
        resolved: dict[PipelineStep, PipelineCheckpoint] = {}
        for (checkpoint_run_id, checkpoint_source, step), checkpoint in self.checkpoints.items():
            if checkpoint_run_id != run_id or checkpoint_source != source:
                continue
            resolved[step] = PipelineCheckpoint(
                run_id=checkpoint_run_id,
                source=checkpoint_source,
                step=step,
                status=checkpoint.status,
                attempts=checkpoint.attempts,
                retryable=checkpoint.retryable,
                payload=dict(checkpoint.payload),
                error_message=checkpoint.error_message,
            )
        return resolved

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


class _FlakyStagePipeline:
    source = PipelineSource.GIAS

    def __init__(self) -> None:
        self.download_calls = 0
        self.stage_calls = 0
        self.promote_calls = 0

    def download(self, context: PipelineRunContext) -> int:
        self.download_calls += 1
        context.bronze_source_path.mkdir(parents=True, exist_ok=True)
        (context.bronze_source_path / "artifact.txt").write_text("ok", encoding="utf-8")
        return 3

    def stage(self, context: PipelineRunContext) -> StageResult:
        _ = context
        self.stage_calls += 1
        if self.stage_calls == 1:
            raise RuntimeError("simulated interruption")
        return StageResult(staged_rows=3, rejected_rows=0)

    def promote(self, context: PipelineRunContext) -> int:
        _ = context
        self.promote_calls += 1
        return 3


def test_pipeline_resume_continues_from_last_checkpoint(tmp_path: Path) -> None:
    store = _CheckpointingStore()
    pipeline = _FlakyStagePipeline()
    runner = PipelineRunner(
        pipelines={PipelineSource.GIAS: pipeline},
        run_store=store,
        bronze_root=tmp_path,
    )

    first_result = runner.run_source(PipelineSource.GIAS)
    assert first_result.status == PipelineRunStatus.FAILED
    assert first_result.error_message == "simulated interruption"
    assert pipeline.download_calls == 1
    assert pipeline.stage_calls == 1
    assert pipeline.promote_calls == 0

    failed_run_id = store.started_contexts[0].run_id
    stage_checkpoint = store.checkpoints[(failed_run_id, PipelineSource.GIAS, PipelineStep.STAGE)]
    assert stage_checkpoint.status == PipelineCheckpointStatus.FAILED

    resumed_source, resumed_result = runner.resume_run(failed_run_id)
    assert resumed_source == PipelineSource.GIAS
    assert resumed_result.status == PipelineRunStatus.SUCCEEDED

    assert pipeline.download_calls == 1
    assert pipeline.stage_calls == 2
    assert pipeline.promote_calls == 1

    download_checkpoint = store.checkpoints[
        (failed_run_id, PipelineSource.GIAS, PipelineStep.DOWNLOAD)
    ]
    assert download_checkpoint.status == PipelineCheckpointStatus.COMPLETED
    assert download_checkpoint.payload["downloaded_rows"] == 3

    stage_checkpoint_after_resume = store.checkpoints[
        (failed_run_id, PipelineSource.GIAS, PipelineStep.STAGE)
    ]
    assert stage_checkpoint_after_resume.status == PipelineCheckpointStatus.COMPLETED
    assert stage_checkpoint_after_resume.payload["staged_rows"] == 3
