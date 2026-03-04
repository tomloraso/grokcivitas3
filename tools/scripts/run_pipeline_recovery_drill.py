"""Run a strict recovery drill against pipeline checkpoint+resume logic.

Run from repo root:
  uv run --project apps/backend python tools/scripts/run_pipeline_recovery_drill.py --strict
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
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
from civitas.infrastructure.pipelines.runner import PipelineRunner


@dataclass
class _CheckpointRecord:
    checkpoint: PipelineCheckpoint


class _DrillRunStore:
    def __init__(self) -> None:
        self.started_contexts: list[PipelineRunContext] = []
        self.finished: list[PipelineRunStatus] = []
        self._checkpoints: dict[tuple[UUID, PipelineSource, PipelineStep], _CheckpointRecord] = {}
        self._locks: set[PipelineSource] = set()

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
        self.finished.append(result.status)

    def last_successful_bronze_path(
        self,
        source: PipelineSource,
        before_started_at: datetime,
    ) -> Path | None:
        _ = source, before_started_at
        return None

    def acquire_source_lock(self, *, source: PipelineSource, run_id: UUID) -> bool:
        _ = run_id
        if source in self._locks:
            return False
        self._locks.add(source)
        return True

    def release_source_lock(self, *, source: PipelineSource, run_id: UUID) -> None:
        _ = run_id
        self._locks.discard(source)

    def save_checkpoint(self, checkpoint: PipelineCheckpoint) -> None:
        self._checkpoints[(checkpoint.run_id, checkpoint.source, checkpoint.step)] = _CheckpointRecord(
            checkpoint=checkpoint
        )

    def load_checkpoints(
        self,
        *,
        run_id: UUID,
        source: PipelineSource,
    ) -> dict[PipelineStep, PipelineCheckpoint]:
        resolved: dict[PipelineStep, PipelineCheckpoint] = {}
        for (checkpoint_run_id, checkpoint_source, step), record in self._checkpoints.items():
            if checkpoint_run_id == run_id and checkpoint_source == source:
                resolved[step] = record.checkpoint
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


class _InterruptOncePipeline:
    source = PipelineSource.GIAS

    def __init__(self, *, rows: int) -> None:
        self._rows = rows
        self.download_calls = 0
        self.stage_calls = 0
        self.promote_calls = 0

    def download(self, context: PipelineRunContext) -> int:
        self.download_calls += 1
        context.bronze_source_path.mkdir(parents=True, exist_ok=True)
        (context.bronze_source_path / "drill.artifact").write_text("ready", encoding="utf-8")
        return self._rows

    def stage(self, context: PipelineRunContext) -> StageResult:
        _ = context
        self.stage_calls += 1
        if self.stage_calls == 1:
            raise RuntimeError("recovery-drill interruption")
        return StageResult(staged_rows=self._rows, rejected_rows=0, contract_version="drill-v1")

    def promote(self, context: PipelineRunContext) -> int:
        _ = context
        self.promote_calls += 1
        return self._rows


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a pipeline recovery drill.")
    parser.add_argument("--strict", action="store_true", help="Fail when drill expectations are not met.")
    parser.add_argument("--rows", type=int, default=5000, help="Synthetic row volume for the drill.")
    return parser.parse_args(argv)


def _run_drill(*, rows: int) -> tuple[bool, dict[str, Any]]:
    store = _DrillRunStore()
    pipeline = _InterruptOncePipeline(rows=rows)

    with TemporaryDirectory(prefix="civitas-recovery-drill-") as temp_dir:
        runner = PipelineRunner(
            pipelines={PipelineSource.GIAS: pipeline},
            run_store=store,
            bronze_root=Path(temp_dir),
        )
        first = runner.run_source(PipelineSource.GIAS)
        run_id = store.started_contexts[0].run_id
        resumed_source, second = runner.resume_run(run_id)

    checkpoints = store.load_checkpoints(run_id=run_id, source=PipelineSource.GIAS)
    ok = (
        first.status == PipelineRunStatus.FAILED
        and first.error_message == "recovery-drill interruption"
        and resumed_source == PipelineSource.GIAS
        and second.status == PipelineRunStatus.SUCCEEDED
        and pipeline.download_calls == 1
        and pipeline.stage_calls == 2
        and pipeline.promote_calls == 1
        and checkpoints.get(PipelineStep.DOWNLOAD) is not None
        and checkpoints[PipelineStep.DOWNLOAD].status == PipelineCheckpointStatus.COMPLETED
        and checkpoints.get(PipelineStep.STAGE) is not None
        and checkpoints[PipelineStep.STAGE].status == PipelineCheckpointStatus.COMPLETED
        and checkpoints.get(PipelineStep.PROMOTE) is not None
        and checkpoints[PipelineStep.PROMOTE].status == PipelineCheckpointStatus.COMPLETED
    )
    return ok, {
        "run_id": str(run_id),
        "first_status": first.status.value,
        "second_status": second.status.value,
        "download_calls": pipeline.download_calls,
        "stage_calls": pipeline.stage_calls,
        "promote_calls": pipeline.promote_calls,
    }


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv or [])
    if args.rows <= 0:
        print("--rows must be greater than 0.", file=sys.stderr)
        return 2

    ok, summary = _run_drill(rows=args.rows)
    print(
        "recovery_drill "
        f"run_id={summary['run_id']} "
        f"first_status={summary['first_status']} "
        f"resumed_status={summary['second_status']} "
        f"download_calls={summary['download_calls']} "
        f"stage_calls={summary['stage_calls']} "
        f"promote_calls={summary['promote_calls']}"
    )
    if args.strict and not ok:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
