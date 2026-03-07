from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from datetime import datetime, timezone
from typing import Any, cast
from uuid import UUID, uuid4

from sqlalchemy import bindparam, text
from sqlalchemy.engine import Engine, RowMapping

from civitas.application.school_summaries.ports.summary_repository import SummaryRepository
from civitas.domain.school_summaries.models import (
    SchoolSummary,
    SummaryGenerationRun,
    SummaryGenerationRunItem,
    SummaryKind,
    SummaryRunItemStatus,
    SummaryRunStatus,
    SummaryTrigger,
)


class PostgresSummaryRepository(SummaryRepository):
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def get_summary(self, urn: str, summary_kind: SummaryKind) -> SchoolSummary | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    text(
                        """
                        SELECT
                            urn,
                            summary_kind,
                            text,
                            data_version_hash,
                            prompt_version,
                            model_id,
                            generated_at,
                            generation_duration_ms
                        FROM school_ai_summaries
                        WHERE urn = :urn
                          AND summary_kind = :summary_kind
                        """
                    ),
                    {"urn": urn, "summary_kind": summary_kind},
                )
                .mappings()
                .first()
            )
        return None if row is None else _map_summary(row)

    def list_summaries(
        self,
        *,
        summary_kind: SummaryKind,
        urns: Sequence[str] | None = None,
    ) -> list[SchoolSummary]:
        query = """
            SELECT
                urn,
                summary_kind,
                text,
                data_version_hash,
                prompt_version,
                model_id,
                generated_at,
                generation_duration_ms
            FROM school_ai_summaries
            WHERE summary_kind = :summary_kind
        """
        statement = text(query + " ORDER BY urn ASC")
        params: dict[str, object] = {"summary_kind": summary_kind}
        if urns is not None:
            statement = text(query + " AND urn IN :urns ORDER BY urn ASC").bindparams(
                bindparam("urns", expanding=True)
            )
            params["urns"] = list(urns)

        with self._engine.connect() as connection:
            rows = connection.execute(statement, params).mappings()
            return [_map_summary(row) for row in rows]

    def upsert_summary(self, summary: SchoolSummary) -> None:
        self.upsert_summaries([summary])

    def upsert_summaries(self, summaries: Sequence[SchoolSummary]) -> None:
        if not summaries:
            return

        summaries_by_kind: dict[SummaryKind, list[SchoolSummary]] = defaultdict(list)
        for summary in summaries:
            summaries_by_kind[summary.summary_kind].append(summary)

        with self._engine.begin() as connection:
            existing_rows: list[RowMapping] = []
            for summary_kind, kind_summaries in summaries_by_kind.items():
                urns = [summary.urn for summary in kind_summaries]
                existing_rows.extend(
                    connection.execute(
                        text(
                            """
                            SELECT
                                urn,
                                summary_kind,
                                text,
                                data_version_hash,
                                prompt_version,
                                model_id,
                                generated_at
                            FROM school_ai_summaries
                            WHERE summary_kind = :summary_kind
                              AND urn IN :urns
                            """
                        ).bindparams(bindparam("urns", expanding=True)),
                        {"summary_kind": summary_kind, "urns": urns},
                    )
                    .mappings()
                    .all()
                )

            summaries_by_key = {
                (summary.summary_kind, summary.urn): summary for summary in summaries
            }
            if existing_rows:
                connection.execute(
                    _INSERT_SUMMARY_HISTORY_STATEMENT,
                    [
                        _insert_summary_history_params(
                            row=existing,
                            superseded_at=summaries_by_key[
                                (_to_summary_kind(existing["summary_kind"]), str(existing["urn"]))
                            ].generated_at,
                        )
                        for existing in existing_rows
                    ],
                )

            connection.execute(
                _UPSERT_SUMMARY_STATEMENT,
                [_upsert_summary_params(summary) for summary in summaries],
            )

    def create_run(
        self,
        trigger: SummaryTrigger,
        requested_count: int,
        summary_kind: SummaryKind,
    ) -> SummaryGenerationRun:
        run_id = uuid4()
        started_at = _utcnow()
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO ai_generation_runs (
                        id,
                        summary_kind,
                        trigger,
                        requested_count,
                        succeeded_count,
                        generation_failed_count,
                        validation_failed_count,
                        started_at,
                        completed_at,
                        status
                    ) VALUES (
                        :id,
                        :summary_kind,
                        :trigger,
                        :requested_count,
                        0,
                        0,
                        0,
                        :started_at,
                        NULL,
                        'running'
                    )
                    """
                ),
                {
                    "id": str(run_id),
                    "summary_kind": summary_kind,
                    "trigger": trigger,
                    "requested_count": requested_count,
                    "started_at": started_at,
                },
            )
        return SummaryGenerationRun(
            id=run_id,
            summary_kind=summary_kind,
            trigger=trigger,
            requested_count=requested_count,
            succeeded_count=0,
            generation_failed_count=0,
            validation_failed_count=0,
            started_at=started_at,
            completed_at=None,
            status="running",
        )

    def get_run(self, run_id: UUID) -> SummaryGenerationRun | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    text(
                        """
                        SELECT
                            id,
                            summary_kind,
                            trigger,
                            requested_count,
                            succeeded_count,
                            generation_failed_count,
                            validation_failed_count,
                            started_at,
                            completed_at,
                            status
                        FROM ai_generation_runs
                        WHERE id = :run_id
                        """
                    ),
                    {"run_id": str(run_id)},
                )
                .mappings()
                .first()
            )
        return None if row is None else _map_run(row)

    def list_run_items(self, run_id: UUID) -> list[SummaryGenerationRunItem]:
        with self._engine.connect() as connection:
            rows = connection.execute(
                text(
                    """
                    SELECT
                        run_id,
                        urn,
                        status,
                        attempt_count,
                        failure_reason_codes,
                        completed_at,
                        data_version_hash,
                        provider_name,
                        provider_batch_id,
                        prompt_version,
                        submitted_at
                    FROM ai_generation_run_items
                    WHERE run_id = :run_id
                    ORDER BY urn ASC
                    """
                ),
                {"run_id": str(run_id)},
            ).mappings()
            return [_map_run_item(row) for row in rows]

    def list_pending_batch_run_items(
        self,
        summary_kind: SummaryKind,
        run_id: UUID | None = None,
    ) -> list[SummaryGenerationRunItem]:
        query = """
            SELECT
                items.run_id,
                items.urn,
                items.status,
                items.attempt_count,
                items.failure_reason_codes,
                items.completed_at,
                items.data_version_hash,
                items.provider_name,
                items.provider_batch_id,
                items.prompt_version,
                items.submitted_at
            FROM ai_generation_run_items AS items
            INNER JOIN ai_generation_runs AS runs
                ON runs.id = items.run_id
            WHERE items.status = 'submitted_batch'
              AND runs.summary_kind = :summary_kind
        """
        statement = text(
            query + " ORDER BY items.run_id ASC, items.provider_batch_id ASC, items.urn ASC"
        )
        params: dict[str, object] = {"summary_kind": summary_kind}
        if run_id is not None:
            statement = text(
                query
                + " AND items.run_id = :run_id ORDER BY items.run_id ASC, items.provider_batch_id ASC, items.urn ASC"
            )
            params["run_id"] = str(run_id)

        with self._engine.connect() as connection:
            rows = connection.execute(statement, params).mappings()
            return [_map_run_item(row) for row in rows]

    def upsert_run_item(self, item: SummaryGenerationRunItem) -> None:
        self.upsert_run_items([item])

    def upsert_run_items(self, items: Sequence[SummaryGenerationRunItem]) -> None:
        if not items:
            return

        with self._engine.begin() as connection:
            connection.execute(
                _UPSERT_RUN_ITEM_STATEMENT,
                [_upsert_run_item_params(item) for item in items],
            )

    def finalize_run(self, run_id: UUID, status: SummaryRunStatus) -> SummaryGenerationRun:
        completed_at = _utcnow()
        with self._engine.begin() as connection:
            counts = (
                connection.execute(
                    text(
                        """
                        SELECT
                            COUNT(*) FILTER (WHERE status = 'succeeded') AS succeeded_count,
                            COUNT(*) FILTER (
                                WHERE status = 'generation_failed'
                            ) AS generation_failed_count,
                            COUNT(*) FILTER (
                                WHERE status = 'validation_failed'
                            ) AS validation_failed_count
                        FROM ai_generation_run_items
                        WHERE run_id = :run_id
                        """
                    ),
                    {"run_id": str(run_id)},
                )
                .mappings()
                .one()
            )
            connection.execute(
                text(
                    """
                    UPDATE ai_generation_runs
                    SET
                        succeeded_count = :succeeded_count,
                        generation_failed_count = :generation_failed_count,
                        validation_failed_count = :validation_failed_count,
                        completed_at = :completed_at,
                        status = :status
                    WHERE id = :run_id
                    """
                ),
                {
                    "run_id": str(run_id),
                    "succeeded_count": int(counts["succeeded_count"] or 0),
                    "generation_failed_count": int(counts["generation_failed_count"] or 0),
                    "validation_failed_count": int(counts["validation_failed_count"] or 0),
                    "completed_at": completed_at,
                    "status": status,
                },
            )
            row = (
                connection.execute(
                    text(
                        """
                        SELECT
                            id,
                            summary_kind,
                            trigger,
                            requested_count,
                            succeeded_count,
                            generation_failed_count,
                            validation_failed_count,
                            started_at,
                            completed_at,
                            status
                        FROM ai_generation_runs
                        WHERE id = :run_id
                        """
                    ),
                    {"run_id": str(run_id)},
                )
                .mappings()
                .one()
            )
        return _map_run(row)


def _map_summary(row: RowMapping) -> SchoolSummary:
    return SchoolSummary(
        urn=str(row["urn"]),
        summary_kind=_to_summary_kind(row["summary_kind"]),
        text=str(row["text"]),
        data_version_hash=str(row["data_version_hash"]),
        prompt_version=str(row["prompt_version"]),
        model_id=str(row["model_id"]),
        generated_at=_to_datetime(row["generated_at"]),
        generation_duration_ms=(
            None if row["generation_duration_ms"] is None else int(row["generation_duration_ms"])
        ),
    )


def _map_run(row: RowMapping) -> SummaryGenerationRun:
    return SummaryGenerationRun(
        id=_to_uuid(row["id"]),
        summary_kind=_to_summary_kind(row["summary_kind"]),
        trigger=_to_summary_trigger(row["trigger"]),
        requested_count=int(row["requested_count"]),
        succeeded_count=int(row["succeeded_count"]),
        generation_failed_count=int(row["generation_failed_count"]),
        validation_failed_count=int(row["validation_failed_count"]),
        started_at=_to_datetime(row["started_at"]),
        completed_at=_to_optional_datetime(row["completed_at"]),
        status=_to_run_status(row["status"]),
    )


def _map_run_item(row: RowMapping) -> SummaryGenerationRunItem:
    raw_reason_codes = row["failure_reason_codes"]
    if raw_reason_codes is None:
        reason_codes: tuple[str, ...] = ()
    else:
        reason_codes = tuple(str(value) for value in cast(Sequence[Any], raw_reason_codes))

    return SummaryGenerationRunItem(
        run_id=_to_uuid(row["run_id"]),
        urn=str(row["urn"]),
        status=_to_run_item_status(row["status"]),
        attempt_count=int(row["attempt_count"]),
        failure_reason_codes=reason_codes,
        completed_at=_to_optional_datetime(row["completed_at"]),
        data_version_hash=(
            None if row["data_version_hash"] is None else str(row["data_version_hash"])
        ),
        provider_name=None if row["provider_name"] is None else str(row["provider_name"]),
        provider_batch_id=(
            None if row["provider_batch_id"] is None else str(row["provider_batch_id"])
        ),
        prompt_version=None if row["prompt_version"] is None else str(row["prompt_version"]),
        submitted_at=_to_optional_datetime(row["submitted_at"]),
    )


def _to_uuid(value: object) -> UUID:
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


def _to_summary_trigger(value: object) -> SummaryTrigger:
    normalized = str(value)
    if normalized not in {"pipeline", "manual"}:
        raise ValueError(f"Unsupported summary trigger '{normalized}'.")
    return cast(SummaryTrigger, normalized)


def _to_summary_kind(value: object) -> SummaryKind:
    normalized = str(value)
    if normalized not in {"overview", "analyst"}:
        raise ValueError(f"Unsupported summary kind '{normalized}'.")
    return cast(SummaryKind, normalized)


def _to_run_status(value: object) -> SummaryRunStatus:
    normalized = str(value)
    if normalized not in {"running", "succeeded", "failed", "partial"}:
        raise ValueError(f"Unsupported run status '{normalized}'.")
    return cast(SummaryRunStatus, normalized)


def _to_run_item_status(value: object) -> SummaryRunItemStatus:
    normalized = str(value)
    if normalized not in {
        "submitted_batch",
        "succeeded",
        "generation_failed",
        "validation_failed",
        "skipped_current",
    }:
        raise ValueError(f"Unsupported run item status '{normalized}'.")
    return cast(SummaryRunItemStatus, normalized)


def _to_datetime(value: object) -> datetime:
    if isinstance(value, datetime):
        return value
    raise TypeError(f"Expected datetime, got {type(value).__name__}.")


def _to_optional_datetime(value: object) -> datetime | None:
    if value is None:
        return None
    return _to_datetime(value)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


_UPSERT_SUMMARY_STATEMENT = text(
    """
    INSERT INTO school_ai_summaries (
        urn,
        summary_kind,
        text,
        data_version_hash,
        prompt_version,
        model_id,
        generated_at,
        generation_duration_ms
    ) VALUES (
        :urn,
        :summary_kind,
        :text,
        :data_version_hash,
        :prompt_version,
        :model_id,
        :generated_at,
        :generation_duration_ms
    )
    ON CONFLICT (urn, summary_kind) DO UPDATE SET
        text = EXCLUDED.text,
        data_version_hash = EXCLUDED.data_version_hash,
        prompt_version = EXCLUDED.prompt_version,
        model_id = EXCLUDED.model_id,
        generated_at = EXCLUDED.generated_at,
        generation_duration_ms = EXCLUDED.generation_duration_ms
    """
)


_INSERT_SUMMARY_HISTORY_STATEMENT = text(
    """
    INSERT INTO school_ai_summary_history (
        id,
        urn,
        summary_kind,
        text,
        data_version_hash,
        prompt_version,
        model_id,
        generated_at,
        superseded_at
    ) VALUES (
        :id,
        :urn,
        :summary_kind,
        :text,
        :data_version_hash,
        :prompt_version,
        :model_id,
        :generated_at,
        :superseded_at
    )
    """
)


_UPSERT_RUN_ITEM_STATEMENT = text(
    """
    INSERT INTO ai_generation_run_items (
        run_id,
        urn,
        status,
        attempt_count,
        failure_reason_codes,
        completed_at,
        data_version_hash,
        provider_name,
        provider_batch_id,
        prompt_version,
        submitted_at
    ) VALUES (
        :run_id,
        :urn,
        :status,
        :attempt_count,
        :failure_reason_codes,
        :completed_at,
        :data_version_hash,
        :provider_name,
        :provider_batch_id,
        :prompt_version,
        :submitted_at
    )
    ON CONFLICT (run_id, urn) DO UPDATE SET
        status = EXCLUDED.status,
        attempt_count = EXCLUDED.attempt_count,
        failure_reason_codes = EXCLUDED.failure_reason_codes,
        completed_at = EXCLUDED.completed_at,
        data_version_hash = COALESCE(
            EXCLUDED.data_version_hash,
            ai_generation_run_items.data_version_hash
        ),
        provider_name = COALESCE(
            EXCLUDED.provider_name,
            ai_generation_run_items.provider_name
        ),
        provider_batch_id = COALESCE(
            EXCLUDED.provider_batch_id,
            ai_generation_run_items.provider_batch_id
        ),
        prompt_version = COALESCE(
            EXCLUDED.prompt_version,
            ai_generation_run_items.prompt_version
        ),
        submitted_at = COALESCE(
            EXCLUDED.submitted_at,
            ai_generation_run_items.submitted_at
        )
    """
)


def _upsert_run_item_params(item: SummaryGenerationRunItem) -> dict[str, object]:
    return {
        "run_id": str(item.run_id),
        "urn": item.urn,
        "status": item.status,
        "attempt_count": item.attempt_count,
        "failure_reason_codes": list(item.failure_reason_codes),
        "completed_at": item.completed_at,
        "data_version_hash": item.data_version_hash,
        "provider_name": item.provider_name,
        "provider_batch_id": item.provider_batch_id,
        "prompt_version": item.prompt_version,
        "submitted_at": item.submitted_at,
    }


def _upsert_summary_params(summary: SchoolSummary) -> dict[str, object]:
    return {
        "urn": summary.urn,
        "summary_kind": summary.summary_kind,
        "text": summary.text,
        "data_version_hash": summary.data_version_hash,
        "prompt_version": summary.prompt_version,
        "model_id": summary.model_id,
        "generated_at": summary.generated_at,
        "generation_duration_ms": summary.generation_duration_ms,
    }


def _insert_summary_history_params(
    *,
    row: RowMapping,
    superseded_at: datetime,
) -> dict[str, object]:
    return {
        "id": str(uuid4()),
        "urn": str(row["urn"]),
        "summary_kind": str(row["summary_kind"]),
        "text": str(row["text"]),
        "data_version_hash": str(row["data_version_hash"]),
        "prompt_version": str(row["prompt_version"]),
        "model_id": str(row["model_id"]),
        "generated_at": row["generated_at"],
        "superseded_at": superseded_at,
    }
