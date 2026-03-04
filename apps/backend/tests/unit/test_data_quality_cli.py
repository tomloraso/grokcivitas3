from __future__ import annotations

from datetime import date, datetime, timezone

from typer.testing import CliRunner

from civitas.cli.main import app
from civitas.domain.operations.models import (
    DataQualityAlert,
    DataQualitySnapshot,
    DataQualitySnapshotReport,
    PipelineRunHealth,
)


class FakeDataQualitySloCheckUseCase:
    def __init__(self, report: DataQualitySnapshotReport) -> None:
        self._report = report
        self.snapshot_date: date | None = None

    def execute(self, *, snapshot_date: date | None = None) -> DataQualitySnapshotReport:
        self.snapshot_date = snapshot_date
        return self._report


def _snapshot() -> DataQualitySnapshot:
    now = datetime(2026, 3, 3, 12, 0, tzinfo=timezone.utc)
    return DataQualitySnapshot(
        snapshot_date=date(2026, 3, 3),
        source="dfe_characteristics",
        dataset="school_demographics_yearly",
        section="demographics",
        source_updated_at=now,
        section_updated_at=now,
        source_freshness_lag_hours=1.0,
        section_freshness_lag_hours=1.0,
        schools_total_count=10,
        schools_with_section_count=9,
        section_coverage_ratio=0.9,
        trends_zero_years_count=1,
        trends_one_year_count=2,
        trends_two_plus_years_count=7,
        contract_version="v1",
    )


def _report(alerts: tuple[DataQualityAlert, ...]) -> DataQualitySnapshotReport:
    return DataQualitySnapshotReport(
        snapshot_date=date(2026, 3, 3),
        snapshots=(_snapshot(),),
        coverage_drifts=(),
        run_health=(
            PipelineRunHealth(
                source="dfe_characteristics",
                quality_gate_failures_total=0,
                consecutive_failed_runs=0,
            ),
        ),
        alerts=alerts,
    )


def test_ops_data_quality_snapshot_success(monkeypatch) -> None:
    fake_use_case = FakeDataQualitySloCheckUseCase(report=_report(alerts=()))
    monkeypatch.setattr("civitas.cli.main.data_quality_slo_check_use_case", lambda: fake_use_case)

    runner = CliRunner()
    result = runner.invoke(app, ["ops", "data-quality", "snapshot"])

    assert result.exit_code == 0
    assert "alerts: none" in result.stdout
    assert "dfe_characteristics/demographics" in result.stdout


def test_ops_data_quality_snapshot_strict_fails_when_alerts_present(monkeypatch) -> None:
    fake_use_case = FakeDataQualitySloCheckUseCase(
        report=_report(
            alerts=(
                DataQualityAlert(
                    alert_type="coverage_drift",
                    severity="critical",
                    source="dfe_characteristics",
                    section="demographics",
                    message="coverage dropped",
                    observed_value=0.2,
                    threshold_value=0.05,
                ),
            )
        )
    )
    monkeypatch.setattr("civitas.cli.main.data_quality_slo_check_use_case", lambda: fake_use_case)

    runner = CliRunner()
    result = runner.invoke(app, ["ops", "data-quality", "snapshot", "--strict"])

    assert result.exit_code == 1
    assert "coverage_drift" in result.stdout


def test_ops_data_quality_snapshot_parses_snapshot_date(monkeypatch) -> None:
    fake_use_case = FakeDataQualitySloCheckUseCase(report=_report(alerts=()))
    monkeypatch.setattr("civitas.cli.main.data_quality_slo_check_use_case", lambda: fake_use_case)

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["ops", "data-quality", "snapshot", "--snapshot-date", "2026-03-01"],
    )

    assert result.exit_code == 0
    assert fake_use_case.snapshot_date == date(2026, 3, 1)


def test_ops_data_quality_snapshot_strict_allows_warning_alerts(monkeypatch) -> None:
    fake_use_case = FakeDataQualitySloCheckUseCase(
        report=_report(
            alerts=(
                DataQualityAlert(
                    alert_type="sparse_trend_risk",
                    severity="warning",
                    source="dfe_characteristics",
                    section="demographics",
                    message="sparse trend warning",
                    observed_value=0.8,
                    threshold_value=0.7,
                ),
            )
        )
    )
    monkeypatch.setattr("civitas.cli.main.data_quality_slo_check_use_case", lambda: fake_use_case)

    runner = CliRunner()
    result = runner.invoke(app, ["ops", "data-quality", "snapshot", "--strict"])

    assert result.exit_code == 0
    assert "sparse_trend_risk" in result.stdout
