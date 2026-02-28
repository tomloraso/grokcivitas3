from pathlib import Path

from civitas.infrastructure.pipelines.base import (
    PipelineResult,
    PipelineRunContext,
    PipelineRunStatus,
    PipelineSource,
    StageResult,
)
from civitas.infrastructure.pipelines.runner import PipelineRunner


class RecordingRunStore:
    def __init__(self) -> None:
        self.started: list[PipelineRunContext] = []
        self.finished: list[tuple[str, PipelineResult]] = []

    def record_started(self, context: PipelineRunContext) -> None:
        self.started.append(context)

    def record_finished(self, run_id: str, result: PipelineResult) -> None:
        self.finished.append((run_id, result))


class SuccessfulPipeline:
    source = PipelineSource.GIAS

    def __init__(self) -> None:
        self.calls: list[str] = []

    def download(self, context: PipelineRunContext) -> int:
        self.calls.append("download")
        return 12

    def stage(self, context: PipelineRunContext) -> StageResult:
        self.calls.append("stage")
        return StageResult(staged_rows=10, rejected_rows=2)

    def promote(self, context: PipelineRunContext) -> int:
        self.calls.append("promote")
        return 10


class FailingPipeline:
    source = PipelineSource.GIAS

    def __init__(self) -> None:
        self.calls: list[str] = []

    def download(self, context: PipelineRunContext) -> int:
        self.calls.append("download")
        return 3

    def stage(self, context: PipelineRunContext) -> StageResult:
        self.calls.append("stage")
        raise RuntimeError("stage failed")

    def promote(self, context: PipelineRunContext) -> int:
        self.calls.append("promote")
        return 0


def test_pipeline_runner_executes_steps_and_logs_success() -> None:
    pipeline = SuccessfulPipeline()
    store = RecordingRunStore()
    runner = PipelineRunner(
        pipelines={PipelineSource.GIAS: pipeline},
        run_store=store,
        bronze_root=Path("data/bronze"),
    )

    result = runner.run_source(PipelineSource.GIAS)

    assert pipeline.calls == ["download", "stage", "promote"]
    assert result.status == PipelineRunStatus.SUCCEEDED
    assert result.downloaded_rows == 12
    assert result.staged_rows == 10
    assert result.promoted_rows == 10
    assert result.rejected_rows == 2
    assert len(store.started) == 1
    assert len(store.finished) == 1
    assert store.started[0].bronze_root == Path("data/bronze")
    assert store.finished[0][0] == str(store.started[0].run_id)
    assert store.finished[0][1].status == PipelineRunStatus.SUCCEEDED


def test_pipeline_runner_logs_failure_with_partial_counts() -> None:
    pipeline = FailingPipeline()
    store = RecordingRunStore()
    runner = PipelineRunner(
        pipelines={PipelineSource.GIAS: pipeline},
        run_store=store,
        bronze_root=Path("data/bronze"),
    )

    result = runner.run_source(PipelineSource.GIAS)

    assert pipeline.calls == ["download", "stage"]
    assert result.status == PipelineRunStatus.FAILED
    assert result.error_message == "stage failed"
    assert result.downloaded_rows == 3
    assert result.staged_rows == 0
    assert result.promoted_rows == 0
    assert result.rejected_rows == 0
    assert len(store.started) == 1
    assert len(store.finished) == 1
    assert store.finished[0][1].status == PipelineRunStatus.FAILED


def test_pipeline_runner_run_all_executes_registered_sources() -> None:
    pipeline = SuccessfulPipeline()
    store = RecordingRunStore()
    runner = PipelineRunner(
        pipelines={PipelineSource.GIAS: pipeline},
        run_store=store,
        bronze_root=Path("data/bronze"),
    )

    results = runner.run_all()

    assert list(results.keys()) == [PipelineSource.GIAS]
    assert results[PipelineSource.GIAS].status == PipelineRunStatus.SUCCEEDED
