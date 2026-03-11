from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from datetime import datetime
from decimal import Decimal
from typing import cast

from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import SQLAlchemyError

from civitas.application.school_profiles.errors import SchoolProfileDataUnavailableError
from civitas.application.school_trends.errors import SchoolTrendsDataUnavailableError
from civitas.application.subject_performance.ports.subject_performance_repository import (
    SubjectPerformanceRepository,
)
from civitas.domain.subject_performance.models import (
    SchoolSubjectPerformanceGroupRow,
    SchoolSubjectPerformanceLatest,
    SchoolSubjectPerformanceSeries,
    SchoolSubjectSummary,
    SubjectPerformanceKeyStage,
)

_PUBLIC_KEY_STAGE_ORDER: tuple[SubjectPerformanceKeyStage, ...] = ("ks4", "16_to_18")


class PostgresSubjectPerformanceRepository(SubjectPerformanceRepository):
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def get_latest_subject_performance(
        self,
        urn: str,
        *,
        include_16_to_18: bool = False,
    ) -> SchoolSubjectPerformanceLatest | None:
        rows = self._load_summary_rows(
            urn=urn,
            include_16_to_18=include_16_to_18,
            error_factory=lambda: SchoolProfileDataUnavailableError(
                "School profile datastore is unavailable."
            ),
        )
        if rows is None:
            return None

        latest_breakdowns = _build_latest_breakdowns(rows)
        if len(latest_breakdowns) == 0:
            return None

        ranked_subjects = tuple(
            subject
            for breakdown in latest_breakdowns
            for subject in breakdown.subjects
            if subject.ranking_eligible
        )
        strongest_subjects = tuple(
            sorted(
                ranked_subjects,
                key=lambda item: (
                    -(item.high_grade_share_pct or 0.0),
                    -(item.pass_grade_share_pct or 0.0),
                    -item.entries_count_total,
                    item.subject,
                ),
            )[:5]
        )
        weakest_subjects = tuple(
            sorted(
                ranked_subjects,
                key=lambda item: (
                    item.high_grade_share_pct or 0.0,
                    item.pass_grade_share_pct or 0.0,
                    -item.entries_count_total,
                    item.subject,
                ),
            )[:5]
        )
        latest_updated_at = _max_optional_datetime(
            tuple(_to_optional_datetime(row.get("updated_at")) for row in rows)
        )
        return SchoolSubjectPerformanceLatest(
            urn=urn,
            strongest_subjects=strongest_subjects,
            weakest_subjects=weakest_subjects,
            stage_breakdowns=latest_breakdowns,
            latest_updated_at=latest_updated_at,
        )

    def get_subject_performance_series(
        self,
        urn: str,
        *,
        include_16_to_18: bool = False,
    ) -> SchoolSubjectPerformanceSeries | None:
        rows = self._load_summary_rows(
            urn=urn,
            include_16_to_18=include_16_to_18,
            error_factory=lambda: SchoolTrendsDataUnavailableError(
                "School trends datastore is unavailable."
            ),
        )
        if rows is None or len(rows) == 0:
            return None

        return SchoolSubjectPerformanceSeries(
            urn=urn,
            rows=_build_group_rows(rows),
            latest_updated_at=_max_optional_datetime(
                tuple(_to_optional_datetime(row.get("updated_at")) for row in rows)
            ),
        )

    def _load_summary_rows(
        self,
        *,
        urn: str,
        include_16_to_18: bool,
        error_factory,
    ) -> tuple[Mapping[str, object], ...] | None:
        key_stages = _visible_key_stages(include_16_to_18=include_16_to_18)
        try:
            with self._engine.connect() as connection:
                if not _school_exists(connection, urn):
                    return None
                rows = tuple(
                    cast(Mapping[str, object], row)
                    for row in connection.execute(
                        text(
                            """
                            SELECT
                                academic_year,
                                key_stage,
                                qualification_family,
                                exam_cohort,
                                subject,
                                source_version,
                                entries_count_total,
                                high_grade_count,
                                high_grade_share_pct,
                                pass_grade_count,
                                pass_grade_share_pct,
                                ranking_eligible,
                                updated_at
                            FROM school_subject_summary_yearly
                            WHERE urn = :urn
                              AND key_stage = ANY(:key_stages)
                            ORDER BY
                                substring(academic_year from 1 for 4)::integer ASC,
                                academic_year ASC,
                                key_stage ASC,
                                qualification_family ASC,
                                coalesce(exam_cohort, '') ASC,
                                subject ASC
                            """
                        ),
                        {
                            "urn": urn,
                            "key_stages": list(key_stages),
                        },
                    ).mappings()
                )
        except SQLAlchemyError as exc:
            raise error_factory() from exc
        return rows


def materialize_school_subject_summaries(
    connection: Connection,
    *,
    key_stage: SubjectPerformanceKeyStage,
) -> int:
    delete_existing = text(
        """
        DELETE FROM school_subject_summary_yearly
        WHERE key_stage = :key_stage
        """
    )
    connection.execute(delete_existing, {"key_stage": key_stage})
    insert_statement = (
        _ks4_subject_summary_insert_statement()
        if key_stage == "ks4"
        else _sixteen_to_eighteen_subject_summary_insert_statement()
    )
    connection.execute(insert_statement)
    return int(
        connection.execute(
            text(
                """
                SELECT count(*)
                FROM school_subject_summary_yearly
                WHERE key_stage = :key_stage
                """
            ),
            {"key_stage": key_stage},
        ).scalar_one()
    )


def _ks4_subject_summary_insert_statement():
    return text(
        f"""
        WITH version_candidates AS (
            SELECT
                urn,
                academic_year,
                qualification_family,
                subject,
                source_version,
                max(source_downloaded_at_utc) AS source_downloaded_at_utc,
                row_number() OVER (
                    PARTITION BY urn, academic_year, qualification_family, subject
                    ORDER BY
                        {_source_version_priority_sql("source_version")},
                        max(source_downloaded_at_utc) DESC,
                        source_version DESC
                ) AS version_rank
            FROM school_ks4_subject_results_yearly
            GROUP BY
                urn,
                academic_year,
                qualification_family,
                subject,
                source_version
        ),
        selected_rows AS (
            SELECT detail.*
            FROM school_ks4_subject_results_yearly AS detail
            INNER JOIN version_candidates AS versions
                ON versions.urn = detail.urn
               AND versions.academic_year = detail.academic_year
               AND versions.qualification_family = detail.qualification_family
               AND versions.subject = detail.subject
               AND versions.source_version = detail.source_version
            WHERE versions.version_rank = 1
        ),
        aggregated_rows AS (
            SELECT
                urn,
                academic_year,
                'ks4'::text AS key_stage,
                qualification_family,
                ''::text AS exam_cohort,
                subject,
                source_version,
                sum(coalesce(number_achieving, 0))::integer AS entries_count_total,
                bool_and(
                    replace(grade_structure, ' ', '') IN (
                        '9/8/7/6/5/4/3/2/1/U/X',
                        'A/B/C/D/E/U/X',
                        'A*/A/B/C/D/E/U/X'
                    )
                ) AS metrics_supported,
                sum(
                    CASE
                        WHEN replace(grade_structure, ' ', '') = '9/8/7/6/5/4/3/2/1/U/X'
                             AND grade IN ('7', '8', '9')
                            THEN coalesce(number_achieving, 0)
                        WHEN replace(grade_structure, ' ', '') IN (
                            'A/B/C/D/E/U/X',
                            'A*/A/B/C/D/E/U/X'
                        )
                             AND grade IN ('A*', 'A')
                            THEN coalesce(number_achieving, 0)
                        ELSE 0
                    END
                )::integer AS high_grade_count_value,
                sum(
                    CASE
                        WHEN replace(grade_structure, ' ', '') = '9/8/7/6/5/4/3/2/1/U/X'
                             AND grade IN ('4', '5', '6', '7', '8', '9')
                            THEN coalesce(number_achieving, 0)
                        WHEN replace(grade_structure, ' ', '') IN (
                            'A/B/C/D/E/U/X',
                            'A*/A/B/C/D/E/U/X'
                        )
                             AND grade IN ('A*', 'A', 'B', 'C')
                            THEN coalesce(number_achieving, 0)
                        ELSE 0
                    END
                )::integer AS pass_grade_count_value
            FROM selected_rows
            GROUP BY
                urn,
                academic_year,
                qualification_family,
                subject,
                source_version
        )
        INSERT INTO school_subject_summary_yearly (
            urn,
            academic_year,
            key_stage,
            qualification_family,
            exam_cohort,
            subject,
            source_version,
            entries_count_total,
            high_grade_count,
            high_grade_share_pct,
            pass_grade_count,
            pass_grade_share_pct,
            ranking_eligible,
            updated_at
        )
        SELECT
            urn,
            academic_year,
            key_stage,
            qualification_family,
            exam_cohort,
            subject,
            source_version,
            entries_count_total,
            CASE
                WHEN metrics_supported THEN high_grade_count_value
                ELSE NULL
            END AS high_grade_count,
            CASE
                WHEN metrics_supported AND entries_count_total > 0 THEN
                    round((high_grade_count_value::numeric * 100.0) / entries_count_total::numeric, 4)
                ELSE NULL
            END AS high_grade_share_pct,
            CASE
                WHEN metrics_supported THEN pass_grade_count_value
                ELSE NULL
            END AS pass_grade_count,
            CASE
                WHEN metrics_supported AND entries_count_total > 0 THEN
                    round((pass_grade_count_value::numeric * 100.0) / entries_count_total::numeric, 4)
                ELSE NULL
            END AS pass_grade_share_pct,
            (
                metrics_supported
                AND qualification_family = 'gcse'
                AND subject <> 'All subjects'
                AND entries_count_total >= 5
            ) AS ranking_eligible,
            timezone('utc', now()) AS updated_at
        FROM aggregated_rows
        """
    )


def _sixteen_to_eighteen_subject_summary_insert_statement():
    return text(
        f"""
        WITH version_candidates AS (
            SELECT
                urn,
                academic_year,
                qualification_family,
                exam_cohort,
                subject,
                source_version,
                max(source_downloaded_at_utc) AS source_downloaded_at_utc,
                row_number() OVER (
                    PARTITION BY urn, academic_year, qualification_family, exam_cohort, subject
                    ORDER BY
                        {_source_version_priority_sql("source_version")},
                        max(source_downloaded_at_utc) DESC,
                        source_version DESC
                ) AS version_rank
            FROM school_16_to_18_subject_results_yearly
            GROUP BY
                urn,
                academic_year,
                qualification_family,
                exam_cohort,
                subject,
                source_version
        ),
        selected_rows AS (
            SELECT detail.*
            FROM school_16_to_18_subject_results_yearly AS detail
            INNER JOIN version_candidates AS versions
                ON versions.urn = detail.urn
               AND versions.academic_year = detail.academic_year
               AND versions.qualification_family = detail.qualification_family
               AND versions.exam_cohort = detail.exam_cohort
               AND versions.subject = detail.subject
               AND versions.source_version = detail.source_version
            WHERE versions.version_rank = 1
        ),
        aggregated_rows AS (
            SELECT
                urn,
                academic_year,
                '16_to_18'::text AS key_stage,
                qualification_family,
                exam_cohort,
                subject,
                source_version,
                sum(coalesce(entries_count, 0))::integer AS entries_count_total,
                bool_and(
                    replace(grade_structure, ' ', '') IN (
                        '*,A,B,C,D,E',
                        'A,B,C,D,E',
                        '*,A,B,C,D'
                    )
                ) AS metrics_supported,
                sum(
                    CASE
                        WHEN replace(grade_structure, ' ', '') = '*,A,B,C,D,E'
                             AND grade IN ('A*', 'A')
                            THEN coalesce(entries_count, 0)
                        WHEN replace(grade_structure, ' ', '') = 'A,B,C,D,E'
                             AND grade IN ('A')
                            THEN coalesce(entries_count, 0)
                        WHEN replace(grade_structure, ' ', '') = '*,A,B,C,D'
                             AND grade IN ('A*', 'A')
                            THEN coalesce(entries_count, 0)
                        ELSE 0
                    END
                )::integer AS high_grade_count_value,
                sum(
                    CASE
                        WHEN replace(grade_structure, ' ', '') = '*,A,B,C,D,E'
                             AND grade IN ('A*', 'A', 'B', 'C', 'D', 'E')
                            THEN coalesce(entries_count, 0)
                        WHEN replace(grade_structure, ' ', '') = 'A,B,C,D,E'
                             AND grade IN ('A', 'B', 'C', 'D', 'E')
                            THEN coalesce(entries_count, 0)
                        WHEN replace(grade_structure, ' ', '') = '*,A,B,C,D'
                             AND grade IN ('A*', 'A', 'B', 'C', 'D')
                            THEN coalesce(entries_count, 0)
                        ELSE 0
                    END
                )::integer AS pass_grade_count_value
            FROM selected_rows
            GROUP BY
                urn,
                academic_year,
                qualification_family,
                exam_cohort,
                subject,
                source_version
        )
        INSERT INTO school_subject_summary_yearly (
            urn,
            academic_year,
            key_stage,
            qualification_family,
            exam_cohort,
            subject,
            source_version,
            entries_count_total,
            high_grade_count,
            high_grade_share_pct,
            pass_grade_count,
            pass_grade_share_pct,
            ranking_eligible,
            updated_at
        )
        SELECT
            urn,
            academic_year,
            key_stage,
            qualification_family,
            exam_cohort,
            subject,
            source_version,
            entries_count_total,
            CASE
                WHEN metrics_supported THEN high_grade_count_value
                ELSE NULL
            END AS high_grade_count,
            CASE
                WHEN metrics_supported AND entries_count_total > 0 THEN
                    round((high_grade_count_value::numeric * 100.0) / entries_count_total::numeric, 4)
                ELSE NULL
            END AS high_grade_share_pct,
            CASE
                WHEN metrics_supported THEN pass_grade_count_value
                ELSE NULL
            END AS pass_grade_count,
            CASE
                WHEN metrics_supported AND entries_count_total > 0 THEN
                    round((pass_grade_count_value::numeric * 100.0) / entries_count_total::numeric, 4)
                ELSE NULL
            END AS pass_grade_share_pct,
            (
                metrics_supported
                AND qualification_family = 'a_level'
                AND lower(exam_cohort) = 'a level'
                AND subject <> 'All subjects'
                AND entries_count_total >= 5
            ) AS ranking_eligible,
            timezone('utc', now()) AS updated_at
        FROM aggregated_rows
        """
    )


def _build_latest_breakdowns(
    rows: Sequence[Mapping[str, object]],
) -> tuple[SchoolSubjectPerformanceGroupRow, ...]:
    latest_year_by_stage: dict[SubjectPerformanceKeyStage, str] = {}
    for row in rows:
        key_stage = _parse_key_stage(row["key_stage"])
        academic_year = str(row["academic_year"])
        current = latest_year_by_stage.get(key_stage)
        if current is None or _academic_year_sort_key(current) < _academic_year_sort_key(
            academic_year
        ):
            latest_year_by_stage[key_stage] = academic_year
    latest_rows = tuple(
        row
        for row in rows
        if latest_year_by_stage.get(_parse_key_stage(row["key_stage"])) == str(row["academic_year"])
    )
    return _build_group_rows(latest_rows)


def _build_group_rows(
    rows: Sequence[Mapping[str, object]],
) -> tuple[SchoolSubjectPerformanceGroupRow, ...]:
    subjects_by_group: dict[
        tuple[str, SubjectPerformanceKeyStage, str, str, str | None],
        list[SchoolSubjectSummary],
    ] = defaultdict(list)
    for row in rows:
        summary = _to_subject_summary(row)
        subjects_by_group[
            (
                summary.academic_year,
                summary.key_stage,
                summary.qualification_family,
                summary.exam_cohort or "",
                summary.exam_cohort,
            )
        ].append(summary)

    grouped_rows = [
        SchoolSubjectPerformanceGroupRow(
            academic_year=academic_year,
            key_stage=key_stage,
            qualification_family=qualification_family,
            exam_cohort=exam_cohort,
            subjects=tuple(
                sorted(
                    subject_rows,
                    key=lambda item: (
                        -(item.high_grade_share_pct or 0.0),
                        -(item.pass_grade_share_pct or 0.0),
                        -item.entries_count_total,
                        item.subject,
                    ),
                )
            ),
        )
        for (
            academic_year,
            key_stage,
            qualification_family,
            _exam_cohort_sort_key,
            exam_cohort,
        ), subject_rows in subjects_by_group.items()
    ]
    return tuple(
        sorted(
            grouped_rows,
            key=lambda item: (
                _academic_year_sort_key(item.academic_year),
                _PUBLIC_KEY_STAGE_ORDER.index(item.key_stage),
                item.qualification_family,
                item.exam_cohort or "",
            ),
        )
    )


def _to_subject_summary(row: Mapping[str, object]) -> SchoolSubjectSummary:
    return SchoolSubjectSummary(
        academic_year=str(row["academic_year"]),
        key_stage=_parse_key_stage(row["key_stage"]),
        qualification_family=str(row["qualification_family"]),
        exam_cohort=_to_optional_str(row.get("exam_cohort")),
        subject=str(row["subject"]),
        source_version=str(row["source_version"]),
        entries_count_total=_required_int(row["entries_count_total"]),
        high_grade_count=_to_optional_int(row.get("high_grade_count")),
        high_grade_share_pct=_to_optional_float(row.get("high_grade_share_pct")),
        pass_grade_count=_to_optional_int(row.get("pass_grade_count")),
        pass_grade_share_pct=_to_optional_float(row.get("pass_grade_share_pct")),
        ranking_eligible=bool(row["ranking_eligible"]),
    )


def _visible_key_stages(*, include_16_to_18: bool) -> tuple[SubjectPerformanceKeyStage, ...]:
    if include_16_to_18:
        return ("ks4", "16_to_18")
    return ("ks4",)


def _school_exists(connection: Connection, urn: str) -> bool:
    return bool(
        connection.execute(
            text(
                """
                SELECT EXISTS(
                    SELECT 1
                    FROM schools
                    WHERE urn = :urn
                )
                """
            ),
            {"urn": urn},
        ).scalar_one()
    )


def _parse_key_stage(value: object) -> SubjectPerformanceKeyStage:
    token = str(value).strip()
    if token == "ks4":
        return "ks4"
    if token == "16_to_18":
        return "16_to_18"
    raise ValueError(f"Unsupported key stage '{token}'.")


def _source_version_priority_sql(column_name: str) -> str:
    return (
        f"CASE lower(trim({column_name})) "
        "WHEN 'final' THEN 1 "
        "WHEN 'revised' THEN 2 "
        "WHEN 'provisional' THEN 3 "
        "ELSE 4 END"
    )


def _academic_year_sort_key(value: str) -> tuple[int, str]:
    try:
        return int(value.split("/", maxsplit=1)[0]), value
    except (ValueError, IndexError):
        return -1, value


def _max_optional_datetime(values: tuple[datetime | None, ...]) -> datetime | None:
    non_null_values = [value for value in values if value is not None]
    if not non_null_values:
        return None
    return max(non_null_values)


def _to_optional_datetime(value: object) -> datetime | None:
    if isinstance(value, datetime):
        return value
    return None


def _to_optional_str(value: object) -> str | None:
    if value is None:
        return None
    token = str(value).strip()
    return token or None


def _to_optional_int(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        return int(stripped)
    return None


def _required_int(value: object) -> int:
    parsed = _to_optional_int(value)
    if parsed is None:
        raise ValueError("Expected integer value.")
    return parsed


def _to_optional_float(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float, Decimal)):
        return float(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        return float(stripped)
    return None
