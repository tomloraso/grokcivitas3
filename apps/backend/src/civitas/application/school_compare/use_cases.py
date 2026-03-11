from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import cast
from uuid import UUID

from civitas.application.access.dto import SectionAccessDto
from civitas.application.access.policies import (
    SCHOOL_COMPARE_CORE_REQUIREMENT,
    get_access_requirement,
)
from civitas.application.access.use_cases import EvaluateAccessUseCase
from civitas.application.school_compare.dto import (
    SchoolCompareBenchmarkDto,
    SchoolCompareCellDto,
    SchoolCompareResponseDto,
    SchoolCompareRowDto,
    SchoolCompareSchoolDto,
    SchoolCompareSectionDto,
)
from civitas.application.school_compare.errors import (
    InvalidSchoolCompareParametersError,
    SchoolCompareDataUnavailableError,
    SchoolCompareNotFoundError,
)
from civitas.application.school_profiles.errors import SchoolProfileDataUnavailableError
from civitas.application.school_profiles.ports.school_profile_repository import (
    SchoolProfileRepository,
)
from civitas.application.school_trends.errors import SchoolTrendsDataUnavailableError
from civitas.application.school_trends.ports.school_trends_repository import (
    SchoolTrendsRepository,
)
from civitas.domain.school_compare.models import (
    COMPARE_METRIC_CATALOG,
    COMPARE_SECTION_LABELS,
    COMPARE_SECTION_ORDER,
    CompareAvailability,
    CompareMetricDefinition,
)
from civitas.domain.school_profiles.models import (
    SchoolPerformanceYear,
    SchoolProfile,
    SchoolProfileSectionCompleteness,
)
from civitas.domain.school_trends.models import SchoolMetricBenchmarkYearlyRow

MIN_COMPARE_SCHOOLS = 2
MAX_COMPARE_SCHOOLS = 4
KS2_METRIC_KEYS = frozenset(
    {
        "ks2_reading_expected_pct",
        "ks2_writing_expected_pct",
        "ks2_maths_expected_pct",
        "ks2_combined_expected_pct",
        "ks2_combined_higher_pct",
    }
)
KS4_METRIC_KEYS = frozenset(
    {
        "attainment8_average",
        "progress8_average",
        "progress8_disadvantaged_gap",
        "engmath_5_plus_pct",
        "ebacc_entry_pct",
    }
)


@dataclass(frozen=True)
class _MetricValue:
    value_text: str | None
    value_numeric: float | int | None
    year_label: str | None
    snapshot_date: date | None


class GetSchoolCompareUseCase:
    def __init__(
        self,
        school_profile_repository: SchoolProfileRepository,
        school_trends_repository: SchoolTrendsRepository,
        evaluate_access_use_case: EvaluateAccessUseCase | None = None,
    ) -> None:
        self._school_profile_repository = school_profile_repository
        self._school_trends_repository = school_trends_repository
        self._evaluate_access_use_case = evaluate_access_use_case

    def execute(
        self,
        *,
        urns: str,
        viewer_user_id: UUID | None = None,
        skip_access_checks: bool = False,
    ) -> SchoolCompareResponseDto:
        normalized_urns = _normalize_requested_urns(urns)
        profiles_by_urn: dict[str, SchoolProfile] = {}
        missing_urns: list[str] = []

        for urn in normalized_urns:
            try:
                profile = self._school_profile_repository.get_school_profile(urn)
            except SchoolProfileDataUnavailableError as exc:
                raise SchoolCompareDataUnavailableError(
                    "School compare datastore is unavailable."
                ) from exc

            if profile is None:
                missing_urns.append(urn)
                continue

            profiles_by_urn[urn] = profile

        if missing_urns:
            raise SchoolCompareNotFoundError(tuple(missing_urns))

        schools = tuple(_build_school_dto(profiles_by_urn[urn]) for urn in normalized_urns)
        access = _resolve_compare_access(
            viewer_user_id=viewer_user_id,
            evaluate_access_use_case=None if skip_access_checks else self._evaluate_access_use_case,
        )
        if access.state == "locked":
            return SchoolCompareResponseDto(
                access=access,
                schools=schools,
                sections=(),
            )

        benchmark_rows_by_urn = {urn: self._latest_benchmark_rows(urn) for urn in normalized_urns}
        has_ks2_data = any(
            _profile_publishes_performance_group(
                profile=profiles_by_urn[urn],
                benchmark_rows=benchmark_rows_by_urn[urn],
                performance_group="ks2",
            )
            for urn in normalized_urns
        )
        has_ks4_data = any(
            _profile_publishes_performance_group(
                profile=profiles_by_urn[urn],
                benchmark_rows=benchmark_rows_by_urn[urn],
                performance_group="ks4",
            )
            for urn in normalized_urns
        )

        sections: list[SchoolCompareSectionDto] = []
        for section_key in COMPARE_SECTION_ORDER:
            rows: list[SchoolCompareRowDto] = []
            for definition in COMPARE_METRIC_CATALOG:
                if definition.section_key != section_key:
                    continue
                if definition.performance_group == "ks2" and not has_ks2_data:
                    continue
                if definition.performance_group == "ks4" and not has_ks4_data:
                    continue

                cells = tuple(
                    _build_compare_cell(
                        profile=profiles_by_urn[urn],
                        definition=definition,
                        benchmark_row=benchmark_rows_by_urn[urn].get(definition.metric_key),
                    )
                    for urn in normalized_urns
                )
                if all(cell.availability == "unsupported" for cell in cells):
                    continue

                rows.append(
                    SchoolCompareRowDto(
                        metric_key=definition.metric_key,
                        label=definition.label,
                        unit=definition.unit,
                        cells=cells,
                    )
                )

            sections.append(
                SchoolCompareSectionDto(
                    key=section_key,
                    label=COMPARE_SECTION_LABELS[section_key],
                    rows=tuple(rows),
                )
            )

        return SchoolCompareResponseDto(
            access=access,
            schools=schools,
            sections=tuple(sections),
        )

    def _latest_benchmark_rows(self, urn: str) -> dict[str, SchoolMetricBenchmarkYearlyRow]:
        try:
            benchmark_series = self._school_trends_repository.get_metric_benchmark_series(urn)
        except SchoolTrendsDataUnavailableError as exc:
            raise SchoolCompareDataUnavailableError(
                "School compare datastore is unavailable."
            ) from exc

        if benchmark_series is None:
            return {}

        latest_by_metric: dict[str, SchoolMetricBenchmarkYearlyRow] = {}
        for row in benchmark_series.rows:
            existing = latest_by_metric.get(row.metric_key)
            if existing is None or _academic_year_sort_key(existing.academic_year) < (
                _academic_year_sort_key(row.academic_year)
            ):
                latest_by_metric[row.metric_key] = row
        return latest_by_metric


def _normalize_requested_urns(raw_urns: str) -> tuple[str, ...]:
    parts = [part.strip() for part in raw_urns.split(",")] if raw_urns else []
    if not parts or any(part == "" for part in parts):
        raise InvalidSchoolCompareParametersError("Compare requires between 2 and 4 unique URNs.")

    if len(parts) < MIN_COMPARE_SCHOOLS or len(parts) > MAX_COMPARE_SCHOOLS:
        raise InvalidSchoolCompareParametersError("Compare requires between 2 and 4 unique URNs.")

    if len(set(parts)) != len(parts):
        raise InvalidSchoolCompareParametersError("Compare requires unique URNs.")

    return tuple(parts)


def _resolve_compare_access(
    *,
    viewer_user_id: UUID | None,
    evaluate_access_use_case: EvaluateAccessUseCase | None,
) -> SectionAccessDto:
    requirement = get_access_requirement(SCHOOL_COMPARE_CORE_REQUIREMENT)
    if evaluate_access_use_case is None:
        return SectionAccessDto(
            state="available",
            capability_key=requirement.capability_key,
            reason_code=None,
            product_codes=(),
            requires_auth=False,
            requires_purchase=False,
        )

    decision = evaluate_access_use_case.execute(
        requirement_key=SCHOOL_COMPARE_CORE_REQUIREMENT,
        user_id=viewer_user_id,
    )
    return SectionAccessDto(
        state=decision.section_state,
        capability_key=decision.capability_key,
        reason_code=decision.reason_code,
        product_codes=decision.available_product_codes,
        requires_auth=decision.requires_auth,
        requires_purchase=decision.requires_purchase,
    )


def _build_school_dto(profile: SchoolProfile) -> SchoolCompareSchoolDto:
    return SchoolCompareSchoolDto(
        urn=profile.school.urn,
        name=profile.school.name,
        postcode=profile.school.postcode,
        phase=profile.school.phase,
        school_type=profile.school.school_type,
        age_range_label=_format_age_range_label(
            low_age=profile.school.statutory_low_age,
            high_age=profile.school.statutory_high_age,
        ),
    )


def _build_compare_cell(
    *,
    profile: SchoolProfile,
    definition: CompareMetricDefinition,
    benchmark_row: SchoolMetricBenchmarkYearlyRow | None,
) -> SchoolCompareCellDto:
    is_supported = _metric_is_supported(
        profile=profile,
        definition=definition,
        benchmark_row=benchmark_row,
    )
    value = _resolve_metric_value(
        profile=profile,
        definition=definition,
        benchmark_row=benchmark_row,
    )
    completeness = _metric_completeness(profile, definition)

    availability: CompareAvailability
    if not is_supported:
        availability = "unsupported"
    elif value.value_text is not None or value.value_numeric is not None:
        availability = "available"
    else:
        availability = "unavailable"

    completeness_status = completeness.status
    completeness_reason_code = completeness.reason_code
    if availability == "unsupported":
        completeness_status = "unavailable"
        completeness_reason_code = "not_applicable"

    return SchoolCompareCellDto(
        urn=profile.school.urn,
        value_text=value.value_text,
        value_numeric=value.value_numeric,
        year_label=value.year_label,
        snapshot_date=value.snapshot_date,
        availability=availability,
        completeness_status=completeness_status,
        completeness_reason_code=completeness_reason_code,
        benchmark=_build_benchmark_dto(definition, benchmark_row),
    )


def _metric_is_supported(
    *,
    profile: SchoolProfile,
    definition: CompareMetricDefinition,
    benchmark_row: SchoolMetricBenchmarkYearlyRow | None,
) -> bool:
    completeness = _metric_completeness(profile, definition)
    if completeness.reason_code == "not_applicable":
        return False

    if definition.metric_key == "fsm6_pct":
        if benchmark_row is not None:
            return True
        latest = profile.demographics_latest
        return latest is None or latest.coverage.fsm6_supported

    if definition.metric_key == "ethnicity_summary":
        latest = profile.demographics_latest
        return latest is None or latest.coverage.ethnicity_supported

    if definition.performance_group is not None:
        if benchmark_row is not None:
            return True
        performance_latest = profile.performance.latest if profile.performance is not None else None
        if _performance_metric_value(performance_latest, definition.metric_key) is not None:
            return True
        return _profile_supports_performance_group(profile, definition.performance_group)

    return True


def _metric_completeness(
    profile: SchoolProfile,
    definition: CompareMetricDefinition,
) -> SchoolProfileSectionCompleteness:
    return cast(
        SchoolProfileSectionCompleteness,
        getattr(profile.completeness, definition.completeness_key),
    )


_FINANCE_METRIC_KEYS = frozenset(
    {
        "total_income_gbp",
        "total_expenditure_gbp",
        "in_year_balance_gbp",
        "finance_income_per_pupil_gbp",
        "finance_expenditure_per_pupil_gbp",
        "finance_staff_costs_pct_of_expenditure",
        "finance_revenue_reserve_per_pupil_gbp",
        "finance_supply_staff_costs_pct_of_staff_costs",
    }
)


def _resolve_metric_value(
    *,
    profile: SchoolProfile,
    definition: CompareMetricDefinition,
    benchmark_row: SchoolMetricBenchmarkYearlyRow | None,
) -> _MetricValue:
    # Finance metrics need ratio→percent conversion, so use dedicated extractor
    # instead of the generic benchmark path (which doesn't convert).
    if definition.metric_key in _FINANCE_METRIC_KEYS:
        return _finance_metric_value(profile, definition)

    if definition.benchmark_supported:
        benchmark_value = _metric_value_from_benchmark(definition, benchmark_row)
        if benchmark_value is not None:
            return benchmark_value

    metric_key = definition.metric_key
    if metric_key == "ofsted_overall_effectiveness":
        return _ofsted_overall_effectiveness_value(profile)
    if metric_key == "most_recent_inspection_date":
        return _most_recent_inspection_value(profile)
    if metric_key == "days_since_most_recent_inspection":
        return _days_since_inspection_value(profile)
    if metric_key in {
        "disadvantaged_pct",
        "fsm_pct",
        "fsm6_pct",
        "sen_pct",
        "ehcp_pct",
        "eal_pct",
    }:
        return _demographics_metric_value(profile, definition)
    if metric_key == "ethnicity_summary":
        return _ethnicity_summary_value(profile)
    if metric_key in {
        "overall_attendance_pct",
        "overall_absence_pct",
        "persistent_absence_pct",
    }:
        return _attendance_metric_value(profile, definition)
    if metric_key in {
        "suspensions_count",
        "suspensions_rate",
        "permanent_exclusions_count",
        "permanent_exclusions_rate",
    }:
        return _behaviour_metric_value(profile, definition)
    if metric_key in {"pupil_teacher_ratio", "supply_staff_pct", "qts_pct"}:
        return _workforce_metric_value(profile, definition)
    if metric_key == "headteacher_name":
        return _headteacher_name_value(profile)
    if metric_key == "headteacher_tenure_years":
        return _headteacher_tenure_value(profile, definition)
    if metric_key in KS2_METRIC_KEYS or metric_key in KS4_METRIC_KEYS:
        return _performance_metric_compare_value(profile, definition)
    if metric_key == "imd_decile":
        return _imd_decile_value(profile, definition)
    if metric_key == "area_crime_incidents_per_1000":
        return _area_crime_value(profile, definition)
    if metric_key in {"area_house_price_average", "area_house_price_annual_change_pct"}:
        return _area_house_price_value(profile, definition)
    return _MetricValue(None, None, None, None)


def _metric_value_from_benchmark(
    definition: CompareMetricDefinition,
    benchmark_row: SchoolMetricBenchmarkYearlyRow | None,
) -> _MetricValue | None:
    if benchmark_row is None or benchmark_row.school_value is None:
        return None

    numeric_value = _coerce_numeric_for_unit(benchmark_row.school_value, definition)
    return _MetricValue(
        value_text=_format_numeric_value(numeric_value, definition),
        value_numeric=numeric_value,
        year_label=benchmark_row.academic_year,
        snapshot_date=None,
    )


def _ofsted_overall_effectiveness_value(profile: SchoolProfile) -> _MetricValue:
    ofsted_latest = profile.ofsted_latest
    if ofsted_latest is None:
        return _MetricValue(None, None, None, None)

    value_text = _clean_text(ofsted_latest.overall_effectiveness_label) or _clean_text(
        ofsted_latest.ungraded_outcome
    )
    snapshot_date = (
        ofsted_latest.most_recent_inspection_date
        or ofsted_latest.inspection_start_date
        or ofsted_latest.publication_date
    )
    return _MetricValue(value_text, None, None, snapshot_date)


def _most_recent_inspection_value(profile: SchoolProfile) -> _MetricValue:
    ofsted_latest = profile.ofsted_latest
    inspection_date = (
        ofsted_latest.most_recent_inspection_date if ofsted_latest is not None else None
    )
    return _MetricValue(
        _format_display_date(inspection_date),
        None,
        None,
        inspection_date,
    )


def _days_since_inspection_value(profile: SchoolProfile) -> _MetricValue:
    ofsted_latest = profile.ofsted_latest
    if ofsted_latest is None or ofsted_latest.days_since_most_recent_inspection is None:
        return _MetricValue(None, None, None, None)

    value_numeric = int(ofsted_latest.days_since_most_recent_inspection)
    return _MetricValue(
        value_text=f"{value_numeric} days",
        value_numeric=value_numeric,
        year_label=None,
        snapshot_date=ofsted_latest.most_recent_inspection_date,
    )


def _demographics_metric_value(
    profile: SchoolProfile,
    definition: CompareMetricDefinition,
) -> _MetricValue:
    latest = profile.demographics_latest
    if latest is None:
        return _MetricValue(None, None, None, None)

    numeric_value = _coerce_numeric_for_unit(getattr(latest, definition.metric_key), definition)
    return _MetricValue(
        value_text=_format_numeric_value(numeric_value, definition),
        value_numeric=numeric_value,
        year_label=latest.academic_year if numeric_value is not None else None,
        snapshot_date=None,
    )


def _ethnicity_summary_value(profile: SchoolProfile) -> _MetricValue:
    latest = profile.demographics_latest
    if latest is None:
        return _MetricValue(None, None, None, None)

    groups = sorted(
        (
            group
            for group in latest.ethnicity_breakdown
            if group.percentage is not None and group.percentage > 0
        ),
        key=lambda item: (-float(item.percentage or 0), item.label),
    )
    top_groups = groups[:3]
    if not top_groups:
        return _MetricValue(None, None, latest.academic_year, None)

    summary = ", ".join(
        f"{group.label} {float(group.percentage or 0.0):.1f}%" for group in top_groups
    )
    return _MetricValue(summary, None, latest.academic_year, None)


def _attendance_metric_value(
    profile: SchoolProfile,
    definition: CompareMetricDefinition,
) -> _MetricValue:
    latest = profile.attendance_latest
    if latest is None:
        return _MetricValue(None, None, None, None)

    numeric_value = _coerce_numeric_for_unit(getattr(latest, definition.metric_key), definition)
    return _MetricValue(
        value_text=_format_numeric_value(numeric_value, definition),
        value_numeric=numeric_value,
        year_label=latest.academic_year if numeric_value is not None else None,
        snapshot_date=None,
    )


def _behaviour_metric_value(
    profile: SchoolProfile,
    definition: CompareMetricDefinition,
) -> _MetricValue:
    latest = profile.behaviour_latest
    if latest is None:
        return _MetricValue(None, None, None, None)

    numeric_value = _coerce_numeric_for_unit(getattr(latest, definition.metric_key), definition)
    return _MetricValue(
        value_text=_format_numeric_value(numeric_value, definition),
        value_numeric=numeric_value,
        year_label=latest.academic_year if numeric_value is not None else None,
        snapshot_date=None,
    )


def _workforce_metric_value(
    profile: SchoolProfile,
    definition: CompareMetricDefinition,
) -> _MetricValue:
    latest = profile.workforce_latest
    if latest is None:
        return _MetricValue(None, None, None, None)

    numeric_value = _coerce_numeric_for_unit(getattr(latest, definition.metric_key), definition)
    return _MetricValue(
        value_text=_format_numeric_value(numeric_value, definition),
        value_numeric=numeric_value,
        year_label=latest.academic_year if numeric_value is not None else None,
        snapshot_date=None,
    )


def _finance_metric_value(
    profile: SchoolProfile,
    definition: CompareMetricDefinition,
) -> _MetricValue:
    latest = profile.finance_latest
    if latest is None:
        return _MetricValue(None, None, None, None)

    # Benchmarked keys use finance_ prefix; strip it for the field lookup
    field_name = definition.metric_key
    if field_name.startswith("finance_"):
        field_name = field_name[len("finance_"):]

    raw_value = getattr(latest, field_name, None)

    # Finance percentages are stored as ratios (0.758 = 75.8%); convert
    if raw_value is not None and definition.unit == "percent":
        raw_value = raw_value * 100.0

    numeric_value = _coerce_numeric_for_unit(raw_value, definition)
    return _MetricValue(
        value_text=_format_numeric_value(numeric_value, definition),
        value_numeric=numeric_value,
        year_label=latest.academic_year if numeric_value is not None else None,
        snapshot_date=None,
    )


def _headteacher_name_value(profile: SchoolProfile) -> _MetricValue:
    leadership = profile.leadership_snapshot
    value_text = _clean_text(leadership.headteacher_name) if leadership is not None else None
    return _MetricValue(value_text, None, None, None)


def _headteacher_tenure_value(
    profile: SchoolProfile,
    definition: CompareMetricDefinition,
) -> _MetricValue:
    leadership = profile.leadership_snapshot
    if leadership is None:
        return _MetricValue(None, None, None, None)

    numeric_value = _coerce_numeric_for_unit(leadership.headteacher_tenure_years, definition)
    return _MetricValue(
        value_text=_format_numeric_value(numeric_value, definition),
        value_numeric=numeric_value,
        year_label=None,
        snapshot_date=None,
    )


def _performance_metric_compare_value(
    profile: SchoolProfile,
    definition: CompareMetricDefinition,
) -> _MetricValue:
    latest = profile.performance.latest if profile.performance is not None else None
    numeric_value = _coerce_numeric_for_unit(
        _performance_metric_value(latest, definition.metric_key),
        definition,
    )
    return _MetricValue(
        value_text=_format_numeric_value(numeric_value, definition),
        value_numeric=numeric_value,
        year_label=latest.academic_year
        if latest is not None and numeric_value is not None
        else None,
        snapshot_date=None,
    )


def _imd_decile_value(
    profile: SchoolProfile,
    definition: CompareMetricDefinition,
) -> _MetricValue:
    deprivation = profile.area_context.deprivation if profile.area_context is not None else None
    numeric_value = deprivation.imd_decile if deprivation is not None else None
    return _MetricValue(
        value_text=_format_numeric_value(numeric_value, definition),
        value_numeric=numeric_value,
        year_label=None,
        snapshot_date=None,
    )


def _area_crime_value(
    profile: SchoolProfile,
    definition: CompareMetricDefinition,
) -> _MetricValue:
    crime = profile.area_context.crime if profile.area_context is not None else None
    if crime is None:
        return _MetricValue(None, None, None, None)

    latest_annual = crime.annual_incidents_per_1000[-1] if crime.annual_incidents_per_1000 else None
    if latest_annual is not None and latest_annual.incidents_per_1000 is not None:
        numeric_value = _coerce_numeric_for_unit(latest_annual.incidents_per_1000, definition)
        return _MetricValue(
            value_text=_format_numeric_value(numeric_value, definition),
            value_numeric=numeric_value,
            year_label=str(latest_annual.year),
            snapshot_date=None,
        )

    numeric_value = _coerce_numeric_for_unit(crime.incidents_per_1000, definition)
    return _MetricValue(
        value_text=_format_numeric_value(numeric_value, definition),
        value_numeric=numeric_value,
        year_label=None,
        snapshot_date=_parse_year_month(crime.latest_month),
    )


def _area_house_price_value(
    profile: SchoolProfile,
    definition: CompareMetricDefinition,
) -> _MetricValue:
    house_prices = profile.area_context.house_prices if profile.area_context is not None else None
    if house_prices is None:
        return _MetricValue(None, None, None, None)

    source_value = (
        house_prices.average_price
        if definition.metric_key == "area_house_price_average"
        else house_prices.annual_change_pct
    )
    numeric_value = _coerce_numeric_for_unit(source_value, definition)
    return _MetricValue(
        value_text=_format_numeric_value(numeric_value, definition),
        value_numeric=numeric_value,
        year_label=None,
        snapshot_date=_parse_year_month(house_prices.latest_month),
    )


def _ratio_to_pct(value: float | None) -> float | None:
    """Convert a 0-1 ratio to 0-100 percent."""
    return value * 100.0 if value is not None else None


def _build_benchmark_dto(
    definition: CompareMetricDefinition,
    benchmark_row: SchoolMetricBenchmarkYearlyRow | None,
) -> SchoolCompareBenchmarkDto | None:
    if not definition.benchmark_supported or benchmark_row is None:
        return None

    # Finance percentages are stored as ratios in the benchmark table
    is_finance_pct = (
        definition.metric_key in _FINANCE_METRIC_KEYS and definition.unit == "percent"
    )
    bm_school = benchmark_row.school_value
    bm_national = benchmark_row.national_value
    bm_local = benchmark_row.local_value
    if is_finance_pct:
        bm_school = _ratio_to_pct(bm_school)
        bm_national = _ratio_to_pct(bm_national)
        bm_local = _ratio_to_pct(bm_local)

    school_value = _coerce_numeric_for_unit(bm_school, definition)
    return SchoolCompareBenchmarkDto(
        academic_year=benchmark_row.academic_year,
        school_value=school_value,
        national_value=bm_national,
        local_value=bm_local,
        school_vs_national_delta=_to_optional_delta(
            bm_school,
            bm_national,
        ),
        school_vs_local_delta=_to_optional_delta(
            bm_school,
            bm_local,
        ),
        local_scope=benchmark_row.local_scope,
        local_area_code=benchmark_row.local_area_code,
        local_area_label=benchmark_row.local_area_label,
    )


def _profile_supports_performance_group(profile: SchoolProfile, performance_group: str) -> bool:
    phase = (profile.school.phase or "").strip().lower()
    if phase:
        if performance_group == "ks2":
            if "all-through" in phase or "primary" in phase:
                return True
            if "secondary" in phase:
                return False
        else:
            if "all-through" in phase or "secondary" in phase:
                return True
            if "primary" in phase:
                return False

    low_age = profile.school.statutory_low_age
    high_age = profile.school.statutory_high_age
    if low_age is not None and high_age is not None:
        if performance_group == "ks2":
            return low_age <= 11 <= high_age
        return low_age <= 14 and high_age >= 16

    if performance_group == "ks2":
        return False
    return False


def _profile_publishes_performance_group(
    *,
    profile: SchoolProfile,
    benchmark_rows: dict[str, SchoolMetricBenchmarkYearlyRow],
    performance_group: str,
) -> bool:
    metric_keys = KS2_METRIC_KEYS if performance_group == "ks2" else KS4_METRIC_KEYS
    latest = profile.performance.latest if profile.performance is not None else None
    return any(
        _performance_metric_value(latest, metric_key) is not None
        or (
            benchmark_rows.get(metric_key) is not None
            and benchmark_rows[metric_key].school_value is not None
        )
        for metric_key in metric_keys
    )


def _performance_metric_value(
    latest: SchoolPerformanceYear | None, metric_key: str
) -> float | None:
    if latest is None:
        return None
    return getattr(latest, metric_key)


def _format_age_range_label(low_age: int | None, high_age: int | None) -> str:
    if low_age is None and high_age is None:
        return "Not published"
    if low_age is None:
        return f"Up to age {high_age}"
    if high_age is None:
        return f"From age {low_age}"
    return f"Ages {low_age}-{high_age}"


def _coerce_numeric_for_unit(
    value: float | int | None,
    definition: CompareMetricDefinition,
) -> float | int | None:
    if value is None:
        return None

    if definition.unit in {"count", "days", "decile"}:
        return int(round(float(value)))

    return float(value)


def _format_numeric_value(
    value: float | int | None,
    definition: CompareMetricDefinition,
) -> str | None:
    if value is None:
        return None

    if definition.unit == "count":
        return f"{int(value):,}"
    if definition.unit == "currency":
        numeric = float(value)
        sign = "-" if numeric < 0 else ""
        abs_val = abs(numeric)
        if abs_val >= 1_000_000:
            return f"{sign}£{abs_val / 1_000_000:.1f}m"
        if abs_val >= 1_000:
            return f"{sign}£{round(abs_val / 1_000):,}k"
        return f"{sign}£{round(abs_val):,}"
    if definition.unit == "percent":
        return f"{float(value):.{definition.decimals or 1}f}%"
    if definition.unit in {"rate", "ratio", "score", "years"}:
        decimals = definition.decimals
        if decimals is None:
            decimals = 1 if definition.unit == "ratio" else 2
        suffix = " years" if definition.unit == "years" else ""
        return f"{float(value):.{decimals}f}{suffix}"
    if definition.unit == "days":
        return f"{int(value)} days"
    if definition.unit == "decile":
        return str(int(value))
    return str(value)


def _parse_year_month(value: str | None) -> date | None:
    if value is None or len(value) != 7:
        return None
    try:
        year_text, month_text = value.split("-", maxsplit=1)
        return date(int(year_text), int(month_text), 1)
    except (TypeError, ValueError):
        return None


def _clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _format_display_date(value: date | None) -> str | None:
    if value is None:
        return None
    return f"{value.day} {value.strftime('%b %Y')}"


def _academic_year_sort_key(value: str) -> tuple[int, str]:
    try:
        start_year = int(value.split("/", maxsplit=1)[0])
    except (IndexError, ValueError):
        start_year = -1
    return start_year, value


def _to_optional_delta(
    school_value: float | int | None,
    benchmark_value: float | None,
) -> float | None:
    if school_value is None or benchmark_value is None:
        return None
    return float(school_value) - float(benchmark_value)
