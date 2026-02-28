from collections.abc import Mapping
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.engine import Engine

from .base import (
    Pipeline,
    PipelineResult,
    PipelineRunContext,
    PipelineRunStatus,
    PipelineSource,
    StageResult,
    utc_now,
)


class PipelineRunStore(Protocol):
    def record_started(self, context: PipelineRunContext) -> None: ...

    def record_finished(self, run_id: str, result: PipelineResult) -> None: ...


class SqlPipelineRunStore:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def record_started(self, context: PipelineRunContext) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO pipeline_runs (
                        run_id,
                        source,
                        status,
                        started_at,
                        bronze_path,
                        downloaded_rows,
                        staged_rows,
                        promoted_rows,
                        rejected_rows
                    ) VALUES (
                        :run_id,
                        :source,
                        :status,
                        :started_at,
                        :bronze_path,
                        0,
                        0,
                        0,
                        0
                    )
                    """
                ),
                {
                    "run_id": str(context.run_id),
                    "source": context.source.value,
                    "status": PipelineRunStatus.RUNNING.value,
                    "started_at": context.started_at,
                    "bronze_path": str(context.bronze_source_path),
                },
            )

    def record_finished(self, run_id: str, result: PipelineResult) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    """
                    UPDATE pipeline_runs
                    SET
                        status = :status,
                        finished_at = :finished_at,
                        downloaded_rows = :downloaded_rows,
                        staged_rows = :staged_rows,
                        promoted_rows = :promoted_rows,
                        rejected_rows = :rejected_rows,
                        error_message = :error_message
                    WHERE run_id = :run_id
                    """
                ),
                {
                    "run_id": run_id,
                    "status": result.status.value,
                    "finished_at": utc_now(),
                    "downloaded_rows": result.downloaded_rows,
                    "staged_rows": result.staged_rows,
                    "promoted_rows": result.promoted_rows,
                    "rejected_rows": result.rejected_rows,
                    "error_message": result.error_message,
                },
            )


class PipelineRunner:
    def __init__(
        self,
        pipelines: Mapping[PipelineSource, Pipeline],
        run_store: PipelineRunStore,
        bronze_root: Path,
    ) -> None:
        self._pipelines = dict(pipelines)
        self._run_store = run_store
        self._bronze_root = bronze_root

    def available_sources(self) -> tuple[str, ...]:
        return tuple(source.value for source in self._pipelines)

    def run_source(self, source: PipelineSource | str) -> PipelineResult:
        resolved_source = PipelineSource(source) if isinstance(source, str) else source

        pipeline = self._pipelines.get(resolved_source)
        if pipeline is None:
            raise KeyError(f"No pipeline registered for source '{resolved_source.value}'")

        context = PipelineRunContext(
            run_id=uuid4(),
            source=resolved_source,
            started_at=utc_now(),
            bronze_root=self._bronze_root,
        )

        self._run_store.record_started(context)

        downloaded_rows = 0
        staged_result = StageResult(staged_rows=0, rejected_rows=0)
        promoted_rows = 0
        error_message: str | None = None
        status = PipelineRunStatus.SUCCEEDED

        try:
            downloaded_rows = pipeline.download(context)
            staged_result = pipeline.stage(context)
            promoted_rows = pipeline.promote(context)
        except Exception as exc:  # pragma: no cover - covered via tests asserting output.
            status = PipelineRunStatus.FAILED
            error_message = str(exc)

        result = PipelineResult(
            status=status,
            downloaded_rows=downloaded_rows,
            staged_rows=staged_result.staged_rows,
            promoted_rows=promoted_rows,
            rejected_rows=staged_result.rejected_rows,
            error_message=error_message,
        )
        self._run_store.record_finished(str(context.run_id), result)
        return result

    def run_all(self) -> dict[PipelineSource, PipelineResult]:
        results: dict[PipelineSource, PipelineResult] = {}
        for source in self._pipelines:
            results[source] = self.run_source(source)
        return results
