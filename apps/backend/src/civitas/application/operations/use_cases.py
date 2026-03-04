from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime, timezone

from civitas.application.operations.ports.data_quality_repository import DataQualityRepository
from civitas.domain.operations.models import (
    CoverageDrift,
    DataQualityAlert,
    DataQualitySnapshot,
    DataQualitySnapshotReport,
    PipelineRunHealth,
)


@dataclass(frozen=True)
class DataQualitySloConfig:
    source_freshness_sla_hours: Mapping[str, float]
    max_day_over_day_coverage_drop: float
    max_consecutive_hard_failures: int
    max_sparse_trend_ratio: float

    def __post_init__(self) -> None:
        if self.max_day_over_day_coverage_drop < 0.0 or self.max_day_over_day_coverage_drop > 1.0:
            raise ValueError("max_day_over_day_coverage_drop must be between 0.0 and 1.0.")
        if self.max_consecutive_hard_failures < 0:
            raise ValueError("max_consecutive_hard_failures must be zero or greater.")
        if self.max_sparse_trend_ratio < 0.0 or self.max_sparse_trend_ratio > 1.0:
            raise ValueError("max_sparse_trend_ratio must be between 0.0 and 1.0.")
        for source, threshold in self.source_freshness_sla_hours.items():
            if threshold <= 0.0:
                raise ValueError(f"Freshness SLA for source '{source}' must be greater than 0.")


class GenerateDataQualitySnapshotsUseCase:
    def __init__(self, repository: DataQualityRepository) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        snapshot_date: date | None = None,
        as_of: datetime | None = None,
    ) -> tuple[DataQualitySnapshot, ...]:
        resolved_as_of = _ensure_utc(as_of) if as_of is not None else datetime.now(timezone.utc)
        resolved_snapshot_date = snapshot_date or resolved_as_of.date()
        snapshots = self._repository.collect_snapshots(
            snapshot_date=resolved_snapshot_date,
            as_of=resolved_as_of,
        )
        self._repository.upsert_snapshots(snapshots)
        return snapshots


class EvaluateDataQualityAlertsUseCase:
    def __init__(
        self,
        repository: DataQualityRepository,
        slo_config: DataQualitySloConfig,
    ) -> None:
        self._repository = repository
        self._slo_config = slo_config

    def execute(self, *, snapshot_date: date) -> DataQualitySnapshotReport:
        snapshots = self._repository.list_snapshots(snapshot_date=snapshot_date)
        coverage_drifts = self._repository.list_coverage_drifts(snapshot_date=snapshot_date)
        run_health = self._repository.list_pipeline_run_health()

        alerts: list[DataQualityAlert] = []
        alerts.extend(
            self._evaluate_freshness_alerts(snapshot_date=snapshot_date, snapshots=snapshots)
        )
        alerts.extend(self._evaluate_coverage_drift_alerts(coverage_drifts))
        alerts.extend(self._evaluate_quality_gate_alerts(run_health))
        alerts.extend(self._evaluate_sparse_trend_alerts(snapshots))

        return DataQualitySnapshotReport(
            snapshot_date=snapshot_date,
            snapshots=snapshots,
            coverage_drifts=coverage_drifts,
            run_health=run_health,
            alerts=tuple(alerts),
        )

    def _evaluate_freshness_alerts(
        self,
        *,
        snapshot_date: date,
        snapshots: tuple[DataQualitySnapshot, ...],
    ) -> list[DataQualityAlert]:
        alerts: list[DataQualityAlert] = []
        seen_sources: set[str] = set()
        for snapshot in snapshots:
            if snapshot.source in seen_sources:
                continue
            seen_sources.add(snapshot.source)

            threshold = self._slo_config.source_freshness_sla_hours.get(snapshot.source)
            if threshold is None or snapshot.source_freshness_lag_hours is None:
                continue
            if snapshot.source_freshness_lag_hours <= threshold:
                continue

            previous = self._repository.get_previous_snapshot(
                source=snapshot.source,
                dataset=snapshot.dataset,
                section=snapshot.section,
                before_date=snapshot_date,
            )
            if previous is None or previous.source_freshness_lag_hours is None:
                continue
            if previous.source_freshness_lag_hours <= threshold:
                continue

            alerts.append(
                DataQualityAlert(
                    alert_type="freshness_sla_breach",
                    severity="critical",
                    source=snapshot.source,
                    section=snapshot.section,
                    message=(
                        f"Source freshness SLA breached for '{snapshot.source}' in two "
                        "consecutive checks."
                    ),
                    observed_value=round(snapshot.source_freshness_lag_hours, 2),
                    threshold_value=threshold,
                )
            )

        return alerts

    def _evaluate_coverage_drift_alerts(
        self,
        coverage_drifts: tuple[CoverageDrift, ...],
    ) -> list[DataQualityAlert]:
        alerts: list[DataQualityAlert] = []
        for drift in coverage_drifts:
            if drift.delta_coverage_ratio is None:
                continue
            coverage_drop = -drift.delta_coverage_ratio
            if coverage_drop <= self._slo_config.max_day_over_day_coverage_drop:
                continue
            alerts.append(
                DataQualityAlert(
                    alert_type="coverage_drift",
                    severity="critical",
                    source=drift.source,
                    section=drift.section,
                    message=(
                        f"Coverage ratio for '{drift.section}' dropped day-over-day by "
                        f"{coverage_drop:.4f}."
                    ),
                    observed_value=round(coverage_drop, 6),
                    threshold_value=self._slo_config.max_day_over_day_coverage_drop,
                )
            )
        return alerts

    def _evaluate_quality_gate_alerts(
        self,
        run_health: tuple[PipelineRunHealth, ...],
    ) -> list[DataQualityAlert]:
        alerts: list[DataQualityAlert] = []
        for metric in run_health:
            if metric.consecutive_failed_runs <= self._slo_config.max_consecutive_hard_failures:
                continue
            alerts.append(
                DataQualityAlert(
                    alert_type="quality_gate_instability",
                    severity="critical",
                    source=metric.source,
                    section=None,
                    message=(
                        f"Source '{metric.source}' has {metric.consecutive_failed_runs} "
                        "consecutive hard pipeline failures."
                    ),
                    observed_value=metric.consecutive_failed_runs,
                    threshold_value=self._slo_config.max_consecutive_hard_failures,
                )
            )
        return alerts

    def _evaluate_sparse_trend_alerts(
        self,
        snapshots: tuple[DataQualitySnapshot, ...],
    ) -> list[DataQualityAlert]:
        alerts: list[DataQualityAlert] = []
        for snapshot in snapshots:
            if snapshot.section != "demographics":
                continue
            if snapshot.schools_total_count <= 0:
                continue
            sparse_count = snapshot.trends_zero_years_count + snapshot.trends_one_year_count
            sparse_ratio = sparse_count / snapshot.schools_total_count
            if sparse_ratio <= self._slo_config.max_sparse_trend_ratio:
                continue
            alerts.append(
                DataQualityAlert(
                    alert_type="sparse_trend_risk",
                    severity="warning",
                    source=snapshot.source,
                    section=snapshot.section,
                    message=(
                        "Schools with zero or one trend year exceed the configured "
                        "sparse-trend baseline."
                    ),
                    observed_value=round(sparse_ratio, 6),
                    threshold_value=self._slo_config.max_sparse_trend_ratio,
                )
            )
        return alerts


class RunDataQualitySloCheckUseCase:
    def __init__(
        self,
        snapshot_use_case: GenerateDataQualitySnapshotsUseCase,
        evaluate_use_case: EvaluateDataQualityAlertsUseCase,
    ) -> None:
        self._snapshot_use_case = snapshot_use_case
        self._evaluate_use_case = evaluate_use_case

    def execute(
        self,
        *,
        snapshot_date: date | None = None,
        as_of: datetime | None = None,
    ) -> DataQualitySnapshotReport:
        resolved_as_of = _ensure_utc(as_of) if as_of is not None else datetime.now(timezone.utc)
        resolved_snapshot_date = snapshot_date or resolved_as_of.date()
        self._snapshot_use_case.execute(
            snapshot_date=resolved_snapshot_date,
            as_of=resolved_as_of,
        )
        return self._evaluate_use_case.execute(snapshot_date=resolved_snapshot_date)


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
