from __future__ import annotations

import hashlib
import json
import random
import time
import urllib.error
from collections.abc import Callable, Mapping
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import DBAPIError, DisconnectionError, OperationalError

from .base import (
    Pipeline,
    PipelineCheckpoint,
    PipelineCheckpointStatus,
    PipelineQualityConfig,
    PipelineResult,
    PipelineRetryPolicy,
    PipelineRunContext,
    PipelineRunStatus,
    PipelineSource,
    PipelineStep,
    StageResult,
    utc_now,
)


class PipelineRunStore(Protocol):
    def record_started(self, context: PipelineRunContext) -> None: ...

    def record_resumed(self, context: PipelineRunContext) -> None: ...

    def record_finished(
        self,
        context: PipelineRunContext,
        result: PipelineResult,
        finished_at: datetime,
    ) -> None: ...

    def last_successful_bronze_path(
        self,
        source: PipelineSource,
        before_started_at: datetime,
    ) -> Path | None: ...

    def acquire_source_lock(self, *, source: PipelineSource, run_id: UUID) -> bool: ...

    def release_source_lock(self, *, source: PipelineSource, run_id: UUID) -> None: ...

    def save_checkpoint(self, checkpoint: PipelineCheckpoint) -> None: ...

    def load_checkpoints(
        self,
        *,
        run_id: UUID,
        source: PipelineSource,
    ) -> dict[PipelineStep, PipelineCheckpoint]: ...

    def load_run_context(self, *, run_id: UUID) -> PipelineRunContext | None: ...

    def latest_resumable_context(self, *, source: PipelineSource) -> PipelineRunContext | None: ...


class SqlPipelineRunStore:
    _SCHOOL_PROFILE_CACHE_KEY = "school_profile"

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

    def record_resumed(self, context: PipelineRunContext) -> None:
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
                        rejected_rows,
                        error_message,
                        finished_at
                    ) VALUES (
                        :run_id,
                        :source,
                        :status,
                        :started_at,
                        :bronze_path,
                        0,
                        0,
                        0,
                        0,
                        NULL,
                        NULL
                    )
                    ON CONFLICT (run_id) DO UPDATE SET
                        status = EXCLUDED.status,
                        downloaded_rows = 0,
                        staged_rows = 0,
                        promoted_rows = 0,
                        rejected_rows = 0,
                        error_message = NULL,
                        finished_at = NULL
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

    def _touch_school_profile_cache_version(self, connection: Connection) -> None:
        if not _table_exists(connection, "app_cache_versions"):
            return

        if connection.dialect.name == "postgresql":
            connection.execute(
                text(
                    """
                    INSERT INTO app_cache_versions (
                        cache_key,
                        version_updated_at
                    ) VALUES (
                        :cache_key,
                        timezone('utc', now())
                    )
                    ON CONFLICT (cache_key) DO UPDATE SET
                        version_updated_at = timezone('utc', now())
                    """
                ),
                {"cache_key": self._SCHOOL_PROFILE_CACHE_KEY},
            )
            return

        connection.execute(
            text(
                """
                INSERT INTO app_cache_versions (
                    cache_key,
                    version_updated_at
                ) VALUES (
                    :cache_key,
                    CURRENT_TIMESTAMP
                )
                ON CONFLICT(cache_key) DO UPDATE SET
                    version_updated_at = CURRENT_TIMESTAMP
                """
            ),
            {"cache_key": self._SCHOOL_PROFILE_CACHE_KEY},
        )

    def record_finished(
        self,
        context: PipelineRunContext,
        result: PipelineResult,
        finished_at: datetime,
    ) -> None:
        dataset, section = _pipeline_event_dimensions(context.source)
        rejected_ratio: float | None = None
        if result.downloaded_rows > 0:
            rejected_ratio = result.rejected_rows / result.downloaded_rows
        duration_seconds = max((finished_at - context.started_at).total_seconds(), 0.0)

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
                    "run_id": str(context.run_id),
                    "status": result.status.value,
                    "finished_at": finished_at,
                    "downloaded_rows": result.downloaded_rows,
                    "staged_rows": result.staged_rows,
                    "promoted_rows": result.promoted_rows,
                    "rejected_rows": result.rejected_rows,
                    "error_message": result.error_message,
                },
            )

            if result.status == PipelineRunStatus.SUCCEEDED:
                self._touch_school_profile_cache_version(connection)

            if not _table_exists(connection, "pipeline_run_events"):
                return

            connection.execute(
                text(
                    """
                    INSERT INTO pipeline_run_events (
                        run_id,
                        source,
                        dataset,
                        section,
                        academic_year,
                        run_status,
                        contract_version,
                        started_at,
                        finished_at,
                        duration_seconds,
                        downloaded_rows,
                        staged_rows,
                        promoted_rows,
                        rejected_rows,
                        rejected_ratio,
                        error_message
                    ) VALUES (
                        :run_id,
                        :source,
                        :dataset,
                        :section,
                        NULL,
                        :run_status,
                        :contract_version,
                        :started_at,
                        :finished_at,
                        :duration_seconds,
                        :downloaded_rows,
                        :staged_rows,
                        :promoted_rows,
                        :rejected_rows,
                        :rejected_ratio,
                        :error_message
                    )
                    ON CONFLICT (run_id) DO UPDATE SET
                        source = EXCLUDED.source,
                        dataset = EXCLUDED.dataset,
                        section = EXCLUDED.section,
                        run_status = EXCLUDED.run_status,
                        contract_version = EXCLUDED.contract_version,
                        started_at = EXCLUDED.started_at,
                        finished_at = EXCLUDED.finished_at,
                        duration_seconds = EXCLUDED.duration_seconds,
                        downloaded_rows = EXCLUDED.downloaded_rows,
                        staged_rows = EXCLUDED.staged_rows,
                        promoted_rows = EXCLUDED.promoted_rows,
                        rejected_rows = EXCLUDED.rejected_rows,
                        rejected_ratio = EXCLUDED.rejected_ratio,
                        error_message = EXCLUDED.error_message
                    """
                ),
                {
                    "run_id": str(context.run_id),
                    "source": context.source.value,
                    "dataset": dataset,
                    "section": section,
                    "run_status": result.status.value,
                    "contract_version": result.contract_version,
                    "started_at": context.started_at,
                    "finished_at": finished_at,
                    "duration_seconds": duration_seconds,
                    "downloaded_rows": result.downloaded_rows,
                    "staged_rows": result.staged_rows,
                    "promoted_rows": result.promoted_rows,
                    "rejected_rows": result.rejected_rows,
                    "rejected_ratio": rejected_ratio,
                    "error_message": result.error_message,
                },
            )

    def last_successful_bronze_path(
        self,
        source: PipelineSource,
        before_started_at: datetime,
    ) -> Path | None:
        with self._engine.begin() as connection:
            row = connection.execute(
                text(
                    """
                    SELECT bronze_path
                    FROM pipeline_runs
                    WHERE source = :source
                      AND status = :status
                      AND started_at < :started_at
                    ORDER BY started_at DESC
                    LIMIT 1
                    """
                ),
                {
                    "source": source.value,
                    "status": PipelineRunStatus.SUCCEEDED.value,
                    "started_at": before_started_at,
                },
            ).fetchone()

        if row is None:
            return None
        bronze_path = row[0]
        if not isinstance(bronze_path, str) or not bronze_path.strip():
            return None
        return Path(bronze_path)

    def acquire_source_lock(self, *, source: PipelineSource, run_id: UUID) -> bool:
        with self._engine.begin() as connection:
            if not _table_exists(connection, "pipeline_source_locks"):
                return True
            acquired_at_sql = (
                "timezone('utc', now())"
                if connection.dialect.name == "postgresql"
                else "CURRENT_TIMESTAMP"
            )
            result = connection.execute(
                text(
                    f"""
                    INSERT INTO pipeline_source_locks (
                        source,
                        run_id,
                        acquired_at
                    ) VALUES (
                        :source,
                        :run_id,
                        {acquired_at_sql}
                    )
                    ON CONFLICT (source) DO NOTHING
                    """
                ),
                {
                    "source": source.value,
                    "run_id": str(run_id),
                },
            )
            if int(result.rowcount or 0) > 0:
                return True

            existing = connection.execute(
                text(
                    """
                    SELECT run_id
                    FROM pipeline_source_locks
                    WHERE source = :source
                    LIMIT 1
                    """
                ),
                {"source": source.value},
            ).fetchone()
            if existing is None:
                return False

            existing_run_id = existing[0]
            if isinstance(existing_run_id, UUID):
                return existing_run_id == run_id
            return str(existing_run_id) == str(run_id)

    def release_source_lock(self, *, source: PipelineSource, run_id: UUID) -> None:
        with self._engine.begin() as connection:
            if not _table_exists(connection, "pipeline_source_locks"):
                return
            connection.execute(
                text(
                    """
                    DELETE FROM pipeline_source_locks
                    WHERE source = :source
                      AND run_id = :run_id
                    """
                ),
                {
                    "source": source.value,
                    "run_id": str(run_id),
                },
            )

    def save_checkpoint(self, checkpoint: PipelineCheckpoint) -> None:
        with self._engine.begin() as connection:
            if not _table_exists(connection, "pipeline_checkpoints"):
                return
            payload_json = json.dumps(checkpoint.payload, sort_keys=True, ensure_ascii=True)
            if connection.dialect.name == "postgresql":
                connection.execute(
                    text(
                        """
                        INSERT INTO pipeline_checkpoints (
                            run_id,
                            source,
                            step,
                            status,
                            attempts,
                            retryable,
                            payload,
                            error_message,
                            updated_at
                        ) VALUES (
                            :run_id,
                            :source,
                            :step,
                            :status,
                            :attempts,
                            :retryable,
                            CAST(:payload AS jsonb),
                            :error_message,
                            timezone('utc', now())
                        )
                        ON CONFLICT (run_id, source, step) DO UPDATE SET
                            status = EXCLUDED.status,
                            attempts = EXCLUDED.attempts,
                            retryable = EXCLUDED.retryable,
                            payload = EXCLUDED.payload,
                            error_message = EXCLUDED.error_message,
                            updated_at = timezone('utc', now())
                        """
                    ),
                    {
                        "run_id": str(checkpoint.run_id),
                        "source": checkpoint.source.value,
                        "step": checkpoint.step.value,
                        "status": checkpoint.status.value,
                        "attempts": checkpoint.attempts,
                        "retryable": checkpoint.retryable,
                        "payload": payload_json,
                        "error_message": checkpoint.error_message,
                    },
                )
                return

            connection.execute(
                text(
                    """
                    INSERT INTO pipeline_checkpoints (
                        run_id,
                        source,
                        step,
                        status,
                        attempts,
                        retryable,
                        payload,
                        error_message,
                        updated_at
                    ) VALUES (
                        :run_id,
                        :source,
                        :step,
                        :status,
                        :attempts,
                        :retryable,
                        :payload,
                        :error_message,
                        CURRENT_TIMESTAMP
                    )
                    ON CONFLICT (run_id, source, step) DO UPDATE SET
                        status = excluded.status,
                        attempts = excluded.attempts,
                        retryable = excluded.retryable,
                        payload = excluded.payload,
                        error_message = excluded.error_message,
                        updated_at = CURRENT_TIMESTAMP
                    """
                ),
                {
                    "run_id": str(checkpoint.run_id),
                    "source": checkpoint.source.value,
                    "step": checkpoint.step.value,
                    "status": checkpoint.status.value,
                    "attempts": checkpoint.attempts,
                    "retryable": checkpoint.retryable,
                    "payload": payload_json,
                    "error_message": checkpoint.error_message,
                },
            )

    def load_checkpoints(
        self,
        *,
        run_id: UUID,
        source: PipelineSource,
    ) -> dict[PipelineStep, PipelineCheckpoint]:
        with self._engine.begin() as connection:
            if not _table_exists(connection, "pipeline_checkpoints"):
                return {}
            rows = connection.execute(
                text(
                    """
                    SELECT
                        step,
                        status,
                        attempts,
                        retryable,
                        payload,
                        error_message
                    FROM pipeline_checkpoints
                    WHERE run_id = :run_id
                      AND source = :source
                    """
                ),
                {
                    "run_id": str(run_id),
                    "source": source.value,
                },
            ).all()

        checkpoints: dict[PipelineStep, PipelineCheckpoint] = {}
        for row in rows:
            step_raw = row[0]
            status_raw = row[1]
            try:
                step = PipelineStep(str(step_raw))
                status = PipelineCheckpointStatus(str(status_raw))
            except ValueError:
                continue
            payload = _decode_payload(row[4])
            checkpoints[step] = PipelineCheckpoint(
                run_id=run_id,
                source=source,
                step=step,
                status=status,
                attempts=int(row[2] or 0),
                retryable=bool(row[3]),
                payload=payload,
                error_message=str(row[5]) if row[5] is not None else None,
            )
        return checkpoints

    def load_run_context(self, *, run_id: UUID) -> PipelineRunContext | None:
        with self._engine.begin() as connection:
            row = connection.execute(
                text(
                    """
                    SELECT run_id, source, started_at, bronze_path
                    FROM pipeline_runs
                    WHERE run_id = :run_id
                    LIMIT 1
                    """
                ),
                {"run_id": str(run_id)},
            ).fetchone()

        if row is None:
            return None
        source_raw = row[1]
        started_at = row[2]
        bronze_path_raw = row[3]
        if not isinstance(source_raw, str):
            return None
        if not isinstance(bronze_path_raw, str):
            return None
        try:
            source = PipelineSource(source_raw)
        except ValueError:
            return None
        if not isinstance(started_at, datetime):
            return None
        bronze_source_path = Path(bronze_path_raw)
        bronze_root = _derive_bronze_root(bronze_source_path)
        return PipelineRunContext(
            run_id=run_id,
            source=source,
            started_at=started_at,
            bronze_root=bronze_root,
        )

    def latest_resumable_context(self, *, source: PipelineSource) -> PipelineRunContext | None:
        with self._engine.begin() as connection:
            if not _table_exists(connection, "pipeline_checkpoints"):
                return None
            row = connection.execute(
                text(
                    """
                    SELECT run_id
                    FROM pipeline_runs
                    WHERE source = :source
                      AND status IN (
                        :status_failed,
                        :status_failed_quality_gate,
                        :status_failed_source_unavailable
                      )
                      AND EXISTS (
                        SELECT 1
                        FROM pipeline_checkpoints checkpoints
                        WHERE checkpoints.run_id = pipeline_runs.run_id
                          AND checkpoints.source = pipeline_runs.source
                      )
                    ORDER BY started_at DESC
                    LIMIT 1
                    """
                ),
                {
                    "source": source.value,
                    "status_failed": PipelineRunStatus.FAILED.value,
                    "status_failed_quality_gate": PipelineRunStatus.FAILED_QUALITY_GATE.value,
                    "status_failed_source_unavailable": (
                        PipelineRunStatus.FAILED_SOURCE_UNAVAILABLE.value
                    ),
                },
            ).fetchone()

        if row is None:
            return None
        run_id_raw = row[0]
        resolved_run_id = run_id_raw if isinstance(run_id_raw, UUID) else UUID(str(run_id_raw))
        return self.load_run_context(run_id=resolved_run_id)


class PipelineRunner:
    def __init__(
        self,
        pipelines: Mapping[PipelineSource, Pipeline],
        run_store: PipelineRunStore,
        bronze_root: Path,
        quality_config_by_source: Mapping[PipelineSource, PipelineQualityConfig] | None = None,
        retry_policy: PipelineRetryPolicy | None = None,
        *,
        stage_chunk_size: int = 1000,
        promote_chunk_size: int = 1000,
        http_timeout_seconds: float = 60.0,
        max_concurrent_sources: int = 1,
        resume_enabled: bool = True,
        sleep: Callable[[float], None] = time.sleep,
        random_fraction: Callable[[], float] = random.random,
    ) -> None:
        if stage_chunk_size <= 0:
            raise ValueError("stage_chunk_size must be greater than 0.")
        if promote_chunk_size <= 0:
            raise ValueError("promote_chunk_size must be greater than 0.")
        if http_timeout_seconds <= 0:
            raise ValueError("http_timeout_seconds must be greater than 0.")
        if max_concurrent_sources <= 0:
            raise ValueError("max_concurrent_sources must be greater than 0.")

        self._pipelines = dict(pipelines)
        self._run_store = run_store
        self._bronze_root = bronze_root
        self._quality_config_by_source = dict(quality_config_by_source or {})
        self._retry_policy = retry_policy or PipelineRetryPolicy(max_retries=0)
        self._stage_chunk_size = stage_chunk_size
        self._promote_chunk_size = promote_chunk_size
        self._http_timeout_seconds = http_timeout_seconds
        self._max_concurrent_sources = max_concurrent_sources
        self._resume_enabled = resume_enabled
        self._sleep = sleep
        self._random_fraction = random_fraction

    def available_sources(self) -> tuple[str, ...]:
        return tuple(source.value for source in self._pipelines)

    def run_source(
        self,
        source: PipelineSource | str,
        *,
        resume: bool = False,
        run_id: UUID | str | None = None,
    ) -> PipelineResult:
        resolved_source = PipelineSource(source) if isinstance(source, str) else source
        pipeline = self._pipelines.get(resolved_source)
        if pipeline is None:
            raise KeyError(f"No pipeline registered for source '{resolved_source.value}'")

        if run_id is not None and not resume:
            raise ValueError("run_id can only be provided when resume=True.")
        if resume and not self._resume_enabled:
            raise ValueError(
                "Pipeline resume is disabled. Set CIVITAS_PIPELINE_RESUME_ENABLED=true to resume."
            )

        context, resumed = self._resolve_run_context(
            source=resolved_source,
            resume=resume,
            run_id=run_id,
        )

        if resumed:
            self._run_store.record_resumed(context)
        else:
            self._run_store.record_started(context)

        lock_acquired = self._run_store.acquire_source_lock(
            source=context.source,
            run_id=context.run_id,
        )
        if not lock_acquired:
            result = PipelineResult(
                status=PipelineRunStatus.FAILED,
                error_message=f"gate_id=source_lock_conflict source={context.source.value}",
            )
            self._run_store.record_finished(context, result, utc_now())
            return result

        downloaded_rows = 0
        staged_result = StageResult(staged_rows=0, rejected_rows=0)
        promoted_rows = 0
        error_message: str | None = None
        status = PipelineRunStatus.SUCCEEDED
        quality_config = self._quality_config_by_source.get(
            resolved_source, PipelineQualityConfig()
        )
        checkpoints = self._run_store.load_checkpoints(
            run_id=context.run_id,
            source=context.source,
        )

        try:
            if _is_checkpoint_completed(checkpoints, PipelineStep.DOWNLOAD):
                downloaded_rows = _checkpoint_int(
                    checkpoints[PipelineStep.DOWNLOAD].payload,
                    "downloaded_rows",
                )
            else:
                downloaded_rows = self._execute_with_retry(
                    context=context,
                    step=PipelineStep.DOWNLOAD,
                    execute=lambda: pipeline.download(context),
                    payload_builder=lambda rows: {"downloaded_rows": int(rows)},
                )

            if downloaded_rows == 0:
                status = PipelineRunStatus.FAILED_SOURCE_UNAVAILABLE
                error_message = (
                    f"gate_id=download_nonzero downloaded_rows=0 source={resolved_source.value}"
                )
            else:
                if not _is_checkpoint_completed(
                    checkpoints, PipelineStep.STAGE
                ) and not _is_checkpoint_completed(checkpoints, PipelineStep.PROMOTE):
                    current_checksum = _resolve_bronze_checksum(context.bronze_source_path)
                    previous_bronze_path = self._run_store.last_successful_bronze_path(
                        source=resolved_source,
                        before_started_at=context.started_at,
                    )
                    previous_checksum = (
                        _resolve_bronze_checksum(previous_bronze_path)
                        if previous_bronze_path is not None
                        else None
                    )
                    if (
                        current_checksum is not None
                        and previous_checksum is not None
                        and current_checksum == previous_checksum
                    ):
                        status = PipelineRunStatus.SKIPPED_NO_CHANGE

                if status != PipelineRunStatus.SKIPPED_NO_CHANGE:
                    if _is_checkpoint_completed(checkpoints, PipelineStep.STAGE):
                        staged_result = StageResult(
                            staged_rows=_checkpoint_int(
                                checkpoints[PipelineStep.STAGE].payload,
                                "staged_rows",
                            ),
                            rejected_rows=_checkpoint_int(
                                checkpoints[PipelineStep.STAGE].payload,
                                "rejected_rows",
                            ),
                            contract_version=_checkpoint_text(
                                checkpoints[PipelineStep.STAGE].payload,
                                "contract_version",
                            ),
                        )
                    else:
                        staged_result = self._execute_with_retry(
                            context=context,
                            step=PipelineStep.STAGE,
                            execute=lambda: pipeline.stage(context),
                            payload_builder=lambda stage: {
                                "staged_rows": stage.staged_rows,
                                "rejected_rows": stage.rejected_rows,
                                "contract_version": stage.contract_version,
                            },
                        )

                    if staged_result.staged_rows == 0:
                        status = PipelineRunStatus.FAILED_QUALITY_GATE
                        error_message = (
                            "gate_id=stage_nonzero "
                            f"downloaded_rows={downloaded_rows} "
                            f"staged_rows={staged_result.staged_rows}"
                        )
                    else:
                        reject_ratio = staged_result.rejected_rows / downloaded_rows
                        if reject_ratio > quality_config.max_reject_ratio:
                            status = PipelineRunStatus.FAILED_QUALITY_GATE
                            error_message = (
                                "gate_id=max_reject_ratio "
                                f"downloaded_rows={downloaded_rows} "
                                f"rejected_rows={staged_result.rejected_rows} "
                                f"reject_ratio={reject_ratio:.6f} "
                                f"max_reject_ratio={quality_config.max_reject_ratio:.6f}"
                            )
                        else:
                            if _is_checkpoint_completed(checkpoints, PipelineStep.PROMOTE):
                                promoted_rows = _checkpoint_int(
                                    checkpoints[PipelineStep.PROMOTE].payload,
                                    "promoted_rows",
                                )
                            else:
                                promoted_rows = self._execute_with_retry(
                                    context=context,
                                    step=PipelineStep.PROMOTE,
                                    execute=lambda: pipeline.promote(context),
                                    payload_builder=lambda rows: {"promoted_rows": int(rows)},
                                )
                            if promoted_rows == 0:
                                status = PipelineRunStatus.FAILED_QUALITY_GATE
                                error_message = (
                                    "gate_id=promote_nonzero "
                                    f"staged_rows={staged_result.staged_rows} "
                                    f"promoted_rows={promoted_rows}"
                                )
        except Exception as exc:  # pragma: no cover - covered via tests asserting output.
            status = PipelineRunStatus.FAILED
            error_message = str(exc)
        finally:
            self._run_store.release_source_lock(source=context.source, run_id=context.run_id)

        result = PipelineResult(
            status=status,
            downloaded_rows=downloaded_rows,
            staged_rows=staged_result.staged_rows,
            promoted_rows=promoted_rows,
            rejected_rows=staged_result.rejected_rows,
            contract_version=staged_result.contract_version,
            error_message=error_message,
        )
        finished_at = utc_now()
        self._run_store.record_finished(context, result, finished_at)
        return result

    def resume_run(self, run_id: UUID | str) -> tuple[PipelineSource, PipelineResult]:
        resolved_run_id = run_id if isinstance(run_id, UUID) else UUID(run_id)
        context = self._run_store.load_run_context(run_id=resolved_run_id)
        if context is None:
            raise KeyError(f"No pipeline run found for run_id '{resolved_run_id}'.")
        return context.source, self.run_source(
            context.source,
            resume=True,
            run_id=resolved_run_id,
        )

    def run_all(self) -> dict[PipelineSource, PipelineResult]:
        ordered_sources = list(self._pipelines)
        if self._max_concurrent_sources <= 1 or len(ordered_sources) <= 1:
            return {source: self.run_source(source) for source in ordered_sources}

        unordered_results: dict[PipelineSource, PipelineResult] = {}
        with ThreadPoolExecutor(
            max_workers=min(self._max_concurrent_sources, len(ordered_sources))
        ) as executor:
            futures = {
                executor.submit(self.run_source, source): source for source in ordered_sources
            }
            for future in as_completed(futures):
                source = futures[future]
                unordered_results[source] = future.result()
        return {source: unordered_results[source] for source in ordered_sources}

    def _resolve_run_context(
        self,
        *,
        source: PipelineSource,
        resume: bool,
        run_id: UUID | str | None,
    ) -> tuple[PipelineRunContext, bool]:
        if resume:
            explicit_run_id = (
                run_id if isinstance(run_id, UUID) else UUID(run_id) if run_id else None
            )
            if explicit_run_id is not None:
                context = self._run_store.load_run_context(run_id=explicit_run_id)
                if context is None:
                    raise KeyError(f"No pipeline run found for run_id '{explicit_run_id}'.")
                if context.source != source:
                    raise KeyError(
                        f"Run '{explicit_run_id}' belongs to source '{context.source.value}', not '{source.value}'."
                    )
                return context, True

            resumable_context = self._run_store.latest_resumable_context(source=source)
            if resumable_context is not None:
                return resumable_context, True

        return (
            PipelineRunContext(
                run_id=uuid4(),
                source=source,
                started_at=utc_now(),
                bronze_root=self._bronze_root,
                stage_chunk_size=self._stage_chunk_size,
                promote_chunk_size=self._promote_chunk_size,
                http_timeout_seconds=self._http_timeout_seconds,
            ),
            False,
        )

    def _execute_with_retry(
        self,
        *,
        context: PipelineRunContext,
        step: PipelineStep,
        execute: Callable[[], Any],
        payload_builder: Callable[[Any], dict[str, object]],
    ) -> Any:
        attempt = 0
        while True:
            try:
                value = execute()
                checkpoint = PipelineCheckpoint(
                    run_id=context.run_id,
                    source=context.source,
                    step=step,
                    status=PipelineCheckpointStatus.COMPLETED,
                    attempts=attempt,
                    retryable=False,
                    payload=payload_builder(value),
                    error_message=None,
                )
                self._run_store.save_checkpoint(checkpoint)
                return value
            except Exception as exc:
                retryable = is_transient_pipeline_error(exc)
                checkpoint = PipelineCheckpoint(
                    run_id=context.run_id,
                    source=context.source,
                    step=step,
                    status=PipelineCheckpointStatus.FAILED,
                    attempts=attempt,
                    retryable=retryable,
                    payload={"reason_code": _retry_reason_code(exc)},
                    error_message=str(exc),
                )
                self._run_store.save_checkpoint(checkpoint)
                if not retryable or attempt >= self._retry_policy.max_retries:
                    raise

                backoff_seconds = _compute_backoff_seconds(
                    backoff_seconds=self._retry_policy.backoff_seconds,
                    jitter_factor=self._retry_policy.jitter_factor,
                    attempt=attempt,
                    random_fraction=self._random_fraction(),
                )
                self._sleep(backoff_seconds)
                attempt += 1


def is_transient_pipeline_error(exc: BaseException) -> bool:
    if isinstance(exc, (TimeoutError, ConnectionError, DisconnectionError)):
        return True
    if isinstance(exc, OperationalError):
        return True
    if isinstance(exc, DBAPIError) and exc.connection_invalidated:
        return True
    if isinstance(exc, urllib.error.HTTPError):
        return exc.code in {408, 425, 429} or exc.code >= 500
    return bool(isinstance(exc, urllib.error.URLError))


def _compute_backoff_seconds(
    *,
    backoff_seconds: float,
    jitter_factor: float,
    attempt: int,
    random_fraction: float,
) -> float:
    exponent = 2 ** max(attempt, 0)
    jitter_multiplier = 1.0 + max(jitter_factor, 0.0) * max(random_fraction, 0.0)
    return backoff_seconds * exponent * jitter_multiplier


def _retry_reason_code(exc: BaseException) -> str:
    if isinstance(exc, TimeoutError):
        return "timeout"
    if isinstance(exc, ConnectionError):
        return "connection_error"
    if isinstance(exc, urllib.error.HTTPError):
        return f"http_{exc.code}"
    if isinstance(exc, urllib.error.URLError):
        return "url_error"
    if isinstance(exc, OperationalError):
        return "db_operational_error"
    if isinstance(exc, DBAPIError) and exc.connection_invalidated:
        return "db_connection_invalidated"
    return exc.__class__.__name__.casefold()


def _is_checkpoint_completed(
    checkpoints: Mapping[PipelineStep, PipelineCheckpoint],
    step: PipelineStep,
) -> bool:
    checkpoint = checkpoints.get(step)
    if checkpoint is None:
        return False
    return checkpoint.status == PipelineCheckpointStatus.COMPLETED


def _checkpoint_int(payload: Mapping[str, Any], key: str) -> int:
    value = payload.get(key)
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return 0
    return 0


def _checkpoint_text(payload: Mapping[str, Any], key: str) -> str | None:
    value = payload.get(key)
    if isinstance(value, str) and value.strip():
        return value
    return None


def _decode_payload(raw_payload: object) -> dict[str, object]:
    if isinstance(raw_payload, dict):
        return dict(raw_payload)
    if isinstance(raw_payload, str):
        try:
            parsed = json.loads(raw_payload)
        except json.JSONDecodeError:
            return {}
        if isinstance(parsed, dict):
            return {str(key): value for key, value in parsed.items()}
    return {}


def _derive_bronze_root(bronze_source_path: Path) -> Path:
    parents = bronze_source_path.parents
    if len(parents) >= 2:
        return parents[1]
    return bronze_source_path.parent


def _table_exists(connection: Connection, table_name: str) -> bool:
    dialect_name = connection.dialect.name
    if dialect_name == "postgresql":
        return bool(
            connection.execute(
                text("SELECT to_regclass(:table_name) IS NOT NULL"),
                {"table_name": table_name},
            ).scalar_one()
        )
    if dialect_name == "sqlite":
        row = connection.execute(
            text(
                """
                SELECT 1
                FROM sqlite_master
                WHERE type = 'table' AND name = :table_name
                LIMIT 1
                """
            ),
            {"table_name": table_name},
        ).fetchone()
        return row is not None
    return False


def _resolve_bronze_checksum(bronze_source_path: Path | None) -> str | None:
    if bronze_source_path is None or not bronze_source_path.exists():
        return None

    checksum_tokens: set[str] = set()
    for json_path in sorted(bronze_source_path.glob("*.json")):
        payload = _load_json_dict(json_path)
        if payload is None:
            continue

        top_level_checksum = payload.get("sha256")
        if isinstance(top_level_checksum, str) and top_level_checksum.strip():
            checksum_tokens.add(f"{json_path.name}:sha256:{top_level_checksum.strip().casefold()}")

        assets = payload.get("assets")
        if isinstance(assets, list):
            for asset in assets:
                if not isinstance(asset, dict):
                    continue
                asset_checksum = asset.get("sha256")
                if not isinstance(asset_checksum, str) or not asset_checksum.strip():
                    continue
                asset_name = asset.get("bronze_file_name")
                normalized_asset_name = (
                    str(asset_name).strip() if isinstance(asset_name, str) else "asset"
                )
                checksum_tokens.add(
                    f"{json_path.name}:{normalized_asset_name}:{asset_checksum.strip().casefold()}"
                )

    if not checksum_tokens:
        return None

    digest = hashlib.sha256()
    for token in sorted(checksum_tokens):
        digest.update(token.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def _load_json_dict(path: Path) -> dict[str, object] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    if isinstance(payload, dict):
        return payload
    return None


def _pipeline_event_dimensions(source: PipelineSource) -> tuple[str, str | None]:
    if source == PipelineSource.GIAS:
        return ("schools", None)
    if source == PipelineSource.DFE_CHARACTERISTICS:
        return ("school_demographics_yearly", "demographics")
    if source == PipelineSource.DFE_PERFORMANCE:
        return ("school_performance_yearly", "school_performance")
    if source == PipelineSource.OFSTED_LATEST:
        return ("school_ofsted_latest", "ofsted_latest")
    if source == PipelineSource.OFSTED_TIMELINE:
        return ("ofsted_inspections", "ofsted_timeline")
    if source == PipelineSource.ONS_IMD:
        return ("area_deprivation", "area_deprivation")
    if source == PipelineSource.POLICE_CRIME_CONTEXT:
        return ("area_crime_context", "area_crime")
    return (source.value, None)
