from dataclasses import dataclass
from datetime import datetime
from typing import Literal

TrendCompletenessStatus = Literal["available", "partial", "unavailable"]
TrendCompletenessReasonCode = Literal[
    "source_missing",
    "insufficient_years_published",
    "source_not_in_catalog",
    "source_file_missing_for_year",
    "source_schema_incompatible_for_year",
    "partial_metric_coverage",
    "source_not_provided",
    "rejected_by_validation",
    "not_joined_yet",
    "pipeline_failed_recently",
    "not_applicable",
]


@dataclass(frozen=True)
class SchoolDemographicsYearlyRow:
    academic_year: str
    disadvantaged_pct: float | None
    sen_pct: float | None
    ehcp_pct: float | None
    eal_pct: float | None


@dataclass(frozen=True)
class SchoolDemographicsSeries:
    urn: str
    rows: tuple[SchoolDemographicsYearlyRow, ...]
    latest_updated_at: datetime | None
