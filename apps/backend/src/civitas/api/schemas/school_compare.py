from datetime import date
from typing import Literal

from pydantic import BaseModel

from civitas.api.schemas.access import SectionAccessResponse


class SchoolCompareSchoolResponse(BaseModel):
    urn: str
    name: str
    postcode: str | None
    phase: str | None
    type: str | None
    age_range_label: str


class SchoolCompareBenchmarkContextResponse(BaseModel):
    scope: Literal["national", "local_authority_district", "phase", "similar_school"]
    label: str
    value: float | None
    percentile_rank: float | None
    school_count: int | None
    area_code: str | None = None


class SchoolCompareBenchmarkResponse(BaseModel):
    academic_year: str
    school_value: float | int | None
    national_value: float | None
    local_value: float | None
    school_vs_national_delta: float | None
    school_vs_local_delta: float | None
    local_scope: Literal["local_authority_district", "phase"]
    local_area_code: str
    local_area_label: str
    contexts: list[SchoolCompareBenchmarkContextResponse]


class SchoolCompareCellResponse(BaseModel):
    urn: str
    value_text: str | None
    value_numeric: float | int | None
    year_label: str | None
    snapshot_date: date | None
    availability: Literal["available", "unsupported", "unavailable", "suppressed"]
    completeness_status: Literal["available", "partial", "unavailable"]
    completeness_reason_code: (
        Literal[
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
            "source_coverage_gap",
            "stale_after_school_refresh",
            "no_incidents_in_radius",
            "unsupported_stage",
        ]
        | None
    )
    benchmark: SchoolCompareBenchmarkResponse | None


class SchoolCompareRowResponse(BaseModel):
    metric_key: str
    label: str
    unit: Literal[
        "text",
        "date",
        "days",
        "years",
        "percent",
        "count",
        "rate",
        "ratio",
        "score",
        "currency",
        "decile",
    ]
    cells: list[SchoolCompareCellResponse]


class SchoolCompareSectionResponse(BaseModel):
    key: Literal[
        "inspection",
        "demographics",
        "attendance",
        "behaviour",
        "workforce",
        "finance",
        "performance",
        "area",
    ]
    label: str
    rows: list[SchoolCompareRowResponse]


class SchoolCompareResponse(BaseModel):
    access: SectionAccessResponse
    schools: list[SchoolCompareSchoolResponse]
    sections: list[SchoolCompareSectionResponse]
