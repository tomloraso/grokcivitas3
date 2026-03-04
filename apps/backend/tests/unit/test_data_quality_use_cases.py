from __future__ import annotations

from datetime import date, datetime, timezone

from civitas.application.operations.use_cases import (
    DataQualitySloConfig,
    EvaluateDataQualityAlertsUseCase,
    GenerateDataQualitySnapshotsUseCase,
    RunDataQualitySloCheckUseCase,
)
from civitas.domain.operations.models import CoverageDrift, DataQualitySnapshot, PipelineRunHealth


class FakeDataQualityRepository:
    def __init__(self) -> None:
        self.collected_snapshots: tuple[DataQualitySnapshot, ...] = ()
        self.persisted_snapshots: tuple[DataQualitySnapshot, ...] = ()
        self.current_snapshots: tuple[DataQualitySnapshot, ...] = ()
        self.previous_snapshots: dict[tuple[str, str, str], DataQualitySnapshot] = {}
        self.coverage_drifts: tuple[CoverageDrift, ...] = ()
        self.run_health: tuple[PipelineRunHealth, ...] = ()

    def collect_snapshots(
        self,
        *,
        snapshot_date: date,
        as_of: datetime,
    ) -> tuple[DataQualitySnapshot, ...]:
        _ = snapshot_date, as_of
        return self.collected_snapshots

    def upsert_snapshots(self, snapshots: tuple[DataQualitySnapshot, ...]) -> None:
        self.persisted_snapshots = snapshots
        self.current_snapshots = snapshots

    def list_snapshots(self, *, snapshot_date: date) -> tuple[DataQualitySnapshot, ...]:
        _ = snapshot_date
        return self.current_snapshots

    def get_previous_snapshot(
        self,
        *,
        source: str,
        dataset: str,
        section: str,
        before_date: date,
    ) -> DataQualitySnapshot | None:
        _ = before_date
        return self.previous_snapshots.get((source, dataset, section))

    def list_coverage_drifts(self, *, snapshot_date: date) -> tuple[CoverageDrift, ...]:
        _ = snapshot_date
        return self.coverage_drifts

    def list_pipeline_run_health(self) -> tuple[PipelineRunHealth, ...]:
        return self.run_health


def _snapshot(
    *,
    snapshot_date: date,
    source: str = "dfe_characteristics",
    dataset: str = "school_demographics_yearly",
    section: str = "demographics",
    source_lag: float | None = 12.0,
    coverage_ratio: float = 0.9,
    total_schools: int = 100,
    with_section: int = 90,
    zero_years: int = 10,
    one_year: int = 10,
    two_plus_years: int = 80,
) -> DataQualitySnapshot:
    as_of = datetime(2026, 3, 3, 12, 0, tzinfo=timezone.utc)
    updated_at = as_of
    if source_lag is not None:
        updated_at = as_of.replace(hour=0)
    return DataQualitySnapshot(
        snapshot_date=snapshot_date,
        source=source,
        dataset=dataset,
        section=section,
        source_updated_at=updated_at,
        section_updated_at=updated_at,
        source_freshness_lag_hours=source_lag,
        section_freshness_lag_hours=source_lag,
        schools_total_count=total_schools,
        schools_with_section_count=with_section,
        section_coverage_ratio=coverage_ratio,
        trends_zero_years_count=zero_years,
        trends_one_year_count=one_year,
        trends_two_plus_years_count=two_plus_years,
        contract_version="contract-v1",
    )


def _config() -> DataQualitySloConfig:
    return DataQualitySloConfig(
        source_freshness_sla_hours={"dfe_characteristics": 24.0},
        max_day_over_day_coverage_drop=0.05,
        max_consecutive_hard_failures=2,
        max_sparse_trend_ratio=0.25,
    )


def test_generate_snapshots_use_case_persists_collected_snapshots() -> None:
    repository = FakeDataQualityRepository()
    expected_snapshot = _snapshot(snapshot_date=date(2026, 3, 3))
    repository.collected_snapshots = (expected_snapshot,)
    use_case = GenerateDataQualitySnapshotsUseCase(repository=repository)

    result = use_case.execute(
        snapshot_date=date(2026, 3, 3),
        as_of=datetime(2026, 3, 3, 9, 0, tzinfo=timezone.utc),
    )

    assert result == (expected_snapshot,)
    assert repository.persisted_snapshots == (expected_snapshot,)


def test_evaluate_alerts_flags_freshness_after_two_consecutive_breaches() -> None:
    repository = FakeDataQualityRepository()
    current = _snapshot(
        snapshot_date=date(2026, 3, 3),
        source_lag=72.0,
    )
    previous = _snapshot(
        snapshot_date=date(2026, 3, 2),
        source_lag=70.0,
    )
    repository.current_snapshots = (current,)
    repository.previous_snapshots[(current.source, current.dataset, current.section)] = previous

    use_case = EvaluateDataQualityAlertsUseCase(repository=repository, slo_config=_config())
    report = use_case.execute(snapshot_date=date(2026, 3, 3))

    assert len(report.alerts) == 1
    assert report.alerts[0].alert_type == "freshness_sla_breach"
    assert report.alerts[0].source == "dfe_characteristics"


def test_evaluate_alerts_flags_coverage_drift_threshold_breach() -> None:
    repository = FakeDataQualityRepository()
    repository.current_snapshots = (_snapshot(snapshot_date=date(2026, 3, 3)),)
    repository.coverage_drifts = (
        CoverageDrift(
            snapshot_date=date(2026, 3, 3),
            source="dfe_characteristics",
            dataset="school_demographics_yearly",
            section="demographics",
            current_coverage_ratio=0.70,
            previous_coverage_ratio=0.90,
            delta_coverage_ratio=-0.20,
        ),
    )

    use_case = EvaluateDataQualityAlertsUseCase(repository=repository, slo_config=_config())
    report = use_case.execute(snapshot_date=date(2026, 3, 3))

    assert len(report.alerts) == 1
    assert report.alerts[0].alert_type == "coverage_drift"
    assert report.alerts[0].threshold_value == 0.05


def test_evaluate_alerts_flags_consecutive_hard_failures() -> None:
    repository = FakeDataQualityRepository()
    repository.current_snapshots = (_snapshot(snapshot_date=date(2026, 3, 3)),)
    repository.run_health = (
        PipelineRunHealth(
            source="dfe_characteristics",
            quality_gate_failures_total=4,
            consecutive_failed_runs=3,
        ),
    )

    use_case = EvaluateDataQualityAlertsUseCase(repository=repository, slo_config=_config())
    report = use_case.execute(snapshot_date=date(2026, 3, 3))

    assert len(report.alerts) == 1
    assert report.alerts[0].alert_type == "quality_gate_instability"
    assert report.alerts[0].observed_value == 3


def test_run_data_quality_slo_check_executes_snapshot_and_alert_paths() -> None:
    repository = FakeDataQualityRepository()
    current = _snapshot(snapshot_date=date(2026, 3, 3))
    repository.collected_snapshots = (current,)
    repository.previous_snapshots[(current.source, current.dataset, current.section)] = _snapshot(
        snapshot_date=date(2026, 3, 2),
        source_lag=1.0,
    )
    repository.run_health = (
        PipelineRunHealth(
            source="dfe_characteristics",
            quality_gate_failures_total=0,
            consecutive_failed_runs=0,
        ),
    )

    snapshot_use_case = GenerateDataQualitySnapshotsUseCase(repository=repository)
    alerts_use_case = EvaluateDataQualityAlertsUseCase(repository=repository, slo_config=_config())
    run_use_case = RunDataQualitySloCheckUseCase(
        snapshot_use_case=snapshot_use_case,
        evaluate_use_case=alerts_use_case,
    )

    report = run_use_case.execute(snapshot_date=date(2026, 3, 3))

    assert report.snapshot_date == date(2026, 3, 3)
    assert report.snapshots == (current,)
