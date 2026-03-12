from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from civitas.api.dependencies import (
    get_school_trend_dashboard_use_case,
    get_school_trends_use_case,
)
from civitas.api.main import app
from civitas.application.school_trends.dto import (
    SchoolBenchmarkContextDto,
    SchoolTrendBenchmarkPointDto,
    SchoolTrendDashboardMetricDto,
    SchoolTrendDashboardResponseDto,
    SchoolTrendDashboardSectionDto,
    SchoolTrendPointDto,
    SchoolTrendsBenchmarksDto,
    SchoolTrendsCompletenessDto,
    SchoolTrendsHistoryQualityDto,
    SchoolTrendsResponseDto,
    SchoolTrendsSectionCompletenessDto,
    SchoolTrendsSeriesDto,
)
from civitas.application.school_trends.errors import (
    SchoolTrendsDataUnavailableError,
    SchoolTrendsNotFoundError,
)
from civitas.application.subject_performance.dto import (
    SchoolSubjectPerformanceGroupRowDto,
    SchoolSubjectPerformanceSeriesDto,
    SchoolSubjectSummaryDto,
)

client = TestClient(app)


class FakeGetSchoolTrendsUseCase:
    def __init__(
        self,
        result: SchoolTrendsResponseDto | None = None,
        error: Exception | None = None,
    ) -> None:
        self._result = result
        self._error = error
        self.calls: list[str] = []

    def execute(self, *, urn: str) -> SchoolTrendsResponseDto:
        self.calls.append(urn)
        if self._error is not None:
            raise self._error
        if self._result is None:
            raise AssertionError("FakeGetSchoolTrendsUseCase configured without result or error")
        return self._result


class FakeGetSchoolTrendDashboardUseCase:
    def __init__(
        self,
        result: SchoolTrendDashboardResponseDto | None = None,
        error: Exception | None = None,
    ) -> None:
        self._result = result
        self._error = error
        self.calls: list[str] = []

    def execute(self, *, urn: str) -> SchoolTrendDashboardResponseDto:
        self.calls.append(urn)
        if self._error is not None:
            raise self._error
        if self._result is None:
            raise AssertionError(
                "FakeGetSchoolTrendDashboardUseCase configured without result or error"
            )
        return self._result


def setup_function() -> None:
    app.dependency_overrides.clear()


def teardown_function() -> None:
    app.dependency_overrides.clear()


def test_get_school_trends_returns_expected_contract() -> None:
    fake_use_case = FakeGetSchoolTrendsUseCase(
        result=SchoolTrendsResponseDto(
            urn="123456",
            years_available=("2023/24", "2024/25"),
            history_quality=SchoolTrendsHistoryQualityDto(
                is_partial_history=True,
                min_years_for_delta=2,
                years_count=2,
            ),
            series=SchoolTrendsSeriesDto(
                disadvantaged_pct=(
                    SchoolTrendPointDto(
                        academic_year="2024/25",
                        value=17.2,
                        delta=None,
                        direction=None,
                    ),
                ),
                fsm_pct=(
                    SchoolTrendPointDto(
                        academic_year="2024/25",
                        value=16.9,
                        delta=None,
                        direction=None,
                    ),
                ),
                fsm6_pct=(
                    SchoolTrendPointDto(
                        academic_year="2024/25",
                        value=18.1,
                        delta=None,
                        direction=None,
                    ),
                ),
                sen_pct=(
                    SchoolTrendPointDto(
                        academic_year="2024/25",
                        value=13.0,
                        delta=None,
                        direction=None,
                    ),
                ),
                ehcp_pct=(
                    SchoolTrendPointDto(
                        academic_year="2024/25",
                        value=2.1,
                        delta=None,
                        direction=None,
                    ),
                ),
                eal_pct=(
                    SchoolTrendPointDto(
                        academic_year="2024/25",
                        value=8.4,
                        delta=None,
                        direction=None,
                    ),
                ),
                first_language_english_pct=(
                    SchoolTrendPointDto(
                        academic_year="2024/25",
                        value=90.6,
                        delta=None,
                        direction=None,
                    ),
                ),
                first_language_unclassified_pct=(
                    SchoolTrendPointDto(
                        academic_year="2024/25",
                        value=1.0,
                        delta=None,
                        direction=None,
                    ),
                ),
                male_pct=(
                    SchoolTrendPointDto(
                        academic_year="2024/25",
                        value=49.2,
                        delta=None,
                        direction=None,
                    ),
                ),
                female_pct=(
                    SchoolTrendPointDto(
                        academic_year="2024/25",
                        value=50.8,
                        delta=None,
                        direction=None,
                    ),
                ),
                pupil_mobility_pct=(
                    SchoolTrendPointDto(
                        academic_year="2024/25",
                        value=3.4,
                        delta=None,
                        direction=None,
                    ),
                ),
                overall_attendance_pct=(
                    SchoolTrendPointDto(
                        academic_year="2024/25",
                        value=93.2,
                        delta=None,
                        direction=None,
                    ),
                ),
                overall_absence_pct=(
                    SchoolTrendPointDto(
                        academic_year="2024/25",
                        value=6.8,
                        delta=None,
                        direction=None,
                    ),
                ),
                persistent_absence_pct=(
                    SchoolTrendPointDto(
                        academic_year="2024/25",
                        value=14.1,
                        delta=None,
                        direction=None,
                    ),
                ),
                suspensions_count=(
                    SchoolTrendPointDto(
                        academic_year="2024/25",
                        value=121,
                        delta=None,
                        direction=None,
                    ),
                ),
                suspensions_rate=(
                    SchoolTrendPointDto(
                        academic_year="2024/25",
                        value=16.4,
                        delta=None,
                        direction=None,
                    ),
                ),
                permanent_exclusions_count=(
                    SchoolTrendPointDto(
                        academic_year="2024/25",
                        value=1,
                        delta=None,
                        direction=None,
                    ),
                ),
                permanent_exclusions_rate=(
                    SchoolTrendPointDto(
                        academic_year="2024/25",
                        value=0.1,
                        delta=None,
                        direction=None,
                    ),
                ),
                pupil_teacher_ratio=(
                    SchoolTrendPointDto(
                        academic_year="2024/25",
                        value=16.3,
                        delta=None,
                        direction=None,
                    ),
                ),
                supply_staff_pct=(
                    SchoolTrendPointDto(
                        academic_year="2024/25",
                        value=2.4,
                        delta=None,
                        direction=None,
                    ),
                ),
                teachers_3plus_years_pct=(
                    SchoolTrendPointDto(
                        academic_year="2024/25",
                        value=76.5,
                        delta=None,
                        direction=None,
                    ),
                ),
                teacher_turnover_pct=(
                    SchoolTrendPointDto(
                        academic_year="2024/25",
                        value=9.8,
                        delta=None,
                        direction=None,
                    ),
                ),
                qts_pct=(
                    SchoolTrendPointDto(
                        academic_year="2024/25",
                        value=95.2,
                        delta=None,
                        direction=None,
                    ),
                ),
                qualifications_level6_plus_pct=(
                    SchoolTrendPointDto(
                        academic_year="2024/25",
                        value=81.1,
                        delta=None,
                        direction=None,
                    ),
                ),
                teacher_headcount_total=(
                    SchoolTrendPointDto(
                        academic_year="2024/25",
                        value=42.0,
                        delta=None,
                        direction=None,
                    ),
                ),
                teacher_fte_total=(
                    SchoolTrendPointDto(
                        academic_year="2024/25",
                        value=39.5,
                        delta=None,
                        direction=None,
                    ),
                ),
                support_staff_headcount_total=(
                    SchoolTrendPointDto(
                        academic_year="2024/25",
                        value=28.0,
                        delta=None,
                        direction=None,
                    ),
                ),
                support_staff_fte_total=(
                    SchoolTrendPointDto(
                        academic_year="2024/25",
                        value=22.4,
                        delta=None,
                        direction=None,
                    ),
                ),
                leadership_share_of_teachers=(
                    SchoolTrendPointDto(
                        academic_year="2024/25",
                        value=9.5,
                        delta=None,
                        direction=None,
                    ),
                ),
                teacher_average_mean_salary_gbp=(
                    SchoolTrendPointDto(
                        academic_year="2024/25",
                        value=46850.0,
                        delta=None,
                        direction=None,
                    ),
                ),
                teacher_average_median_salary_gbp=(
                    SchoolTrendPointDto(
                        academic_year="2024/25",
                        value=45200.0,
                        delta=None,
                        direction=None,
                    ),
                ),
                teachers_on_leadership_pay_range_pct=(
                    SchoolTrendPointDto(
                        academic_year="2024/25",
                        value=7.1,
                        delta=None,
                        direction=None,
                    ),
                ),
                teacher_absence_pct=(
                    SchoolTrendPointDto(
                        academic_year="2024/25",
                        value=8.6,
                        delta=None,
                        direction=None,
                    ),
                ),
                teacher_absence_days_total=(
                    SchoolTrendPointDto(
                        academic_year="2024/25",
                        value=198.0,
                        delta=None,
                        direction=None,
                    ),
                ),
                teacher_absence_days_average=(
                    SchoolTrendPointDto(
                        academic_year="2024/25",
                        value=5.5,
                        delta=None,
                        direction=None,
                    ),
                ),
                teacher_absence_days_average_all_teachers=(
                    SchoolTrendPointDto(
                        academic_year="2024/25",
                        value=4.7,
                        delta=None,
                        direction=None,
                    ),
                ),
                teacher_vacancy_count=(
                    SchoolTrendPointDto(
                        academic_year="2024/25",
                        value=1.0,
                        delta=None,
                        direction=None,
                    ),
                ),
                teacher_vacancy_rate=(
                    SchoolTrendPointDto(
                        academic_year="2024/25",
                        value=1.7,
                        delta=None,
                        direction=None,
                    ),
                ),
                teacher_tempfilled_vacancy_count=(
                    SchoolTrendPointDto(
                        academic_year="2024/25",
                        value=2.0,
                        delta=None,
                        direction=None,
                    ),
                ),
                teacher_tempfilled_vacancy_rate=(
                    SchoolTrendPointDto(
                        academic_year="2024/25",
                        value=3.4,
                        delta=None,
                        direction=None,
                    ),
                ),
                third_party_support_staff_headcount=(
                    SchoolTrendPointDto(
                        academic_year="2024/25",
                        value=3.0,
                        delta=None,
                        direction=None,
                    ),
                ),
                income_per_pupil_gbp=(
                    SchoolTrendPointDto(
                        academic_year="2023/24",
                        value=6634.62,
                        delta=None,
                        direction=None,
                    ),
                ),
                expenditure_per_pupil_gbp=(
                    SchoolTrendPointDto(
                        academic_year="2023/24",
                        value=6506.41,
                        delta=None,
                        direction=None,
                    ),
                ),
                staff_costs_pct_of_expenditure=(
                    SchoolTrendPointDto(
                        academic_year="2023/24",
                        value=0.7682,
                        delta=None,
                        direction=None,
                    ),
                ),
                revenue_reserve_per_pupil_gbp=(
                    SchoolTrendPointDto(
                        academic_year="2023/24",
                        value=881.41,
                        delta=None,
                        direction=None,
                    ),
                ),
                teaching_staff_costs_per_pupil_gbp=(),
                supply_staff_costs_pct_of_staff_costs=(),
                admissions_oversubscription_ratio=(
                    SchoolTrendPointDto(
                        academic_year="2024/25",
                        value=1.18,
                        delta=None,
                        direction=None,
                    ),
                ),
                admissions_first_preference_offer_rate=(
                    SchoolTrendPointDto(
                        academic_year="2024/25",
                        value=0.73,
                        delta=None,
                        direction=None,
                    ),
                ),
                admissions_any_preference_offer_rate=(
                    SchoolTrendPointDto(
                        academic_year="2024/25",
                        value=0.86,
                        delta=None,
                        direction=None,
                    ),
                ),
                admissions_cross_la_applications=(
                    SchoolTrendPointDto(
                        academic_year="2024/25",
                        value=18,
                        delta=None,
                        direction=None,
                    ),
                ),
                admissions_cross_la_offers=(
                    SchoolTrendPointDto(
                        academic_year="2024/25",
                        value=9,
                        delta=None,
                        direction=None,
                    ),
                ),
                ks4_overall_pct=(
                    SchoolTrendPointDto(
                        academic_year="2023/24",
                        value=92.0,
                        delta=None,
                        direction=None,
                    ),
                ),
            ),
            benchmarks=SchoolTrendsBenchmarksDto(
                disadvantaged_pct=(
                    SchoolTrendBenchmarkPointDto(
                        academic_year="2024/25",
                        school_value=17.2,
                        national_value=16.0,
                        local_value=16.7,
                        school_vs_national_delta=1.2,
                        school_vs_local_delta=0.5,
                        local_scope="local_authority_district",
                        local_area_code="E09000033",
                        local_area_label="Westminster",
                    ),
                ),
                fsm_pct=(
                    SchoolTrendBenchmarkPointDto(
                        academic_year="2024/25",
                        school_value=16.9,
                        national_value=15.1,
                        local_value=16.2,
                        school_vs_national_delta=1.8,
                        school_vs_local_delta=0.7,
                        local_scope="local_authority_district",
                        local_area_code="E09000033",
                        local_area_label="Westminster",
                        contexts=(
                            SchoolBenchmarkContextDto(
                                scope="national",
                                label="England",
                                value=15.1,
                                percentile_rank=74.0,
                                school_count=22000,
                                area_code="england",
                            ),
                            SchoolBenchmarkContextDto(
                                scope="similar_school",
                                label="Similar Schools",
                                value=16.4,
                                percentile_rank=78.5,
                                school_count=36,
                                area_code=None,
                            ),
                        ),
                    ),
                ),
                fsm6_pct=(),
                sen_pct=(),
                ehcp_pct=(),
                eal_pct=(),
                first_language_english_pct=(),
                first_language_unclassified_pct=(),
                male_pct=(),
                female_pct=(),
                pupil_mobility_pct=(),
                overall_attendance_pct=(),
                overall_absence_pct=(),
                persistent_absence_pct=(),
                suspensions_count=(),
                suspensions_rate=(),
                permanent_exclusions_count=(),
                permanent_exclusions_rate=(),
                pupil_teacher_ratio=(),
                supply_staff_pct=(),
                teachers_3plus_years_pct=(),
                teacher_turnover_pct=(),
                qts_pct=(),
                qualifications_level6_plus_pct=(),
                teacher_headcount_total=(
                    SchoolTrendBenchmarkPointDto(
                        academic_year="2024/25",
                        school_value=42.0,
                        national_value=40.8,
                        local_value=41.5,
                        school_vs_national_delta=1.2,
                        school_vs_local_delta=0.5,
                        local_scope="local_authority_district",
                        local_area_code="E09000033",
                        local_area_label="Westminster",
                    ),
                ),
                teacher_average_mean_salary_gbp=(
                    SchoolTrendBenchmarkPointDto(
                        academic_year="2024/25",
                        school_value=46850.0,
                        national_value=45210.0,
                        local_value=46000.0,
                        school_vs_national_delta=1640.0,
                        school_vs_local_delta=850.0,
                        local_scope="local_authority_district",
                        local_area_code="E09000033",
                        local_area_label="Westminster",
                    ),
                ),
                teacher_vacancy_rate=(
                    SchoolTrendBenchmarkPointDto(
                        academic_year="2024/25",
                        school_value=1.7,
                        national_value=1.9,
                        local_value=1.8,
                        school_vs_national_delta=-0.2,
                        school_vs_local_delta=-0.1,
                        local_scope="local_authority_district",
                        local_area_code="E09000033",
                        local_area_label="Westminster",
                    ),
                ),
                third_party_support_staff_headcount=(
                    SchoolTrendBenchmarkPointDto(
                        academic_year="2024/25",
                        school_value=3.0,
                        national_value=1.8,
                        local_value=2.2,
                        school_vs_national_delta=1.2,
                        school_vs_local_delta=0.8,
                        local_scope="local_authority_district",
                        local_area_code="E09000033",
                        local_area_label="Westminster",
                    ),
                ),
                income_per_pupil_gbp=(
                    SchoolTrendBenchmarkPointDto(
                        academic_year="2023/24",
                        school_value=6634.62,
                        national_value=6120.25,
                        local_value=6450.10,
                        school_vs_national_delta=514.37,
                        school_vs_local_delta=184.52,
                        local_scope="local_authority_district",
                        local_area_code="E09000033",
                        local_area_label="Westminster",
                    ),
                ),
                expenditure_per_pupil_gbp=(),
                staff_costs_pct_of_expenditure=(),
                revenue_reserve_per_pupil_gbp=(),
                teaching_staff_costs_per_pupil_gbp=(),
                supply_staff_costs_pct_of_staff_costs=(),
                admissions_oversubscription_ratio=(
                    SchoolTrendBenchmarkPointDto(
                        academic_year="2024/25",
                        school_value=1.18,
                        national_value=1.1,
                        local_value=1.14,
                        school_vs_national_delta=0.08,
                        school_vs_local_delta=0.04,
                        local_scope="local_authority_district",
                        local_area_code="E09000033",
                        local_area_label="Westminster",
                    ),
                ),
                admissions_first_preference_offer_rate=(
                    SchoolTrendBenchmarkPointDto(
                        academic_year="2024/25",
                        school_value=0.73,
                        national_value=0.76,
                        local_value=0.74,
                        school_vs_national_delta=-0.03,
                        school_vs_local_delta=-0.01,
                        local_scope="local_authority_district",
                        local_area_code="E09000033",
                        local_area_label="Westminster",
                    ),
                ),
                admissions_any_preference_offer_rate=(
                    SchoolTrendBenchmarkPointDto(
                        academic_year="2024/25",
                        school_value=0.86,
                        national_value=0.82,
                        local_value=0.84,
                        school_vs_national_delta=0.04,
                        school_vs_local_delta=0.02,
                        local_scope="local_authority_district",
                        local_area_code="E09000033",
                        local_area_label="Westminster",
                    ),
                ),
                admissions_cross_la_applications=(
                    SchoolTrendBenchmarkPointDto(
                        academic_year="2024/25",
                        school_value=18,
                        national_value=12.0,
                        local_value=15.0,
                        school_vs_national_delta=6.0,
                        school_vs_local_delta=3.0,
                        local_scope="local_authority_district",
                        local_area_code="E09000033",
                        local_area_label="Westminster",
                    ),
                ),
            ),
            completeness=SchoolTrendsCompletenessDto(
                status="partial",
                reason_code="insufficient_years_published",
                last_updated_at=None,
                years_available=("2023/24", "2024/25"),
            ),
            section_completeness=SchoolTrendsSectionCompletenessDto(
                demographics=SchoolTrendsCompletenessDto(
                    status="partial",
                    reason_code="insufficient_years_published",
                    last_updated_at=None,
                    years_available=("2024/25",),
                ),
                attendance=SchoolTrendsCompletenessDto(
                    status="partial",
                    reason_code="insufficient_years_published",
                    last_updated_at=None,
                    years_available=("2024/25",),
                ),
                behaviour=SchoolTrendsCompletenessDto(
                    status="partial",
                    reason_code="insufficient_years_published",
                    last_updated_at=None,
                    years_available=("2024/25",),
                ),
                workforce=SchoolTrendsCompletenessDto(
                    status="partial",
                    reason_code="insufficient_years_published",
                    last_updated_at=None,
                    years_available=("2024/25",),
                ),
                admissions=SchoolTrendsCompletenessDto(
                    status="partial",
                    reason_code="insufficient_years_published",
                    last_updated_at=None,
                    years_available=("2024/25",),
                ),
                destinations=SchoolTrendsCompletenessDto(
                    status="partial",
                    reason_code="unsupported_stage",
                    last_updated_at=None,
                    years_available=("2023/24",),
                ),
                finance=SchoolTrendsCompletenessDto(
                    status="partial",
                    reason_code="insufficient_years_published",
                    last_updated_at=None,
                    years_available=("2023/24",),
                ),
            ),
            subject_performance=SchoolSubjectPerformanceSeriesDto(
                rows=(
                    SchoolSubjectPerformanceGroupRowDto(
                        academic_year="2024/25",
                        key_stage="ks4",
                        qualification_family="gcse",
                        exam_cohort=None,
                        subjects=(
                            SchoolSubjectSummaryDto(
                                academic_year="2024/25",
                                key_stage="ks4",
                                qualification_family="gcse",
                                exam_cohort=None,
                                subject="Mathematics",
                                source_version="revised",
                                entries_count_total=30,
                                high_grade_count=18,
                                high_grade_share_pct=60.0,
                                pass_grade_count=27,
                                pass_grade_share_pct=90.0,
                                ranking_eligible=True,
                            ),
                            SchoolSubjectSummaryDto(
                                academic_year="2024/25",
                                key_stage="ks4",
                                qualification_family="gcse",
                                exam_cohort=None,
                                subject="History",
                                source_version="revised",
                                entries_count_total=18,
                                high_grade_count=4,
                                high_grade_share_pct=22.2222,
                                pass_grade_count=11,
                                pass_grade_share_pct=61.1111,
                                ranking_eligible=True,
                            ),
                        ),
                    ),
                ),
                latest_updated_at=None,
            ),
        )
    )
    app.dependency_overrides[get_school_trends_use_case] = lambda: fake_use_case

    response = client.get("/api/v1/schools/123456/trends")

    assert response.status_code == 200
    payload = response.json()
    assert payload["urn"] == "123456"
    assert payload["years_available"] == ["2023/24", "2024/25"]
    assert payload["history_quality"]["years_count"] == 2
    assert payload["series"]["fsm_pct"][0]["value"] == 16.9
    assert payload["series"]["teacher_headcount_total"][0]["value"] == 42.0
    assert payload["series"]["teacher_average_mean_salary_gbp"][0]["value"] == 46850.0
    assert payload["series"]["teacher_vacancy_rate"][0]["value"] == 1.7
    assert payload["series"]["third_party_support_staff_headcount"][0]["value"] == 3.0
    assert payload["series"]["admissions_oversubscription_ratio"][0]["value"] == pytest.approx(1.18)
    assert payload["series"]["admissions_cross_la_offers"][0]["value"] == 9
    assert payload["series"]["ks4_overall_pct"][0]["value"] == 92.0
    assert payload["series"]["study_16_18_overall_pct"] == []
    assert payload["series"]["income_per_pupil_gbp"][0]["value"] == 6634.62
    assert payload["subject_performance"]["rows"][0]["subjects"][0]["subject"] == "Mathematics"
    assert payload["subject_performance"]["rows"][0]["subjects"][1][
        "pass_grade_share_pct"
    ] == pytest.approx(61.1111)
    assert payload["completeness"]["reason_code"] == "insufficient_years_published"
    assert payload["benchmarks"]["fsm_pct"][0]["local_scope"] == "local_authority_district"
    assert payload["benchmarks"]["fsm_pct"][0]["local_area_label"] == "Westminster"
    assert payload["benchmarks"]["fsm_pct"][0]["contexts"][0]["scope"] == "national"
    assert payload["benchmarks"]["fsm_pct"][0]["contexts"][1]["scope"] == "similar_school"
    assert payload["benchmarks"]["fsm_pct"][0]["contexts"][1]["percentile_rank"] == pytest.approx(
        78.5
    )
    assert payload["benchmarks"]["fsm_pct"][0]["contexts"][1]["school_count"] == 36
    assert payload["benchmarks"]["teacher_headcount_total"][0]["school_value"] == 42.0
    assert payload["benchmarks"]["admissions_cross_la_applications"][0]["school_value"] == 18
    assert payload["benchmarks"]["teacher_average_mean_salary_gbp"][0][
        "school_vs_national_delta"
    ] == pytest.approx(1640.0)
    assert payload["benchmarks"]["teacher_vacancy_rate"][0]["local_value"] == pytest.approx(1.8)
    assert payload["benchmarks"]["fsm_pct"][0]["school_vs_national_delta"] == pytest.approx(1.8)
    assert payload["benchmarks"]["income_per_pupil_gbp"][0][
        "school_vs_local_delta"
    ] == pytest.approx(184.52)
    assert payload["section_completeness"]["admissions"]["years_available"] == ["2024/25"]
    assert payload["section_completeness"]["destinations"]["reason_code"] == "unsupported_stage"
    assert payload["section_completeness"]["finance"]["years_available"] == ["2023/24"]
    assert fake_use_case.calls == ["123456"]


def test_get_school_trends_returns_404_for_unknown_urn() -> None:
    fake_use_case = FakeGetSchoolTrendsUseCase(error=SchoolTrendsNotFoundError("999999"))
    app.dependency_overrides[get_school_trends_use_case] = lambda: fake_use_case

    response = client.get("/api/v1/schools/999999/trends")

    assert response.status_code == 404
    assert response.json() == {"detail": "School with URN '999999' was not found."}


def test_get_school_trends_returns_503_when_datastore_is_unavailable() -> None:
    fake_use_case = FakeGetSchoolTrendsUseCase(
        error=SchoolTrendsDataUnavailableError("School trends datastore is unavailable.")
    )
    app.dependency_overrides[get_school_trends_use_case] = lambda: fake_use_case

    response = client.get("/api/v1/schools/123456/trends")

    assert response.status_code == 503
    assert response.json() == {"detail": "School trends datastore is unavailable."}


def test_get_school_trend_dashboard_returns_expected_contract() -> None:
    fake_use_case = FakeGetSchoolTrendDashboardUseCase(
        result=SchoolTrendDashboardResponseDto(
            urn="123456",
            years_available=("2023/24", "2024", "2024/25"),
            sections=(
                SchoolTrendDashboardSectionDto(
                    key="demographics",
                    metrics=(
                        SchoolTrendDashboardMetricDto(
                            metric_key="fsm_pct",
                            label="Free School Meals (%)",
                            unit="percent",
                            points=(
                                SchoolTrendBenchmarkPointDto(
                                    academic_year="2024/25",
                                    school_value=16.9,
                                    national_value=15.1,
                                    local_value=16.2,
                                    school_vs_national_delta=1.8,
                                    school_vs_local_delta=0.7,
                                    local_scope="local_authority_district",
                                    local_area_code="E09000033",
                                    local_area_label="Westminster",
                                ),
                            ),
                        ),
                    ),
                ),
                SchoolTrendDashboardSectionDto(
                    key="admissions",
                    metrics=(
                        SchoolTrendDashboardMetricDto(
                            metric_key="admissions_oversubscription_ratio",
                            label="Oversubscription Ratio",
                            unit="ratio",
                            points=(
                                SchoolTrendBenchmarkPointDto(
                                    academic_year="2024/25",
                                    school_value=1.18,
                                    national_value=1.1,
                                    local_value=1.14,
                                    school_vs_national_delta=0.08,
                                    school_vs_local_delta=0.04,
                                    local_scope="local_authority_district",
                                    local_area_code="E09000033",
                                    local_area_label="Westminster",
                                ),
                            ),
                        ),
                    ),
                ),
                SchoolTrendDashboardSectionDto(
                    key="finance",
                    metrics=(
                        SchoolTrendDashboardMetricDto(
                            metric_key="finance_income_per_pupil_gbp",
                            label="Income per Pupil",
                            unit="currency",
                            points=(
                                SchoolTrendBenchmarkPointDto(
                                    academic_year="2023/24",
                                    school_value=6634.62,
                                    national_value=6120.25,
                                    local_value=6450.10,
                                    school_vs_national_delta=514.37,
                                    school_vs_local_delta=184.52,
                                    local_scope="local_authority_district",
                                    local_area_code="E09000033",
                                    local_area_label="Westminster",
                                ),
                            ),
                        ),
                    ),
                ),
                SchoolTrendDashboardSectionDto(
                    key="performance",
                    metrics=(
                        SchoolTrendDashboardMetricDto(
                            metric_key="attainment8_average",
                            label="Attainment 8",
                            unit="score",
                            points=(
                                SchoolTrendBenchmarkPointDto(
                                    academic_year="2024/25",
                                    school_value=55.2,
                                    national_value=49.8,
                                    local_value=52.3,
                                    school_vs_national_delta=5.4,
                                    school_vs_local_delta=2.9,
                                    local_scope="local_authority_district",
                                    local_area_code="E09000033",
                                    local_area_label="Westminster",
                                ),
                            ),
                        ),
                    ),
                ),
                SchoolTrendDashboardSectionDto(key="attendance", metrics=()),
                SchoolTrendDashboardSectionDto(key="behaviour", metrics=()),
                SchoolTrendDashboardSectionDto(key="workforce", metrics=()),
                SchoolTrendDashboardSectionDto(key="area", metrics=()),
            ),
            completeness=SchoolTrendsCompletenessDto(
                status="partial",
                reason_code="partial_metric_coverage",
                last_updated_at=None,
                years_available=("2024/25",),
            ),
        )
    )
    app.dependency_overrides[get_school_trend_dashboard_use_case] = lambda: fake_use_case

    response = client.get("/api/v1/schools/123456/trends/dashboard")

    assert response.status_code == 200
    payload = response.json()
    assert payload["urn"] == "123456"
    assert payload["years_available"] == ["2023/24", "2024", "2024/25"]
    assert payload["sections"][0]["key"] == "demographics"
    assert payload["sections"][0]["metrics"][0]["metric_key"] == "fsm_pct"
    assert payload["sections"][1]["key"] == "admissions"
    assert payload["sections"][1]["metrics"][0]["metric_key"] == "admissions_oversubscription_ratio"
    assert payload["sections"][2]["key"] == "finance"
    assert payload["sections"][2]["metrics"][0]["metric_key"] == "finance_income_per_pupil_gbp"
    assert payload["sections"][3]["metrics"][0]["points"][0][
        "school_vs_national_delta"
    ] == pytest.approx(5.4)
    assert fake_use_case.calls == ["123456"]


def test_get_school_trend_dashboard_returns_404_for_unknown_urn() -> None:
    fake_use_case = FakeGetSchoolTrendDashboardUseCase(error=SchoolTrendsNotFoundError("999999"))
    app.dependency_overrides[get_school_trend_dashboard_use_case] = lambda: fake_use_case

    response = client.get("/api/v1/schools/999999/trends/dashboard")

    assert response.status_code == 404
    assert response.json() == {"detail": "School with URN '999999' was not found."}


def test_get_school_trend_dashboard_returns_503_when_datastore_is_unavailable() -> None:
    fake_use_case = FakeGetSchoolTrendDashboardUseCase(
        error=SchoolTrendsDataUnavailableError("School trends datastore is unavailable.")
    )
    app.dependency_overrides[get_school_trend_dashboard_use_case] = lambda: fake_use_case

    response = client.get("/api/v1/schools/123456/trends/dashboard")

    assert response.status_code == 503
    assert response.json() == {"detail": "School trends datastore is unavailable."}
