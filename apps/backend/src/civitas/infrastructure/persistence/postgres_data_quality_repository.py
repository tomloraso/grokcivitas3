from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import cast

from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine

from civitas.application.operations.ports.data_quality_repository import DataQualityRepository
from civitas.domain.operations.models import (
    CoverageDrift,
    DataQualitySection,
    DataQualitySnapshot,
    PipelineRunHealth,
)
from civitas.infrastructure.pipelines.base import PipelineSource

_HARD_FAILURE_STATUSES = {
    "failed_source_unavailable",
    "failed_quality_gate",
    "failed",
}


@dataclass(frozen=True)
class _SectionDefinition:
    source: str
    dataset: str
    section: DataQualitySection


_SECTIONS: tuple[_SectionDefinition, ...] = (
    _SectionDefinition(
        source=PipelineSource.DFE_CHARACTERISTICS.value,
        dataset="school_demographics_yearly",
        section="demographics",
    ),
    _SectionDefinition(
        source=PipelineSource.DFE_ATTENDANCE.value,
        dataset="school_attendance_yearly",
        section="attendance",
    ),
    _SectionDefinition(
        source=PipelineSource.DFE_BEHAVIOUR.value,
        dataset="school_behaviour_yearly",
        section="behaviour",
    ),
    _SectionDefinition(
        source=PipelineSource.DFE_WORKFORCE.value,
        dataset="school_workforce_yearly",
        section="workforce",
    ),
    _SectionDefinition(
        source=PipelineSource.SCHOOL_ADMISSIONS.value,
        dataset="school_admissions_yearly",
        section="admissions",
    ),
    _SectionDefinition(
        source=PipelineSource.SCHOOL_FINANCIAL_BENCHMARKS.value,
        dataset="school_financials_yearly",
        section="finance",
    ),
    _SectionDefinition(
        source=PipelineSource.DFE_WORKFORCE.value,
        dataset="school_leadership_snapshot",
        section="leadership",
    ),
    _SectionDefinition(
        source=PipelineSource.DFE_PERFORMANCE.value,
        dataset="school_performance_yearly",
        section="school_performance",
    ),
    _SectionDefinition(
        source=PipelineSource.OFSTED_LATEST.value,
        dataset="school_ofsted_latest",
        section="ofsted_latest",
    ),
    _SectionDefinition(
        source=PipelineSource.OFSTED_TIMELINE.value,
        dataset="ofsted_inspections",
        section="ofsted_timeline",
    ),
    _SectionDefinition(
        source=PipelineSource.ONS_IMD.value,
        dataset="area_deprivation",
        section="area_deprivation",
    ),
    _SectionDefinition(
        source=PipelineSource.UK_HOUSE_PRICES.value,
        dataset="area_house_price_context",
        section="area_house_prices",
    ),
    _SectionDefinition(
        source=PipelineSource.POLICE_CRIME_CONTEXT.value,
        dataset="area_crime_context",
        section="area_crime",
    ),
)


class PostgresDataQualityRepository(DataQualityRepository):
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def collect_snapshots(
        self,
        *,
        snapshot_date: date,
        as_of: datetime,
    ) -> tuple[DataQualitySnapshot, ...]:
        resolved_as_of = _normalize_datetime(as_of)
        with self._engine.connect() as connection:
            schools_total = int(
                connection.execute(text("SELECT COUNT(*) FROM schools")).scalar_one()
            )
            source_updated_at = {
                str(row["source"]): _to_optional_datetime(row["finished_at"])
                for row in connection.execute(
                    text(
                        """
                        SELECT
                            source,
                            MAX(finished_at) AS finished_at
                        FROM pipeline_runs
                        WHERE status IN ('succeeded', 'skipped_no_change')
                        GROUP BY source
                        """
                    )
                ).mappings()
            }
            contract_versions = {
                str(row["source"]): str(row["contract_version"])
                for row in connection.execute(
                    text(
                        """
                        SELECT DISTINCT ON (source)
                            source,
                            contract_version
                        FROM pipeline_run_events
                        WHERE contract_version IS NOT NULL
                        ORDER BY source, finished_at DESC
                        """
                    )
                ).mappings()
            }
            trends_distribution = self._query_trends_distribution(connection=connection)
            section_metrics = {
                "demographics": self._query_demographics_metrics(connection=connection),
                "attendance": self._query_attendance_metrics(connection=connection),
                "behaviour": self._query_behaviour_metrics(connection=connection),
                "workforce": self._query_workforce_metrics(connection=connection),
                "admissions": self._query_admissions_metrics(connection=connection),
                "finance": self._query_finance_metrics(connection=connection),
                "leadership": self._query_leadership_metrics(connection=connection),
                "school_performance": self._query_school_performance_metrics(connection=connection),
                "ofsted_latest": self._query_ofsted_latest_metrics(connection=connection),
                "ofsted_timeline": self._query_ofsted_timeline_metrics(connection=connection),
                "area_deprivation": self._query_area_deprivation_metrics(connection=connection),
                "area_house_prices": self._query_area_house_price_metrics(connection=connection),
                "area_crime": self._query_area_crime_metrics(connection=connection),
            }

        snapshots: list[DataQualitySnapshot] = []
        for section_def in _SECTIONS:
            schools_with_section, section_updated_at = section_metrics[section_def.section]
            coverage_ratio = 1.0
            if schools_total > 0:
                coverage_ratio = schools_with_section / schools_total

            source_updated = source_updated_at.get(section_def.source)
            source_lag = _compute_lag_hours(source_updated, resolved_as_of)
            section_lag = _compute_lag_hours(section_updated_at, resolved_as_of)

            zero_years = 0
            one_year = 0
            two_plus_years = 0
            if section_def.section == "demographics":
                zero_years, one_year, two_plus_years = trends_distribution

            snapshots.append(
                DataQualitySnapshot(
                    snapshot_date=snapshot_date,
                    source=section_def.source,
                    dataset=section_def.dataset,
                    section=section_def.section,
                    source_updated_at=source_updated,
                    section_updated_at=section_updated_at,
                    source_freshness_lag_hours=source_lag,
                    section_freshness_lag_hours=section_lag,
                    schools_total_count=schools_total,
                    schools_with_section_count=schools_with_section,
                    section_coverage_ratio=coverage_ratio,
                    trends_zero_years_count=zero_years,
                    trends_one_year_count=one_year,
                    trends_two_plus_years_count=two_plus_years,
                    contract_version=contract_versions.get(section_def.source),
                )
            )

        snapshots.sort(key=lambda item: (item.source, item.section))
        return tuple(snapshots)

    def upsert_snapshots(self, snapshots: tuple[DataQualitySnapshot, ...]) -> None:
        if len(snapshots) == 0:
            return

        with self._engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO data_quality_snapshots (
                        snapshot_date,
                        source,
                        dataset,
                        section,
                        source_updated_at,
                        section_updated_at,
                        source_freshness_lag_hours,
                        section_freshness_lag_hours,
                        schools_total_count,
                        schools_with_section_count,
                        section_coverage_ratio,
                        trends_zero_years_count,
                        trends_one_year_count,
                        trends_two_plus_years_count,
                        contract_version,
                        updated_at
                    ) VALUES (
                        :snapshot_date,
                        :source,
                        :dataset,
                        :section,
                        :source_updated_at,
                        :section_updated_at,
                        :source_freshness_lag_hours,
                        :section_freshness_lag_hours,
                        :schools_total_count,
                        :schools_with_section_count,
                        :section_coverage_ratio,
                        :trends_zero_years_count,
                        :trends_one_year_count,
                        :trends_two_plus_years_count,
                        :contract_version,
                        timezone('utc', now())
                    )
                    ON CONFLICT (snapshot_date, source, dataset, section) DO UPDATE
                    SET
                        source_updated_at = EXCLUDED.source_updated_at,
                        section_updated_at = EXCLUDED.section_updated_at,
                        source_freshness_lag_hours = EXCLUDED.source_freshness_lag_hours,
                        section_freshness_lag_hours = EXCLUDED.section_freshness_lag_hours,
                        schools_total_count = EXCLUDED.schools_total_count,
                        schools_with_section_count = EXCLUDED.schools_with_section_count,
                        section_coverage_ratio = EXCLUDED.section_coverage_ratio,
                        trends_zero_years_count = EXCLUDED.trends_zero_years_count,
                        trends_one_year_count = EXCLUDED.trends_one_year_count,
                        trends_two_plus_years_count = EXCLUDED.trends_two_plus_years_count,
                        contract_version = EXCLUDED.contract_version,
                        updated_at = timezone('utc', now())
                    """
                ),
                [
                    {
                        "snapshot_date": snapshot.snapshot_date,
                        "source": snapshot.source,
                        "dataset": snapshot.dataset,
                        "section": snapshot.section,
                        "source_updated_at": snapshot.source_updated_at,
                        "section_updated_at": snapshot.section_updated_at,
                        "source_freshness_lag_hours": snapshot.source_freshness_lag_hours,
                        "section_freshness_lag_hours": snapshot.section_freshness_lag_hours,
                        "schools_total_count": snapshot.schools_total_count,
                        "schools_with_section_count": snapshot.schools_with_section_count,
                        "section_coverage_ratio": snapshot.section_coverage_ratio,
                        "trends_zero_years_count": snapshot.trends_zero_years_count,
                        "trends_one_year_count": snapshot.trends_one_year_count,
                        "trends_two_plus_years_count": snapshot.trends_two_plus_years_count,
                        "contract_version": snapshot.contract_version,
                    }
                    for snapshot in snapshots
                ],
            )

    def list_snapshots(self, *, snapshot_date: date) -> tuple[DataQualitySnapshot, ...]:
        with self._engine.connect() as connection:
            rows = connection.execute(
                text(
                    """
                    SELECT
                        snapshot_date,
                        source,
                        dataset,
                        section,
                        source_updated_at,
                        section_updated_at,
                        source_freshness_lag_hours,
                        section_freshness_lag_hours,
                        schools_total_count,
                        schools_with_section_count,
                        section_coverage_ratio,
                        trends_zero_years_count,
                        trends_one_year_count,
                        trends_two_plus_years_count,
                        contract_version
                    FROM data_quality_snapshots
                    WHERE snapshot_date = :snapshot_date
                    ORDER BY source, section
                    """
                ),
                {"snapshot_date": snapshot_date},
            ).mappings()

            return tuple(self._snapshot_from_row(cast(Mapping[str, object], row)) for row in rows)

    def get_previous_snapshot(
        self,
        *,
        source: str,
        dataset: str,
        section: str,
        before_date: date,
    ) -> DataQualitySnapshot | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    text(
                        """
                        SELECT
                            snapshot_date,
                            source,
                            dataset,
                            section,
                            source_updated_at,
                            section_updated_at,
                            source_freshness_lag_hours,
                            section_freshness_lag_hours,
                            schools_total_count,
                            schools_with_section_count,
                            section_coverage_ratio,
                            trends_zero_years_count,
                            trends_one_year_count,
                            trends_two_plus_years_count,
                            contract_version
                        FROM data_quality_snapshots
                        WHERE source = :source
                          AND dataset = :dataset
                          AND section = :section
                          AND snapshot_date < :before_date
                        ORDER BY snapshot_date DESC
                        LIMIT 1
                        """
                    ),
                    {
                        "source": source,
                        "dataset": dataset,
                        "section": section,
                        "before_date": before_date,
                    },
                )
                .mappings()
                .first()
            )

        if row is None:
            return None
        return self._snapshot_from_row(cast(Mapping[str, object], row))

    def list_coverage_drifts(self, *, snapshot_date: date) -> tuple[CoverageDrift, ...]:
        with self._engine.connect() as connection:
            rows = connection.execute(
                text(
                    """
                    SELECT
                        curr.snapshot_date,
                        curr.source,
                        curr.dataset,
                        curr.section,
                        curr.section_coverage_ratio AS current_coverage_ratio,
                        prev.section_coverage_ratio AS previous_coverage_ratio,
                        CASE
                            WHEN prev.section_coverage_ratio IS NULL THEN NULL
                            ELSE curr.section_coverage_ratio - prev.section_coverage_ratio
                        END AS delta_coverage_ratio
                    FROM data_quality_snapshots AS curr
                    LEFT JOIN LATERAL (
                        SELECT section_coverage_ratio
                        FROM data_quality_snapshots AS prev
                        WHERE prev.source = curr.source
                          AND prev.dataset = curr.dataset
                          AND prev.section = curr.section
                          AND prev.snapshot_date < curr.snapshot_date
                        ORDER BY prev.snapshot_date DESC
                        LIMIT 1
                    ) AS prev ON TRUE
                    WHERE curr.snapshot_date = :snapshot_date
                    ORDER BY curr.source, curr.section
                    """
                ),
                {"snapshot_date": snapshot_date},
            ).mappings()

            return tuple(
                CoverageDrift(
                    snapshot_date=_to_date(row["snapshot_date"]),
                    source=str(row["source"]),
                    dataset=str(row["dataset"]),
                    section=_to_section(row["section"]),
                    current_coverage_ratio=_to_float(row["current_coverage_ratio"]),
                    previous_coverage_ratio=_to_optional_float(row["previous_coverage_ratio"]),
                    delta_coverage_ratio=_to_optional_float(row["delta_coverage_ratio"]),
                )
                for row in rows
            )

    def list_pipeline_run_health(self) -> tuple[PipelineRunHealth, ...]:
        with self._engine.connect() as connection:
            quality_gate_totals = {
                str(row["source"]): int(row["failure_count"])
                for row in connection.execute(
                    text(
                        """
                        SELECT
                            source,
                            COUNT(*) AS failure_count
                        FROM pipeline_run_events
                        WHERE run_status = 'failed_quality_gate'
                        GROUP BY source
                        """
                    )
                ).mappings()
            }
            status_rows = tuple(
                connection.execute(
                    text(
                        """
                        SELECT
                            source,
                            run_status
                        FROM pipeline_run_events
                        ORDER BY source ASC, finished_at DESC, id DESC
                        """
                    )
                ).mappings()
            )

        statuses_by_source: dict[str, list[str]] = {}
        for row in status_rows:
            source = str(row["source"])
            statuses_by_source.setdefault(source, []).append(str(row["run_status"]))

        known_sources = (
            {source.value for source in PipelineSource}
            | set(statuses_by_source.keys())
            | set(quality_gate_totals.keys())
        )
        metrics: list[PipelineRunHealth] = []
        for source in sorted(known_sources):
            consecutive_failed_runs = 0
            for status in statuses_by_source.get(source, []):
                if status not in _HARD_FAILURE_STATUSES:
                    break
                consecutive_failed_runs += 1

            metrics.append(
                PipelineRunHealth(
                    source=source,
                    quality_gate_failures_total=quality_gate_totals.get(source, 0),
                    consecutive_failed_runs=consecutive_failed_runs,
                )
            )

        return tuple(metrics)

    def _query_demographics_metrics(
        self,
        *,
        connection: Connection,
    ) -> tuple[int, datetime | None]:
        count = int(
            connection.execute(
                text("SELECT COUNT(DISTINCT urn) FROM school_demographics_yearly")
            ).scalar_one()
        )
        updated_at = _to_optional_datetime(
            connection.execute(
                text("SELECT MAX(updated_at) FROM school_demographics_yearly")
            ).scalar_one()
        )
        return count, updated_at

    def _query_ofsted_latest_metrics(
        self,
        *,
        connection: Connection,
    ) -> tuple[int, datetime | None]:
        count = int(
            connection.execute(
                text("SELECT COUNT(DISTINCT urn) FROM school_ofsted_latest")
            ).scalar_one()
        )
        updated_at = _to_optional_datetime(
            connection.execute(
                text("SELECT MAX(updated_at) FROM school_ofsted_latest")
            ).scalar_one()
        )
        return count, updated_at

    def _query_attendance_metrics(
        self,
        *,
        connection: Connection,
    ) -> tuple[int, datetime | None]:
        count = int(
            connection.execute(
                text("SELECT COUNT(DISTINCT urn) FROM school_attendance_yearly")
            ).scalar_one()
        )
        updated_at = _to_optional_datetime(
            connection.execute(
                text("SELECT MAX(updated_at) FROM school_attendance_yearly")
            ).scalar_one()
        )
        return count, updated_at

    def _query_behaviour_metrics(
        self,
        *,
        connection: Connection,
    ) -> tuple[int, datetime | None]:
        count = int(
            connection.execute(
                text("SELECT COUNT(DISTINCT urn) FROM school_behaviour_yearly")
            ).scalar_one()
        )
        updated_at = _to_optional_datetime(
            connection.execute(
                text("SELECT MAX(updated_at) FROM school_behaviour_yearly")
            ).scalar_one()
        )
        return count, updated_at

    def _query_workforce_metrics(
        self,
        *,
        connection: Connection,
    ) -> tuple[int, datetime | None]:
        count = int(
            connection.execute(
                text("SELECT COUNT(DISTINCT urn) FROM school_workforce_yearly")
            ).scalar_one()
        )
        updated_at = _to_optional_datetime(
            connection.execute(
                text("SELECT MAX(updated_at) FROM school_workforce_yearly")
            ).scalar_one()
        )
        return count, updated_at

    def _query_finance_metrics(
        self,
        *,
        connection: Connection,
    ) -> tuple[int, datetime | None]:
        count = int(
            connection.execute(
                text("SELECT COUNT(DISTINCT urn) FROM school_financials_yearly")
            ).scalar_one()
        )
        updated_at = _to_optional_datetime(
            connection.execute(
                text("SELECT MAX(updated_at) FROM school_financials_yearly")
            ).scalar_one()
        )
        return count, updated_at

    def _query_admissions_metrics(
        self,
        *,
        connection: Connection,
    ) -> tuple[int, datetime | None]:
        count = int(
            connection.execute(
                text("SELECT COUNT(DISTINCT urn) FROM school_admissions_yearly")
            ).scalar_one()
        )
        updated_at = _to_optional_datetime(
            connection.execute(
                text("SELECT MAX(updated_at) FROM school_admissions_yearly")
            ).scalar_one()
        )
        return count, updated_at

    def _query_leadership_metrics(
        self,
        *,
        connection: Connection,
    ) -> tuple[int, datetime | None]:
        count = int(
            connection.execute(
                text("SELECT COUNT(DISTINCT urn) FROM school_leadership_snapshot")
            ).scalar_one()
        )
        updated_at = _to_optional_datetime(
            connection.execute(
                text("SELECT MAX(updated_at) FROM school_leadership_snapshot")
            ).scalar_one()
        )
        return count, updated_at

    def _query_school_performance_metrics(
        self,
        *,
        connection: Connection,
    ) -> tuple[int, datetime | None]:
        count = int(
            connection.execute(
                text("SELECT COUNT(DISTINCT urn) FROM school_performance_yearly")
            ).scalar_one()
        )
        updated_at = _to_optional_datetime(
            connection.execute(
                text("SELECT MAX(updated_at) FROM school_performance_yearly")
            ).scalar_one()
        )
        return count, updated_at

    def _query_ofsted_timeline_metrics(
        self,
        *,
        connection: Connection,
    ) -> tuple[int, datetime | None]:
        count = int(
            connection.execute(
                text("SELECT COUNT(DISTINCT urn) FROM ofsted_inspections")
            ).scalar_one()
        )
        updated_at = _to_optional_datetime(
            connection.execute(text("SELECT MAX(updated_at) FROM ofsted_inspections")).scalar_one()
        )
        return count, updated_at

    def _query_area_deprivation_metrics(
        self,
        *,
        connection: Connection,
    ) -> tuple[int, datetime | None]:
        count = int(
            connection.execute(
                text(
                    """
                    SELECT COUNT(DISTINCT schools.urn)
                    FROM schools
                    INNER JOIN postcode_cache
                        ON replace(upper(postcode_cache.postcode), ' ', '') =
                           replace(upper(schools.postcode), ' ', '')
                    INNER JOIN area_deprivation
                        ON area_deprivation.lsoa_code = postcode_cache.lsoa_code
                    WHERE schools.postcode IS NOT NULL
                      AND btrim(schools.postcode) <> ''
                    """
                )
            ).scalar_one()
        )
        updated_at = _to_optional_datetime(
            connection.execute(text("SELECT MAX(updated_at) FROM area_deprivation")).scalar_one()
        )
        return count, updated_at

    def _query_area_crime_metrics(
        self,
        *,
        connection: Connection,
    ) -> tuple[int, datetime | None]:
        count = int(
            connection.execute(
                text("SELECT COUNT(DISTINCT urn) FROM area_crime_context")
            ).scalar_one()
        )
        updated_at = _to_optional_datetime(
            connection.execute(text("SELECT MAX(updated_at) FROM area_crime_context")).scalar_one()
        )
        return count, updated_at

    def _query_area_house_price_metrics(
        self,
        *,
        connection: Connection,
    ) -> tuple[int, datetime | None]:
        count = int(
            connection.execute(
                text(
                    """
                    SELECT COUNT(DISTINCT schools.urn)
                    FROM schools
                    INNER JOIN postcode_cache
                        ON replace(upper(postcode_cache.postcode), ' ', '') =
                           replace(upper(schools.postcode), ' ', '')
                    INNER JOIN area_deprivation
                        ON area_deprivation.lsoa_code = postcode_cache.lsoa_code
                    INNER JOIN area_house_price_context
                        ON area_house_price_context.area_code =
                           area_deprivation.local_authority_district_code
                    WHERE schools.postcode IS NOT NULL
                      AND btrim(schools.postcode) <> ''
                    """
                )
            ).scalar_one()
        )
        updated_at = _to_optional_datetime(
            connection.execute(
                text("SELECT MAX(updated_at) FROM area_house_price_context")
            ).scalar_one()
        )
        return count, updated_at

    def _query_trends_distribution(
        self,
        *,
        connection: Connection,
    ) -> tuple[int, int, int]:
        row = connection.execute(
            text(
                """
                SELECT
                    COALESCE(SUM(CASE WHEN yearly_counts.years_count = 0 THEN 1 ELSE 0 END), 0)
                        AS zero_years_count,
                    COALESCE(SUM(CASE WHEN yearly_counts.years_count = 1 THEN 1 ELSE 0 END), 0)
                        AS one_year_count,
                    COALESCE(SUM(CASE WHEN yearly_counts.years_count >= 2 THEN 1 ELSE 0 END), 0)
                        AS two_plus_years_count
                FROM (
                    SELECT
                        schools.urn,
                        COUNT(DISTINCT demographics.academic_year) AS years_count
                    FROM schools
                    LEFT JOIN school_demographics_yearly AS demographics
                        ON demographics.urn = schools.urn
                    GROUP BY schools.urn
                ) AS yearly_counts
                """
            )
        ).mappings()
        first = row.first()
        if first is None:
            return (0, 0, 0)
        return (
            int(first["zero_years_count"]),
            int(first["one_year_count"]),
            int(first["two_plus_years_count"]),
        )

    def _snapshot_from_row(self, row: Mapping[str, object]) -> DataQualitySnapshot:
        return DataQualitySnapshot(
            snapshot_date=_to_date(row["snapshot_date"]),
            source=str(row["source"]),
            dataset=str(row["dataset"]),
            section=_to_section(row["section"]),
            source_updated_at=_to_optional_datetime(row["source_updated_at"]),
            section_updated_at=_to_optional_datetime(row["section_updated_at"]),
            source_freshness_lag_hours=_to_optional_float(row["source_freshness_lag_hours"]),
            section_freshness_lag_hours=_to_optional_float(row["section_freshness_lag_hours"]),
            schools_total_count=_to_int(row["schools_total_count"]),
            schools_with_section_count=_to_int(row["schools_with_section_count"]),
            section_coverage_ratio=_to_float(row["section_coverage_ratio"]),
            trends_zero_years_count=_to_int(row["trends_zero_years_count"]),
            trends_one_year_count=_to_int(row["trends_one_year_count"]),
            trends_two_plus_years_count=_to_int(row["trends_two_plus_years_count"]),
            contract_version=_to_optional_str(row["contract_version"]),
        )


def _to_optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _to_optional_float(value: object) -> float | None:
    if value is None:
        return None
    return _to_float(value)


def _to_optional_datetime(value: object) -> datetime | None:
    if not isinstance(value, datetime):
        return None
    return _normalize_datetime(value)


def _to_date(value: object) -> date:
    if isinstance(value, date):
        return value
    raise ValueError(f"Expected date value, got: {type(value)!r}")


def _to_int(value: object) -> int:
    if isinstance(value, bool):
        raise ValueError("Expected numeric value, got bool.")
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        return int(value)
    raise ValueError(f"Expected integer-compatible value, got: {type(value)!r}")


def _to_float(value: object) -> float:
    if isinstance(value, bool):
        raise ValueError("Expected numeric value, got bool.")
    if isinstance(value, (float, int)):
        return float(value)
    if isinstance(value, str):
        return float(value)
    raise ValueError(f"Expected float-compatible value, got: {type(value)!r}")


def _to_section(value: object) -> DataQualitySection:
    raw_section = str(value)
    if raw_section not in {
        "demographics",
        "attendance",
        "behaviour",
        "workforce",
        "admissions",
        "finance",
        "leadership",
        "school_performance",
        "ofsted_latest",
        "ofsted_timeline",
        "area_deprivation",
        "area_house_prices",
        "area_crime",
    }:
        raise ValueError(f"Unknown data-quality section: {raw_section}")
    return cast(DataQualitySection, raw_section)


def _normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _compute_lag_hours(updated_at: datetime | None, as_of: datetime) -> float | None:
    if updated_at is None:
        return None
    duration_seconds = (as_of - updated_at).total_seconds()
    if duration_seconds < 0:
        return 0.0
    return duration_seconds / 3600.0
