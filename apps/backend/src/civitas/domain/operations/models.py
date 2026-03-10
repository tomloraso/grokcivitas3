from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal

DataQualitySection = Literal[
    "demographics",
    "attendance",
    "behaviour",
    "workforce",
    "finance",
    "leadership",
    "school_performance",
    "ofsted_latest",
    "ofsted_timeline",
    "area_deprivation",
    "area_crime",
    "area_house_prices",
]

DataQualityAlertType = Literal[
    "freshness_sla_breach",
    "coverage_drift",
    "quality_gate_instability",
    "sparse_trend_risk",
]

DataQualityAlertSeverity = Literal["warning", "critical"]


@dataclass(frozen=True)
class DataQualitySnapshot:
    snapshot_date: date
    source: str
    dataset: str
    section: DataQualitySection
    source_updated_at: datetime | None
    section_updated_at: datetime | None
    source_freshness_lag_hours: float | None
    section_freshness_lag_hours: float | None
    schools_total_count: int
    schools_with_section_count: int
    section_coverage_ratio: float
    trends_zero_years_count: int
    trends_one_year_count: int
    trends_two_plus_years_count: int
    contract_version: str | None


@dataclass(frozen=True)
class CoverageDrift:
    snapshot_date: date
    source: str
    dataset: str
    section: DataQualitySection
    current_coverage_ratio: float
    previous_coverage_ratio: float | None
    delta_coverage_ratio: float | None


@dataclass(frozen=True)
class PipelineRunHealth:
    source: str
    quality_gate_failures_total: int
    consecutive_failed_runs: int


@dataclass(frozen=True)
class DataQualityAlert:
    alert_type: DataQualityAlertType
    severity: DataQualityAlertSeverity
    source: str | None
    section: DataQualitySection | None
    message: str
    observed_value: float | int | None
    threshold_value: float | int | None


@dataclass(frozen=True)
class DataQualitySnapshotReport:
    snapshot_date: date
    snapshots: tuple[DataQualitySnapshot, ...]
    coverage_drifts: tuple[CoverageDrift, ...]
    run_health: tuple[PipelineRunHealth, ...]
    alerts: tuple[DataQualityAlert, ...]
