from datetime import date

import pytest

from civitas.application.school_compare.errors import (
    InvalidSchoolCompareParametersError,
    SchoolCompareNotFoundError,
)
from civitas.application.school_compare.use_cases import GetSchoolCompareUseCase
from civitas.domain.access.models import AccessDecision
from civitas.domain.school_profiles.models import (
    SchoolAdmissionsLatest,
    SchoolAreaContext,
    SchoolAreaContextCoverage,
    SchoolAreaCrime,
    SchoolAreaCrimeAnnualRate,
    SchoolAreaDeprivation,
    SchoolAreaHousePrices,
    SchoolAttendanceLatest,
    SchoolBehaviourLatest,
    SchoolDemographicsCoverage,
    SchoolDemographicsEthnicityGroup,
    SchoolDemographicsLatest,
    SchoolFinanceLatest,
    SchoolLeadershipSnapshot,
    SchoolOfstedLatest,
    SchoolPerformance,
    SchoolPerformanceYear,
    SchoolProfile,
    SchoolProfileCompleteness,
    SchoolProfileSchool,
    SchoolProfileSectionCompleteness,
    SchoolWorkforceLatest,
)
from civitas.domain.school_trends.models import (
    SchoolMetricBenchmarkSeries,
    SchoolMetricBenchmarkYearlyRow,
)


class FakeSchoolProfileRepository:
    def __init__(self, profiles: dict[str, SchoolProfile | None]) -> None:
        self._profiles = profiles
        self.calls: list[str] = []

    def get_school_profile(self, urn: str) -> SchoolProfile | None:
        self.calls.append(urn)
        return self._profiles.get(urn)


class FakeSchoolTrendsRepository:
    def __init__(self, benchmarks: dict[str, SchoolMetricBenchmarkSeries | None]) -> None:
        self._benchmarks = benchmarks
        self.calls: list[str] = []

    def get_metric_benchmark_series(self, urn: str) -> SchoolMetricBenchmarkSeries | None:
        self.calls.append(urn)
        return self._benchmarks.get(urn)


class FakeEvaluateAccessUseCase:
    def __init__(self, decision: AccessDecision) -> None:
        self._decision = decision
        self.calls: list[tuple[str, object | None]] = []

    def execute(self, *, requirement_key: str, user_id: object | None, allow_preview: bool = True):
        self.calls.append((requirement_key, user_id))
        return self._decision


def _section(
    status: str = "available",
    reason_code: str | None = None,
) -> SchoolProfileSectionCompleteness:
    return SchoolProfileSectionCompleteness(
        status=status,
        reason_code=reason_code,
        last_updated_at=None,
        years_available=None,
    )


def _completeness(
    *,
    demographics: tuple[str, str | None] = ("available", None),
    attendance: tuple[str, str | None] = ("available", None),
    behaviour: tuple[str, str | None] = ("available", None),
    workforce: tuple[str, str | None] = ("available", None),
    admissions: tuple[str, str | None] = ("unavailable", "source_missing"),
    finance: tuple[str, str | None] = ("available", None),
    leadership: tuple[str, str | None] = ("available", None),
    performance: tuple[str, str | None] = ("available", None),
    ofsted_latest: tuple[str, str | None] = ("available", None),
    area_deprivation: tuple[str, str | None] = ("available", None),
    area_crime: tuple[str, str | None] = ("available", None),
    area_house_prices: tuple[str, str | None] = ("available", None),
) -> SchoolProfileCompleteness:
    return SchoolProfileCompleteness(
        demographics=_section(*demographics),
        attendance=_section(*attendance),
        behaviour=_section(*behaviour),
        workforce=_section(*workforce),
        admissions=_section(*admissions),
        finance=_section(*finance),
        leadership=_section(*leadership),
        performance=_section(*performance),
        ofsted_latest=_section(*ofsted_latest),
        ofsted_timeline=_section("unavailable", "source_missing"),
        area_deprivation=_section(*area_deprivation),
        area_crime=_section(*area_crime),
        area_house_prices=_section(*area_house_prices),
    )


def _profile(
    *,
    urn: str,
    name: str,
    phase: str,
    low_age: int,
    high_age: int,
    demographics_latest: SchoolDemographicsLatest | None,
    attendance_latest: SchoolAttendanceLatest | None,
    behaviour_latest: SchoolBehaviourLatest | None,
    workforce_latest: SchoolWorkforceLatest | None,
    admissions_latest: SchoolAdmissionsLatest | None,
    leadership_snapshot: SchoolLeadershipSnapshot | None,
    performance: SchoolPerformance | None,
    ofsted_latest: SchoolOfstedLatest | None,
    area_context: SchoolAreaContext | None,
    completeness: SchoolProfileCompleteness,
    finance_latest: SchoolFinanceLatest | None = None,
) -> SchoolProfile:
    return SchoolProfile(
        school=SchoolProfileSchool(
            urn=urn,
            name=name,
            phase=phase,
            school_type="Community school",
            status="Open",
            postcode="SW1A 1AA",
            website=None,
            telephone=None,
            head_title=None,
            head_first_name=None,
            head_last_name=None,
            head_job_title=None,
            address_street=None,
            address_locality=None,
            address_line3=None,
            address_town=None,
            address_county=None,
            statutory_low_age=low_age,
            statutory_high_age=high_age,
            gender=None,
            religious_character=None,
            diocese=None,
            admissions_policy=None,
            sixth_form=None,
            nursery_provision=None,
            boarders=None,
            fsm_pct_gias=None,
            trust_name=None,
            trust_flag=None,
            federation_name=None,
            federation_flag=None,
            la_name="Westminster",
            la_code="213",
            urban_rural=None,
            number_of_boys=None,
            number_of_girls=None,
            lsoa_code="E01004736",
            lsoa_name="Westminster 018A",
            last_changed_date=None,
            lat=51.5,
            lng=-0.14,
        ),
        demographics_latest=demographics_latest,
        attendance_latest=attendance_latest,
        behaviour_latest=behaviour_latest,
        workforce_latest=workforce_latest,
        admissions_latest=admissions_latest,
        finance_latest=finance_latest,
        leadership_snapshot=leadership_snapshot,
        performance=performance,
        ofsted_latest=ofsted_latest,
        ofsted_timeline=None,
        area_context=area_context,
        completeness=completeness,
    )


def _benchmark_series(
    urn: str,
    *rows: tuple[str, str, float | None, float | None, float | None],
) -> SchoolMetricBenchmarkSeries:
    return SchoolMetricBenchmarkSeries(
        urn=urn,
        rows=tuple(
            SchoolMetricBenchmarkYearlyRow(
                metric_key=metric_key,
                academic_year=academic_year,
                school_value=school_value,
                national_value=national_value,
                local_value=local_value,
                local_scope="local_authority_district",
                local_area_code="E09000033",
                local_area_label="Westminster",
            )
            for metric_key, academic_year, school_value, national_value, local_value in rows
        ),
        latest_updated_at=None,
    )


def _row(result, metric_key: str):
    for section in result.sections:
        for row in section.rows:
            if row.metric_key == metric_key:
                return row
    raise AssertionError(f"Missing row {metric_key}")


def _primary_profile() -> SchoolProfile:
    return _profile(
        urn="100001",
        name="Primary Example",
        phase="Primary",
        low_age=4,
        high_age=11,
        demographics_latest=SchoolDemographicsLatest(
            academic_year="2024/25",
            disadvantaged_pct=22.4,
            fsm_pct=20.1,
            fsm6_pct=28.4,
            sen_pct=13.2,
            ehcp_pct=2.1,
            eal_pct=16.4,
            first_language_english_pct=83.6,
            first_language_unclassified_pct=0.4,
            coverage=SchoolDemographicsCoverage(
                fsm_supported=True,
                ethnicity_supported=True,
                top_languages_supported=True,
                fsm6_supported=True,
            ),
            ethnicity_breakdown=(
                SchoolDemographicsEthnicityGroup(
                    key="white_british",
                    label="White British",
                    percentage=48.0,
                    count=96,
                ),
                SchoolDemographicsEthnicityGroup(
                    key="asian_british",
                    label="Asian British",
                    percentage=22.0,
                    count=44,
                ),
                SchoolDemographicsEthnicityGroup(
                    key="black_british",
                    label="Black British",
                    percentage=14.0,
                    count=28,
                ),
            ),
        ),
        attendance_latest=SchoolAttendanceLatest(
            academic_year="2024/25",
            overall_attendance_pct=94.1,
            overall_absence_pct=5.9,
            persistent_absence_pct=13.4,
        ),
        behaviour_latest=SchoolBehaviourLatest(
            academic_year="2024/25",
            suspensions_count=18,
            suspensions_rate=4.2,
            permanent_exclusions_count=0,
            permanent_exclusions_rate=0.0,
        ),
        workforce_latest=SchoolWorkforceLatest(
            academic_year="2024/25",
            pupil_teacher_ratio=18.3,
            supply_staff_pct=2.2,
            teachers_3plus_years_pct=70.0,
            teacher_turnover_pct=9.0,
            qts_pct=96.0,
            qualifications_level6_plus_pct=82.0,
        ),
        admissions_latest=None,
        leadership_snapshot=SchoolLeadershipSnapshot(
            headteacher_name="Ada Jones",
            headteacher_start_date=date(2021, 9, 1),
            headteacher_tenure_years=3.5,
            leadership_turnover_score=1.0,
        ),
        performance=SchoolPerformance(
            latest=SchoolPerformanceYear(
                academic_year="2024/25",
                attainment8_average=None,
                progress8_average=None,
                progress8_disadvantaged=None,
                progress8_not_disadvantaged=None,
                progress8_disadvantaged_gap=None,
                engmath_5_plus_pct=None,
                engmath_4_plus_pct=None,
                ebacc_entry_pct=None,
                ebacc_5_plus_pct=None,
                ebacc_4_plus_pct=None,
                ks2_reading_expected_pct=72.0,
                ks2_writing_expected_pct=70.0,
                ks2_maths_expected_pct=74.0,
                ks2_combined_expected_pct=66.0,
                ks2_reading_higher_pct=18.0,
                ks2_writing_higher_pct=15.0,
                ks2_maths_higher_pct=20.0,
                ks2_combined_higher_pct=12.0,
            ),
            history=(),
        ),
        ofsted_latest=SchoolOfstedLatest(
            overall_effectiveness_code="2",
            overall_effectiveness_label="Good",
            inspection_start_date=date(2025, 10, 10),
            publication_date=date(2025, 11, 15),
            latest_oeif_inspection_start_date=None,
            latest_oeif_publication_date=None,
            quality_of_education_code=None,
            quality_of_education_label=None,
            behaviour_and_attitudes_code=None,
            behaviour_and_attitudes_label=None,
            personal_development_code=None,
            personal_development_label=None,
            leadership_and_management_code=None,
            leadership_and_management_label=None,
            latest_ungraded_inspection_date=None,
            latest_ungraded_publication_date=None,
            most_recent_inspection_date=date(2025, 10, 10),
            days_since_most_recent_inspection=149,
            is_graded=True,
            ungraded_outcome=None,
        ),
        area_context=SchoolAreaContext(
            deprivation=SchoolAreaDeprivation(
                lsoa_code="E01004736",
                imd_score=27.1,
                imd_rank=4825,
                imd_decile=3,
                idaci_score=0.241,
                idaci_decile=2,
                income_score=None,
                income_rank=None,
                income_decile=None,
                employment_score=None,
                employment_rank=None,
                employment_decile=None,
                education_score=None,
                education_rank=None,
                education_decile=None,
                health_score=None,
                health_rank=None,
                health_decile=None,
                crime_score=None,
                crime_rank=None,
                crime_decile=None,
                barriers_score=None,
                barriers_rank=None,
                barriers_decile=None,
                living_environment_score=None,
                living_environment_rank=None,
                living_environment_decile=None,
                population_total=2000,
                local_authority_district_code="E09000033",
                local_authority_district_name="Westminster",
                source_release="IoD2025",
            ),
            crime=SchoolAreaCrime(
                radius_miles=1.0,
                latest_month="2026-01",
                total_incidents=240,
                population_denominator=2000,
                incidents_per_1000=120.0,
                annual_incidents_per_1000=(
                    SchoolAreaCrimeAnnualRate(
                        year=2025,
                        total_incidents=240,
                        incidents_per_1000=120.0,
                    ),
                ),
                categories=(),
            ),
            house_prices=SchoolAreaHousePrices(
                area_code="E09000033",
                area_name="Westminster",
                latest_month="2026-01",
                average_price=810000.0,
                annual_change_pct=6.0,
                monthly_change_pct=None,
                three_year_change_pct=None,
                trend=(),
            ),
            coverage=SchoolAreaContextCoverage(
                has_deprivation=True,
                has_crime=True,
                crime_months_available=12,
                has_house_prices=True,
                house_price_months_available=12,
            ),
        ),
        completeness=_completeness(area_house_prices=("partial", "insufficient_years_published")),
    )


def _secondary_profile() -> SchoolProfile:
    return _profile(
        urn="200002",
        name="Secondary Example",
        phase="Secondary",
        low_age=11,
        high_age=18,
        demographics_latest=SchoolDemographicsLatest(
            academic_year="2024/25",
            disadvantaged_pct=17.2,
            fsm_pct=16.9,
            fsm6_pct=None,
            sen_pct=12.4,
            ehcp_pct=1.9,
            eal_pct=9.2,
            first_language_english_pct=90.8,
            first_language_unclassified_pct=0.8,
            coverage=SchoolDemographicsCoverage(
                fsm_supported=True,
                ethnicity_supported=False,
                top_languages_supported=False,
                fsm6_supported=False,
            ),
            ethnicity_breakdown=(),
        ),
        attendance_latest=SchoolAttendanceLatest(
            academic_year="2024/25",
            overall_attendance_pct=92.8,
            overall_absence_pct=7.2,
            persistent_absence_pct=18.1,
        ),
        behaviour_latest=SchoolBehaviourLatest(
            academic_year="2024/25",
            suspensions_count=121,
            suspensions_rate=16.4,
            permanent_exclusions_count=1,
            permanent_exclusions_rate=0.1,
        ),
        workforce_latest=SchoolWorkforceLatest(
            academic_year="2024/25",
            pupil_teacher_ratio=16.3,
            supply_staff_pct=2.4,
            teachers_3plus_years_pct=76.5,
            teacher_turnover_pct=9.8,
            qts_pct=95.2,
            qualifications_level6_plus_pct=81.1,
        ),
        admissions_latest=None,
        leadership_snapshot=SchoolLeadershipSnapshot(
            headteacher_name="Ben Smith",
            headteacher_start_date=date(2020, 9, 1),
            headteacher_tenure_years=4.5,
            leadership_turnover_score=1.2,
        ),
        performance=SchoolPerformance(
            latest=SchoolPerformanceYear(
                academic_year="2024/25",
                attainment8_average=47.2,
                progress8_average=0.11,
                progress8_disadvantaged=-0.12,
                progress8_not_disadvantaged=0.21,
                progress8_disadvantaged_gap=-0.33,
                engmath_5_plus_pct=52.3,
                engmath_4_plus_pct=71.4,
                ebacc_entry_pct=36.2,
                ebacc_5_plus_pct=25.5,
                ebacc_4_plus_pct=31.3,
                ks2_reading_expected_pct=None,
                ks2_writing_expected_pct=None,
                ks2_maths_expected_pct=None,
                ks2_combined_expected_pct=None,
                ks2_reading_higher_pct=None,
                ks2_writing_higher_pct=None,
                ks2_maths_higher_pct=None,
                ks2_combined_higher_pct=None,
            ),
            history=(),
        ),
        ofsted_latest=SchoolOfstedLatest(
            overall_effectiveness_code=None,
            overall_effectiveness_label=None,
            inspection_start_date=date(2026, 1, 2),
            publication_date=date(2026, 1, 20),
            latest_oeif_inspection_start_date=None,
            latest_oeif_publication_date=None,
            quality_of_education_code=None,
            quality_of_education_label=None,
            behaviour_and_attitudes_code=None,
            behaviour_and_attitudes_label=None,
            personal_development_code=None,
            personal_development_label=None,
            leadership_and_management_code=None,
            leadership_and_management_label=None,
            latest_ungraded_inspection_date=None,
            latest_ungraded_publication_date=None,
            most_recent_inspection_date=date(2026, 1, 2),
            days_since_most_recent_inspection=65,
            is_graded=False,
            ungraded_outcome="Has taken effective action",
        ),
        area_context=SchoolAreaContext(
            deprivation=SchoolAreaDeprivation(
                lsoa_code="E01004737",
                imd_score=19.2,
                imd_rank=7200,
                imd_decile=5,
                idaci_score=0.18,
                idaci_decile=4,
                income_score=None,
                income_rank=None,
                income_decile=None,
                employment_score=None,
                employment_rank=None,
                employment_decile=None,
                education_score=None,
                education_rank=None,
                education_decile=None,
                health_score=None,
                health_rank=None,
                health_decile=None,
                crime_score=None,
                crime_rank=None,
                crime_decile=None,
                barriers_score=None,
                barriers_rank=None,
                barriers_decile=None,
                living_environment_score=None,
                living_environment_rank=None,
                living_environment_decile=None,
                population_total=3000,
                local_authority_district_code="E09000033",
                local_authority_district_name="Westminster",
                source_release="IoD2025",
            ),
            crime=SchoolAreaCrime(
                radius_miles=1.0,
                latest_month="2026-01",
                total_incidents=486,
                population_denominator=3000,
                incidents_per_1000=162.0,
                annual_incidents_per_1000=(
                    SchoolAreaCrimeAnnualRate(
                        year=2025,
                        total_incidents=486,
                        incidents_per_1000=162.0,
                    ),
                ),
                categories=(),
            ),
            house_prices=SchoolAreaHousePrices(
                area_code="E09000033",
                area_name="Westminster",
                latest_month="2026-01",
                average_price=640000.0,
                annual_change_pct=4.1,
                monthly_change_pct=None,
                three_year_change_pct=None,
                trend=(),
            ),
            coverage=SchoolAreaContextCoverage(
                has_deprivation=True,
                has_crime=True,
                crime_months_available=12,
                has_house_prices=True,
                house_price_months_available=12,
            ),
        ),
        completeness=_completeness(),
    )


def test_get_school_compare_returns_aligned_rows_in_request_order() -> None:
    use_case = GetSchoolCompareUseCase(
        school_profile_repository=FakeSchoolProfileRepository(
            {
                "100001": _primary_profile(),
                "200002": _secondary_profile(),
            }
        ),
        school_trends_repository=FakeSchoolTrendsRepository(
            {
                "100001": _benchmark_series(
                    "100001",
                    ("fsm_pct", "2024/25", 20.1, 18.0, 19.2),
                    ("area_crime_incidents_per_1000", "2025", 120.0, 95.0, 110.0),
                    ("area_house_price_average", "2025", 780000.0, 610000.0, 720000.0),
                    ("area_house_price_annual_change_pct", "2025", 5.4, 4.2, 4.8),
                ),
                "200002": _benchmark_series(
                    "200002",
                    ("fsm_pct", "2024/25", 16.9, 18.0, 19.2),
                    ("attainment8_average", "2024/25", 47.2, 46.1, 48.6),
                    ("progress8_average", "2024/25", 0.11, -0.03, 0.08),
                    ("progress8_disadvantaged_gap", "2024/25", -0.33, -0.41, -0.28),
                    ("engmath_5_plus_pct", "2024/25", 52.3, 49.4, 51.0),
                    ("ebacc_entry_pct", "2024/25", 36.2, 38.6, 40.1),
                    ("area_crime_incidents_per_1000", "2025", 162.0, 95.0, 110.0),
                    ("area_house_price_average", "2025", 640000.0, 610000.0, 720000.0),
                    ("area_house_price_annual_change_pct", "2025", 4.1, 4.2, 4.8),
                ),
            }
        ),
    )

    result = use_case.execute(urns="200002, 100001")

    assert result.access.state == "available"
    assert result.access.capability_key == "premium_comparison"
    assert [school.urn for school in result.schools] == ["200002", "100001"]
    assert [section.key for section in result.sections] == [
        "inspection",
        "demographics",
        "attendance",
        "behaviour",
        "workforce",
        "finance",
        "performance",
        "area",
    ]

    ethnicity_row = _row(result, "ethnicity_summary")
    assert ethnicity_row.cells[0].availability == "unsupported"
    assert ethnicity_row.cells[1].availability == "available"
    assert ethnicity_row.cells[1].value_text == (
        "White British 48.0%, Asian British 22.0%, Black British 14.0%"
    )

    fsm_row = _row(result, "fsm_pct")
    assert [cell.urn for cell in fsm_row.cells] == ["200002", "100001"]
    assert fsm_row.cells[0].year_label == "2024/25"
    assert fsm_row.cells[0].benchmark is not None
    assert fsm_row.cells[0].benchmark.local_area_label == "Westminster"
    assert fsm_row.cells[1].value_text == "20.1%"

    ks2_row = _row(result, "ks2_reading_expected_pct")
    assert ks2_row.cells[0].availability == "unsupported"
    assert ks2_row.cells[1].availability == "available"
    assert ks2_row.cells[1].value_numeric == 72.0

    ks4_row = _row(result, "attainment8_average")
    assert ks4_row.cells[0].availability == "available"
    assert ks4_row.cells[0].benchmark is not None
    assert ks4_row.cells[1].availability == "unsupported"

    inspection_date_row = _row(result, "most_recent_inspection_date")
    assert inspection_date_row.cells[0].value_text == "2 Jan 2026"
    assert inspection_date_row.cells[1].value_text == "10 Oct 2025"

    house_price_row = _row(result, "area_house_price_average")
    assert house_price_row.cells[0].year_label == "2025"
    assert house_price_row.cells[0].value_text == "£640k"
    assert house_price_row.cells[1].value_text == "£780k"


def test_get_school_compare_hides_ks2_rows_when_no_school_publishes_ks2_data() -> None:
    secondary_a = _secondary_profile()
    secondary_b = _secondary_profile()
    secondary_b = _profile(
        urn="300003",
        name="Secondary Example 2",
        phase=secondary_b.school.phase or "Secondary",
        low_age=secondary_b.school.statutory_low_age or 11,
        high_age=secondary_b.school.statutory_high_age or 18,
        demographics_latest=secondary_b.demographics_latest,
        attendance_latest=secondary_b.attendance_latest,
        behaviour_latest=secondary_b.behaviour_latest,
        workforce_latest=secondary_b.workforce_latest,
        admissions_latest=secondary_b.admissions_latest,
        leadership_snapshot=secondary_b.leadership_snapshot,
        performance=secondary_b.performance,
        ofsted_latest=secondary_b.ofsted_latest,
        area_context=secondary_b.area_context,
        completeness=secondary_b.completeness,
    )
    use_case = GetSchoolCompareUseCase(
        school_profile_repository=FakeSchoolProfileRepository(
            {"200002": secondary_a, "300003": secondary_b}
        ),
        school_trends_repository=FakeSchoolTrendsRepository(
            {
                "200002": _benchmark_series("200002"),
                "300003": _benchmark_series("300003"),
            }
        ),
    )

    result = use_case.execute(urns="200002,300003")

    assert result.access.state == "available"
    performance_row_keys = [
        row.metric_key
        for row in next(section for section in result.sections if section.key == "performance").rows
    ]
    assert "ks2_reading_expected_pct" not in performance_row_keys
    assert "attainment8_average" in performance_row_keys


def test_get_school_compare_returns_locked_payload_without_metric_sections() -> None:
    evaluate_access_use_case = FakeEvaluateAccessUseCase(
        AccessDecision(
            requirement_key="school_compare.core",
            access_level="preview_only",
            section_state="locked",
            capability_key="premium_comparison",
            reason_code="anonymous_user",
            available_product_codes=("premium_launch",),
            requires_auth=True,
            requires_purchase=False,
        )
    )
    use_case = GetSchoolCompareUseCase(
        school_profile_repository=FakeSchoolProfileRepository(
            {
                "100001": _primary_profile(),
                "200002": _secondary_profile(),
            }
        ),
        school_trends_repository=FakeSchoolTrendsRepository({}),
        evaluate_access_use_case=evaluate_access_use_case,
    )

    result = use_case.execute(urns="100001,200002")

    assert result.access.state == "locked"
    assert result.access.product_codes == ("premium_launch",)
    assert [school.urn for school in result.schools] == ["100001", "200002"]
    assert result.sections == ()


def test_get_school_compare_rejects_invalid_parameters() -> None:
    use_case = GetSchoolCompareUseCase(
        school_profile_repository=FakeSchoolProfileRepository({}),
        school_trends_repository=FakeSchoolTrendsRepository({}),
    )

    with pytest.raises(
        InvalidSchoolCompareParametersError,
        match="Compare requires between 2 and 4 unique URNs.",
    ):
        use_case.execute(urns="100001")

    with pytest.raises(
        InvalidSchoolCompareParametersError,
        match="Compare requires unique URNs.",
    ):
        use_case.execute(urns="100001,100001")


def test_get_school_compare_raises_not_found_for_missing_urns() -> None:
    use_case = GetSchoolCompareUseCase(
        school_profile_repository=FakeSchoolProfileRepository(
            {"100001": _primary_profile(), "999999": None}
        ),
        school_trends_repository=FakeSchoolTrendsRepository(
            {"100001": _benchmark_series("100001")}
        ),
    )

    with pytest.raises(
        SchoolCompareNotFoundError,
        match="School with URN '999999' was not found.",
    ):
        use_case.execute(urns="100001,999999")
