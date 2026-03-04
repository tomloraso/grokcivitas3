"""Benchmark pipeline throughput using a deterministic synthetic workload.

Run from repo root:
  uv run --project apps/backend python tools/scripts/benchmark_pipeline_throughput.py --strict
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter
from uuid import UUID

from civitas.infrastructure.pipelines.base import (
    PipelineCheckpoint,
    PipelineRunContext,
    PipelineRunStatus,
    PipelineSource,
    PipelineStep,
    StageResult,
)
from civitas.infrastructure.pipelines.runner import PipelineRunner


class _BenchmarkStore:
    def __init__(self) -> None:
        self.started_contexts: list[PipelineRunContext] = []
        self._checkpoints: dict[tuple[UUID, PipelineSource, PipelineStep], PipelineCheckpoint] = {}

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
        _ = context, result, finished_at

    def last_successful_bronze_path(
        self,
        source: PipelineSource,
        before_started_at: datetime,
    ) -> Path | None:
        _ = source, before_started_at
        return None

    def acquire_source_lock(self, *, source: PipelineSource, run_id: UUID) -> bool:
        _ = source, run_id
        return True

    def release_source_lock(self, *, source: PipelineSource, run_id: UUID) -> None:
        _ = source, run_id

    def save_checkpoint(self, checkpoint: PipelineCheckpoint) -> None:
        self._checkpoints[(checkpoint.run_id, checkpoint.source, checkpoint.step)] = checkpoint

    def load_checkpoints(
        self,
        *,
        run_id: UUID,
        source: PipelineSource,
    ) -> dict[PipelineStep, PipelineCheckpoint]:
        resolved: dict[PipelineStep, PipelineCheckpoint] = {}
        for (checkpoint_run_id, checkpoint_source, step), checkpoint in self._checkpoints.items():
            if checkpoint_run_id == run_id and checkpoint_source == source:
                resolved[step] = checkpoint
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


@dataclass(frozen=True)
class _BenchmarkMetrics:
    duration_seconds: float
    rows_per_second: float
    downloaded_rows: int
    staged_rows: int
    promoted_rows: int
    status: PipelineRunStatus


class _ThroughputPipeline:
    source = PipelineSource.GIAS

    def __init__(self, *, rows: int) -> None:
        self._rows = rows

    def download(self, context: PipelineRunContext) -> int:
        context.bronze_source_path.mkdir(parents=True, exist_ok=True)
        (context.bronze_source_path / "throughput.artifact").write_text("ready", encoding="utf-8")
        return self._rows

    def stage(self, context: PipelineRunContext) -> StageResult:
        _ = context
        accepted_rows = 0
        for _ in range(self._rows):
            accepted_rows += 1
        return StageResult(staged_rows=accepted_rows, rejected_rows=0, contract_version="bench-v1")

    def promote(self, context: PipelineRunContext) -> int:
        _ = context
        promoted_rows = 0
        for _ in range(self._rows):
            promoted_rows += 1
        return promoted_rows


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark pipeline throughput.")
    parser.add_argument("--strict", action="store_true", help="Enforce thresholds as hard gates.")
    parser.add_argument("--rows", type=int, default=50000, help="Synthetic rows to process.")
    parser.add_argument(
        "--min-rows-per-second",
        type=float,
        default=5000.0,
        help="Minimum acceptable throughput.",
    )
    parser.add_argument(
        "--max-duration-seconds",
        type=float,
        default=30.0,
        help="Maximum acceptable runtime.",
    )
    return parser.parse_args(argv)


def _run_benchmark(*, rows: int) -> _BenchmarkMetrics:
    store = _BenchmarkStore()
    pipeline = _ThroughputPipeline(rows=rows)
    with TemporaryDirectory(prefix="civitas-throughput-benchmark-") as temp_dir:
        runner = PipelineRunner(
            pipelines={PipelineSource.GIAS: pipeline},
            run_store=store,
            bronze_root=Path(temp_dir),
        )
        started = perf_counter()
        result = runner.run_source(PipelineSource.GIAS)
        elapsed = max(perf_counter() - started, 1e-9)
    return _BenchmarkMetrics(
        duration_seconds=elapsed,
        rows_per_second=result.promoted_rows / elapsed,
        downloaded_rows=result.downloaded_rows,
        staged_rows=result.staged_rows,
        promoted_rows=result.promoted_rows,
        status=result.status,
    )


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv or [])
    if args.rows <= 0:
        print("--rows must be greater than 0.", file=sys.stderr)
        return 2
    if args.min_rows_per_second <= 0:
        print("--min-rows-per-second must be greater than 0.", file=sys.stderr)
        return 2
    if args.max_duration_seconds <= 0:
        print("--max-duration-seconds must be greater than 0.", file=sys.stderr)
        return 2

    metrics = _run_benchmark(rows=args.rows)
    print(
        "throughput_benchmark "
        f"status={metrics.status.value} "
        f"duration_seconds={metrics.duration_seconds:.6f} "
        f"rows_per_second={metrics.rows_per_second:.2f} "
        f"downloaded_rows={metrics.downloaded_rows} "
        f"staged_rows={metrics.staged_rows} "
        f"promoted_rows={metrics.promoted_rows}"
    )

    strict_ok = (
        metrics.status == PipelineRunStatus.SUCCEEDED
        and metrics.rows_per_second >= args.min_rows_per_second
        and metrics.duration_seconds <= args.max_duration_seconds
    )
    if args.strict and not strict_ok:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
