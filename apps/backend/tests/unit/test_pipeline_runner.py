import json
from datetime import datetime
from pathlib import Path
from uuid import UUID

import pytest

from civitas.infrastructure.pipelines.base import (
    PipelineCheckpoint,
    PipelineQualityConfig,
    PipelineResult,
    PipelineRunContext,
    PipelineRunStatus,
    PipelineSource,
    PipelineStep,
    StageResult,
    utc_now,
)
from civitas.infrastructure.pipelines.runner import PipelineRunner


class RecordingRunStore:
    def __init__(
        self,
        previous_successful_bronze_path: Path | None = None,
        *,
        loaded_context: PipelineRunContext | None = None,
        latest_context: PipelineRunContext | None = None,
    ) -> None:
        self.started: list[PipelineRunContext] = []
        self.finished: list[tuple[PipelineRunContext, PipelineResult, datetime]] = []
        self.previous_successful_bronze_path = previous_successful_bronze_path
        self.loaded_context = loaded_context
        self.latest_context = latest_context

    def record_started(self, context: PipelineRunContext) -> None:
        self.started.append(context)

    def record_finished(
        self,
        context: PipelineRunContext,
        result: PipelineResult,
        finished_at: datetime,
    ) -> None:
        self.finished.append((context, result, finished_at))

    def last_successful_bronze_path(
        self,
        source: PipelineSource,
        before_started_at: datetime,
    ) -> Path | None:
        _ = source, before_started_at
        return self.previous_successful_bronze_path

    def record_resumed(self, context: PipelineRunContext) -> None:
        self.started.append(context)

    def acquire_source_lock(self, *, source: PipelineSource, run_id: UUID) -> bool:
        _ = source, run_id
        return True

    def release_source_lock(self, *, source: PipelineSource, run_id: UUID) -> None:
        _ = source, run_id

    def save_checkpoint(self, checkpoint: PipelineCheckpoint) -> None:
        _ = checkpoint

    def load_checkpoints(
        self,
        *,
        run_id: UUID,
        source: PipelineSource,
    ) -> dict[PipelineStep, PipelineCheckpoint]:
        _ = run_id, source
        return {}

    def load_run_context(self, *, run_id: UUID) -> PipelineRunContext | None:
        if self.loaded_context is None:
            return None
        return self.loaded_context if self.loaded_context.run_id == run_id else None

    def latest_resumable_context(self, *, source: PipelineSource) -> PipelineRunContext | None:
        if self.latest_context is None:
            return None
        return self.latest_context if self.latest_context.source == source else None


class StubPipeline:
    source = PipelineSource.GIAS

    def __init__(
        self,
        *,
        downloaded_rows: int = 0,
        staged_rows: int = 0,
        rejected_rows: int = 0,
        promoted_rows: int = 0,
        raise_at: str | None = None,
        bronze_checksum: str | None = None,
        contract_version: str | None = None,
    ) -> None:
        self._downloaded_rows = downloaded_rows
        self._staged_rows = staged_rows
        self._rejected_rows = rejected_rows
        self._promoted_rows = promoted_rows
        self._raise_at = raise_at
        self._bronze_checksum = bronze_checksum
        self._contract_version = contract_version
        self.calls: list[str] = []

    def download(self, context: PipelineRunContext) -> int:
        self.calls.append("download")
        if self._raise_at == "download":
            raise RuntimeError("download failed")
        if self._bronze_checksum is not None:
            context.bronze_source_path.mkdir(parents=True, exist_ok=True)
            metadata_path = context.bronze_source_path / "edubasealldata.metadata.json"
            metadata_path.write_text(
                json.dumps({"sha256": self._bronze_checksum, "rows": self._downloaded_rows}),
                encoding="utf-8",
            )
        return self._downloaded_rows

    def stage(self, context: PipelineRunContext) -> StageResult:
        self.calls.append("stage")
        _ = context
        if self._raise_at == "stage":
            raise RuntimeError("stage failed")
        return StageResult(
            staged_rows=self._staged_rows,
            rejected_rows=self._rejected_rows,
            contract_version=self._contract_version,
        )

    def promote(self, context: PipelineRunContext) -> int:
        self.calls.append("promote")
        _ = context
        if self._raise_at == "promote":
            raise RuntimeError("promote failed")
        return self._promoted_rows


def _quality(max_reject_ratio: float = 1.0) -> dict[PipelineSource, PipelineQualityConfig]:
    return {PipelineSource.GIAS: PipelineQualityConfig(max_reject_ratio=max_reject_ratio)}


def test_pipeline_runner_executes_steps_and_logs_success(tmp_path: Path) -> None:
    pipeline = StubPipeline(
        downloaded_rows=12,
        staged_rows=10,
        rejected_rows=2,
        promoted_rows=10,
        bronze_checksum="abc123",
        contract_version="gias-contract-v1",
    )
    store = RecordingRunStore()
    runner = PipelineRunner(
        pipelines={PipelineSource.GIAS: pipeline},
        run_store=store,
        bronze_root=tmp_path,
        quality_config_by_source=_quality(),
    )

    result = runner.run_source(PipelineSource.GIAS)

    assert pipeline.calls == ["download", "stage", "promote"]
    assert result.status == PipelineRunStatus.SUCCEEDED
    assert result.downloaded_rows == 12
    assert result.staged_rows == 10
    assert result.promoted_rows == 10
    assert result.rejected_rows == 2
    assert result.contract_version == "gias-contract-v1"
    assert len(store.started) == 1
    assert len(store.finished) == 1
    assert store.started[0].bronze_root == tmp_path
    assert store.finished[0][0].run_id == store.started[0].run_id
    assert store.finished[0][1].status == PipelineRunStatus.SUCCEEDED


def test_pipeline_runner_fails_when_source_is_unavailable(tmp_path: Path) -> None:
    pipeline = StubPipeline(downloaded_rows=0, staged_rows=10, promoted_rows=10)
    store = RecordingRunStore()
    runner = PipelineRunner(
        pipelines={PipelineSource.GIAS: pipeline},
        run_store=store,
        bronze_root=tmp_path,
        quality_config_by_source=_quality(),
    )

    result = runner.run_source(PipelineSource.GIAS)

    assert pipeline.calls == ["download"]
    assert result.status == PipelineRunStatus.FAILED_SOURCE_UNAVAILABLE
    assert "gate_id=download_nonzero" in (result.error_message or "")
    assert result.downloaded_rows == 0
    assert result.staged_rows == 0
    assert result.promoted_rows == 0


def test_pipeline_runner_fails_when_stage_produces_no_rows(tmp_path: Path) -> None:
    pipeline = StubPipeline(
        downloaded_rows=20,
        staged_rows=0,
        rejected_rows=0,
        promoted_rows=99,
        bronze_checksum="abc123",
    )
    store = RecordingRunStore()
    runner = PipelineRunner(
        pipelines={PipelineSource.GIAS: pipeline},
        run_store=store,
        bronze_root=tmp_path,
        quality_config_by_source=_quality(),
    )

    result = runner.run_source(PipelineSource.GIAS)

    assert pipeline.calls == ["download", "stage"]
    assert result.status == PipelineRunStatus.FAILED_QUALITY_GATE
    assert "gate_id=stage_nonzero" in (result.error_message or "")
    assert result.downloaded_rows == 20
    assert result.staged_rows == 0
    assert result.promoted_rows == 0


def test_pipeline_runner_fails_when_promote_produces_no_rows(tmp_path: Path) -> None:
    pipeline = StubPipeline(
        downloaded_rows=20,
        staged_rows=15,
        rejected_rows=1,
        promoted_rows=0,
        bronze_checksum="abc123",
    )
    store = RecordingRunStore()
    runner = PipelineRunner(
        pipelines={PipelineSource.GIAS: pipeline},
        run_store=store,
        bronze_root=tmp_path,
        quality_config_by_source=_quality(),
    )

    result = runner.run_source(PipelineSource.GIAS)

    assert pipeline.calls == ["download", "stage", "promote"]
    assert result.status == PipelineRunStatus.FAILED_QUALITY_GATE
    assert "gate_id=promote_nonzero" in (result.error_message or "")
    assert result.downloaded_rows == 20
    assert result.staged_rows == 15
    assert result.promoted_rows == 0


def test_pipeline_runner_fails_when_reject_ratio_exceeds_threshold(tmp_path: Path) -> None:
    pipeline = StubPipeline(
        downloaded_rows=100,
        staged_rows=60,
        rejected_rows=45,
        promoted_rows=60,
        bronze_checksum="abc123",
    )
    store = RecordingRunStore()
    runner = PipelineRunner(
        pipelines={PipelineSource.GIAS: pipeline},
        run_store=store,
        bronze_root=tmp_path,
        quality_config_by_source=_quality(max_reject_ratio=0.4),
    )

    result = runner.run_source(PipelineSource.GIAS)

    assert pipeline.calls == ["download", "stage"]
    assert result.status == PipelineRunStatus.FAILED_QUALITY_GATE
    assert "gate_id=max_reject_ratio" in (result.error_message or "")
    assert "reject_ratio=0.450000" in (result.error_message or "")


def test_pipeline_runner_skips_when_checksum_matches_previous_success(tmp_path: Path) -> None:
    previous_bronze_path = tmp_path / "previous" / "gias" / "2026-03-02"
    previous_bronze_path.mkdir(parents=True, exist_ok=True)
    (previous_bronze_path / "edubasealldata.metadata.json").write_text(
        json.dumps({"sha256": "same-checksum", "rows": 123}),
        encoding="utf-8",
    )

    pipeline = StubPipeline(
        downloaded_rows=123,
        staged_rows=100,
        rejected_rows=0,
        promoted_rows=100,
        bronze_checksum="same-checksum",
    )
    store = RecordingRunStore(previous_successful_bronze_path=previous_bronze_path)
    runner = PipelineRunner(
        pipelines={PipelineSource.GIAS: pipeline},
        run_store=store,
        bronze_root=tmp_path / "current",
        quality_config_by_source=_quality(),
    )

    result = runner.run_source(PipelineSource.GIAS)

    assert pipeline.calls == ["download"]
    assert result.status == PipelineRunStatus.SKIPPED_NO_CHANGE
    assert result.downloaded_rows == 123
    assert result.staged_rows == 0
    assert result.promoted_rows == 0
    assert result.rejected_rows == 0
    assert result.error_message is None


def test_pipeline_runner_force_refresh_clears_same_day_bronze_and_runs_full_pipeline(
    tmp_path: Path,
) -> None:
    current_bronze_path = tmp_path / "gias" / utc_now().date().isoformat()
    current_bronze_path.mkdir(parents=True, exist_ok=True)
    stale_artifact = current_bronze_path / "stale.txt"
    stale_artifact.write_text("stale", encoding="utf-8")

    pipeline = StubPipeline(
        downloaded_rows=12,
        staged_rows=10,
        rejected_rows=1,
        promoted_rows=10,
        bronze_checksum="same-checksum",
    )
    store = RecordingRunStore(previous_successful_bronze_path=current_bronze_path)
    runner = PipelineRunner(
        pipelines={PipelineSource.GIAS: pipeline},
        run_store=store,
        bronze_root=tmp_path,
        quality_config_by_source=_quality(),
    )

    result = runner.run_source(PipelineSource.GIAS, force_refresh=True)

    assert pipeline.calls == ["download", "stage", "promote"]
    assert result.status == PipelineRunStatus.SUCCEEDED
    assert stale_artifact.exists() is False


def test_pipeline_runner_force_refresh_rejects_resume(tmp_path: Path) -> None:
    pipeline = StubPipeline(downloaded_rows=12, staged_rows=10, promoted_rows=10)
    store = RecordingRunStore()
    runner = PipelineRunner(
        pipelines={PipelineSource.GIAS: pipeline},
        run_store=store,
        bronze_root=tmp_path,
        quality_config_by_source=_quality(),
    )

    with pytest.raises(ValueError, match="force_refresh cannot be used when resume=True"):
        runner.run_source(PipelineSource.GIAS, resume=True, force_refresh=True)


def test_pipeline_runner_rejects_resumed_context_with_mismatched_bronze_root(
    tmp_path: Path,
) -> None:
    pipeline = StubPipeline(downloaded_rows=12, staged_rows=10, promoted_rows=10)
    loaded_context = PipelineRunContext(
        run_id=UUID("6f3f1a49-ecfb-4889-9efd-2913f6f821cc"),
        source=PipelineSource.GIAS,
        started_at=datetime.now().astimezone(),
        bronze_root=tmp_path / "legacy-bronze",
    )
    store = RecordingRunStore(loaded_context=loaded_context)
    runner = PipelineRunner(
        pipelines={PipelineSource.GIAS: pipeline},
        run_store=store,
        bronze_root=tmp_path / "data-bronze",
        quality_config_by_source=_quality(),
    )

    with pytest.raises(ValueError, match="does not match the configured bronze root"):
        runner.run_source(PipelineSource.GIAS, resume=True, run_id=loaded_context.run_id)


def test_pipeline_runner_logs_unexpected_failure_with_partial_counts(tmp_path: Path) -> None:
    pipeline = StubPipeline(
        downloaded_rows=3,
        staged_rows=10,
        rejected_rows=0,
        promoted_rows=10,
        raise_at="stage",
        bronze_checksum="abc123",
    )
    store = RecordingRunStore()
    runner = PipelineRunner(
        pipelines={PipelineSource.GIAS: pipeline},
        run_store=store,
        bronze_root=tmp_path,
        quality_config_by_source=_quality(),
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


def test_pipeline_runner_run_all_executes_registered_sources(tmp_path: Path) -> None:
    pipeline = StubPipeline(
        downloaded_rows=12,
        staged_rows=10,
        rejected_rows=2,
        promoted_rows=10,
        bronze_checksum="abc123",
    )
    store = RecordingRunStore()
    runner = PipelineRunner(
        pipelines={PipelineSource.GIAS: pipeline},
        run_store=store,
        bronze_root=tmp_path,
        quality_config_by_source=_quality(),
    )

    results = runner.run_all()

    assert list(results.keys()) == [PipelineSource.GIAS]
    assert results[PipelineSource.GIAS].status == PipelineRunStatus.SUCCEEDED
