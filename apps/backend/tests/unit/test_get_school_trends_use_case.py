from __future__ import annotations

import pytest

from civitas.application.school_trends.errors import SchoolTrendsNotFoundError
from civitas.application.school_trends.use_cases import (
    GetSchoolTrendDashboardUseCase,
    GetSchoolTrendsUseCase,
)
from civitas.domain.school_trends.models import (
    SchoolAttendanceSeries,
    SchoolAttendanceYearlyRow,
    SchoolBehaviourSeries,
    SchoolBehaviourYearlyRow,
    SchoolDemographicsSeries,
    SchoolDemographicsYearlyRow,
    SchoolMetricBenchmarkSeries,
    SchoolMetricBenchmarkYearlyRow,
    SchoolWorkforceSeries,
    SchoolWorkforceYearlyRow,
)


class FakeSchoolTrendsRepository:
    def __init__(
        self,
        *,
        demographics: SchoolDemographicsSeries | None,
        attendance: SchoolAttendanceSeries | None,
        behaviour: SchoolBehaviourSeries | None,
        workforce: SchoolWorkforceSeries | None,
        benchmarks: SchoolMetricBenchmarkSeries | None,
    ) -> None:
        self._demographics = demographics
        self._attendance = attendance
        self._behaviour = behaviour
        self._workforce = workforce
        self._benchmarks = benchmarks
        self.received_urns: list[str] = []

    def get_demographics_series(self, urn: str) -> SchoolDemographicsSeries | None:
        self.received_urns.append(urn)
        return self._demographics

    def get_attendance_series(self, urn: str) -> SchoolAttendanceSeries | None:
        return self._attendance

    def get_behaviour_series(self, urn: str) -> SchoolBehaviourSeries | None:
        return self._behaviour

    def get_workforce_series(self, urn: str) -> SchoolWorkforceSeries | None:
        return self._workforce

    def get_metric_benchmark_series(self, urn: str) -> SchoolMetricBenchmarkSeries | None:
        return self._benchmarks


def test_get_school_trends_returns_expected_delta_and_direction() -> None:
    repository = FakeSchoolTrendsRepository(
        demographics=SchoolDemographicsSeries(
            urn="123456",
            rows=(
                SchoolDemographicsYearlyRow(
                    academic_year="2022/23",
                    disadvantaged_pct=20.0,
                    fsm_pct=18.0,
                    fsm6_pct=21.0,
                    sen_pct=10.0,
                    ehcp_pct=2.0,
                    eal_pct=8.0,
                    first_language_english_pct=90.0,
                    first_language_unclassified_pct=1.0,
                    male_pct=49.0,
                    female_pct=51.0,
                    pupil_mobility_pct=3.0,
                ),
                SchoolDemographicsYearlyRow(
                    academic_year="2023/24",
                    disadvantaged_pct=19.0,
                    fsm_pct=17.5,
                    fsm6_pct=20.2,
                    sen_pct=10.0,
                    ehcp_pct=2.5,
                    eal_pct=8.0,
                    first_language_english_pct=89.0,
                    first_language_unclassified_pct=1.0,
                    male_pct=49.5,
                    female_pct=50.5,
                    pupil_mobility_pct=2.6,
                ),
                SchoolDemographicsYearlyRow(
                    academic_year="2024/25",
                    disadvantaged_pct=21.0,
                    fsm_pct=18.2,
                    fsm6_pct=21.1,
                    sen_pct=None,
                    ehcp_pct=2.0,
                    eal_pct=9.0,
                    first_language_english_pct=88.5,
                    first_language_unclassified_pct=0.8,
                    male_pct=48.8,
                    female_pct=51.2,
                    pupil_mobility_pct=2.4,
                ),
            ),
            latest_updated_at=None,
        ),
        attendance=SchoolAttendanceSeries(
            urn="123456",
            rows=(
                SchoolAttendanceYearlyRow(
                    academic_year="2022/23",
                    overall_attendance_pct=92.8,
                    overall_absence_pct=7.2,
                    persistent_absence_pct=15.3,
                ),
                SchoolAttendanceYearlyRow(
                    academic_year="2023/24",
                    overall_attendance_pct=93.0,
                    overall_absence_pct=7.0,
                    persistent_absence_pct=14.8,
                ),
                SchoolAttendanceYearlyRow(
                    academic_year="2024/25",
                    overall_attendance_pct=93.2,
                    overall_absence_pct=6.8,
                    persistent_absence_pct=14.1,
                ),
            ),
            latest_updated_at=None,
        ),
        behaviour=SchoolBehaviourSeries(
            urn="123456",
            rows=(
                SchoolBehaviourYearlyRow(
                    academic_year="2022/23",
                    suspensions_count=95,
                    suspensions_rate=12.4,
                    permanent_exclusions_count=0,
                    permanent_exclusions_rate=0.0,
                ),
                SchoolBehaviourYearlyRow(
                    academic_year="2023/24",
                    suspensions_count=109,
                    suspensions_rate=14.8,
                    permanent_exclusions_count=1,
                    permanent_exclusions_rate=0.1,
                ),
                SchoolBehaviourYearlyRow(
                    academic_year="2024/25",
                    suspensions_count=121,
                    suspensions_rate=16.4,
                    permanent_exclusions_count=1,
                    permanent_exclusions_rate=0.1,
                ),
            ),
            latest_updated_at=None,
        ),
        workforce=SchoolWorkforceSeries(
            urn="123456",
            rows=(
                SchoolWorkforceYearlyRow(
                    academic_year="2022/23",
                    pupil_teacher_ratio=17.0,
                    supply_staff_pct=3.1,
                    teachers_3plus_years_pct=73.0,
                    teacher_turnover_pct=10.8,
                    qts_pct=94.5,
                    qualifications_level6_plus_pct=79.0,
                ),
                SchoolWorkforceYearlyRow(
                    academic_year="2023/24",
                    pupil_teacher_ratio=16.7,
                    supply_staff_pct=2.8,
                    teachers_3plus_years_pct=74.0,
                    teacher_turnover_pct=10.2,
                    qts_pct=95.1,
                    qualifications_level6_plus_pct=80.3,
                ),
                SchoolWorkforceYearlyRow(
                    academic_year="2024/25",
                    pupil_teacher_ratio=16.3,
                    supply_staff_pct=2.4,
                    teachers_3plus_years_pct=76.5,
                    teacher_turnover_pct=9.8,
                    qts_pct=95.2,
                    qualifications_level6_plus_pct=81.1,
                ),
            ),
            latest_updated_at=None,
        ),
        benchmarks=SchoolMetricBenchmarkSeries(
            urn="123456",
            rows=(
                SchoolMetricBenchmarkYearlyRow(
                    metric_key="disadvantaged_pct",
                    academic_year="2022/23",
                    school_value=20.0,
                    national_value=18.4,
                    local_value=19.0,
                    local_scope="local_authority_district",
                    local_area_code="E09000033",
                    local_area_label="Westminster",
                ),
                SchoolMetricBenchmarkYearlyRow(
                    metric_key="disadvantaged_pct",
                    academic_year="2023/24",
                    school_value=19.0,
                    national_value=18.1,
                    local_value=18.7,
                    local_scope="local_authority_district",
                    local_area_code="E09000033",
                    local_area_label="Westminster",
                ),
                SchoolMetricBenchmarkYearlyRow(
                    metric_key="disadvantaged_pct",
                    academic_year="2024/25",
                    school_value=21.0,
                    national_value=18.0,
                    local_value=18.2,
                    local_scope="local_authority_district",
                    local_area_code="E09000033",
                    local_area_label="Westminster",
                ),
            ),
            latest_updated_at=None,
        ),
    )
    use_case = GetSchoolTrendsUseCase(school_trends_repository=repository)

    result = use_case.execute(urn=" 123456 ")

    assert repository.received_urns == ["123456"]
    assert result.urn == "123456"
    assert result.years_available == ("2022/23", "2023/24", "2024/25")
    assert result.history_quality.min_years_for_delta == 2
    assert result.history_quality.years_count == 3
    assert result.history_quality.is_partial_history is False
    assert result.completeness.status == "partial"
    assert result.completeness.reason_code == "partial_metric_coverage"

    assert result.series.disadvantaged_pct[1].delta == -1.0
    assert result.series.disadvantaged_pct[2].delta == 2.0
    assert result.series.disadvantaged_pct[2].direction == "up"
    assert result.series.sen_pct[2].value is None

    assert result.series.overall_attendance_pct[1].delta == pytest.approx(0.2)
    assert result.series.overall_absence_pct[2].delta == pytest.approx(-0.2)
    assert result.series.persistent_absence_pct[2].delta == pytest.approx(-0.7)

    assert result.series.suspensions_count[1].delta == 14.0
    assert result.series.pupil_teacher_ratio[2].delta == pytest.approx(-0.4)
    assert result.series.qts_pct[2].delta == pytest.approx(0.1)

    assert result.benchmarks.disadvantaged_pct[2].school_vs_national_delta == pytest.approx(3.0)
    assert result.benchmarks.disadvantaged_pct[2].school_vs_local_delta == pytest.approx(2.8)
    assert result.benchmarks.disadvantaged_pct[2].local_scope == "local_authority_district"


def test_get_school_trends_marks_partial_history_when_only_one_year_is_available() -> None:
    repository = FakeSchoolTrendsRepository(
        demographics=SchoolDemographicsSeries(
            urn="123456",
            rows=(
                SchoolDemographicsYearlyRow(
                    academic_year="2024/25",
                    disadvantaged_pct=17.2,
                    fsm_pct=16.9,
                    fsm6_pct=18.1,
                    sen_pct=13.0,
                    ehcp_pct=2.1,
                    eal_pct=8.4,
                    first_language_english_pct=90.6,
                    first_language_unclassified_pct=1.0,
                    male_pct=49.2,
                    female_pct=50.8,
                    pupil_mobility_pct=3.4,
                ),
            ),
            latest_updated_at=None,
        ),
        attendance=SchoolAttendanceSeries(
            urn="123456",
            rows=(
                SchoolAttendanceYearlyRow(
                    academic_year="2024/25",
                    overall_attendance_pct=93.2,
                    overall_absence_pct=6.8,
                    persistent_absence_pct=14.1,
                ),
            ),
            latest_updated_at=None,
        ),
        behaviour=SchoolBehaviourSeries(
            urn="123456",
            rows=(
                SchoolBehaviourYearlyRow(
                    academic_year="2024/25",
                    suspensions_count=121,
                    suspensions_rate=16.4,
                    permanent_exclusions_count=1,
                    permanent_exclusions_rate=0.1,
                ),
            ),
            latest_updated_at=None,
        ),
        workforce=SchoolWorkforceSeries(
            urn="123456",
            rows=(
                SchoolWorkforceYearlyRow(
                    academic_year="2024/25",
                    pupil_teacher_ratio=16.3,
                    supply_staff_pct=2.4,
                    teachers_3plus_years_pct=76.5,
                    teacher_turnover_pct=9.8,
                    qts_pct=95.2,
                    qualifications_level6_plus_pct=81.1,
                ),
            ),
            latest_updated_at=None,
        ),
        benchmarks=SchoolMetricBenchmarkSeries(
            urn="123456",
            rows=(
                SchoolMetricBenchmarkYearlyRow(
                    metric_key="overall_attendance_pct",
                    academic_year="2024/25",
                    school_value=93.2,
                    national_value=92.1,
                    local_value=92.8,
                    local_scope="phase",
                    local_area_code="Secondary",
                    local_area_label="Secondary",
                ),
            ),
            latest_updated_at=None,
        ),
    )
    use_case = GetSchoolTrendsUseCase(school_trends_repository=repository)

    result = use_case.execute(urn="123456")

    assert result.years_available == ("2024/25",)
    assert result.history_quality.years_count == 1
    assert result.history_quality.is_partial_history is True
    assert result.completeness.status == "partial"
    assert result.completeness.reason_code == "insufficient_years_published"
    assert result.series.disadvantaged_pct[0].delta is None


def test_get_school_trends_returns_empty_series_for_school_without_any_rows() -> None:
    repository = FakeSchoolTrendsRepository(
        demographics=SchoolDemographicsSeries(
            urn="123456",
            rows=(),
            latest_updated_at=None,
        ),
        attendance=SchoolAttendanceSeries(
            urn="123456",
            rows=(),
            latest_updated_at=None,
        ),
        behaviour=SchoolBehaviourSeries(
            urn="123456",
            rows=(),
            latest_updated_at=None,
        ),
        workforce=SchoolWorkforceSeries(
            urn="123456",
            rows=(),
            latest_updated_at=None,
        ),
        benchmarks=SchoolMetricBenchmarkSeries(
            urn="123456",
            rows=(),
            latest_updated_at=None,
        ),
    )
    use_case = GetSchoolTrendsUseCase(school_trends_repository=repository)

    result = use_case.execute(urn="123456")

    assert result.urn == "123456"
    assert result.years_available == ()
    assert result.completeness.status == "unavailable"
    assert result.series.disadvantaged_pct == ()
    assert result.benchmarks.disadvantaged_pct == ()


def test_get_school_trends_raises_not_found_when_school_is_missing() -> None:
    repository = FakeSchoolTrendsRepository(
        demographics=None,
        attendance=None,
        behaviour=None,
        workforce=None,
        benchmarks=None,
    )
    use_case = GetSchoolTrendsUseCase(school_trends_repository=repository)

    with pytest.raises(SchoolTrendsNotFoundError, match="School with URN '999999' was not found."):
        use_case.execute(urn="999999")


def test_get_school_trend_dashboard_groups_metrics_by_section() -> None:
    repository = FakeSchoolTrendsRepository(
        demographics=SchoolDemographicsSeries(
            urn="123456",
            rows=(
                SchoolDemographicsYearlyRow(
                    academic_year="2024/25",
                    disadvantaged_pct=17.2,
                    fsm_pct=16.9,
                    fsm6_pct=18.1,
                    sen_pct=13.0,
                    ehcp_pct=2.1,
                    eal_pct=8.4,
                    first_language_english_pct=90.6,
                    first_language_unclassified_pct=1.0,
                    male_pct=49.2,
                    female_pct=50.8,
                    pupil_mobility_pct=3.4,
                ),
            ),
            latest_updated_at=None,
        ),
        attendance=SchoolAttendanceSeries(
            urn="123456",
            rows=(
                SchoolAttendanceYearlyRow(
                    academic_year="2024/25",
                    overall_attendance_pct=93.2,
                    overall_absence_pct=6.8,
                    persistent_absence_pct=14.1,
                ),
            ),
            latest_updated_at=None,
        ),
        behaviour=SchoolBehaviourSeries(
            urn="123456",
            rows=(
                SchoolBehaviourYearlyRow(
                    academic_year="2024/25",
                    suspensions_count=121,
                    suspensions_rate=16.4,
                    permanent_exclusions_count=1,
                    permanent_exclusions_rate=0.1,
                ),
            ),
            latest_updated_at=None,
        ),
        workforce=SchoolWorkforceSeries(
            urn="123456",
            rows=(
                SchoolWorkforceYearlyRow(
                    academic_year="2024/25",
                    pupil_teacher_ratio=16.3,
                    supply_staff_pct=2.4,
                    teachers_3plus_years_pct=76.5,
                    teacher_turnover_pct=9.8,
                    qts_pct=95.2,
                    qualifications_level6_plus_pct=81.1,
                ),
            ),
            latest_updated_at=None,
        ),
        benchmarks=SchoolMetricBenchmarkSeries(
            urn="123456",
            rows=(
                SchoolMetricBenchmarkYearlyRow(
                    metric_key="fsm_pct",
                    academic_year="2024/25",
                    school_value=16.9,
                    national_value=15.1,
                    local_value=16.2,
                    local_scope="local_authority_district",
                    local_area_code="E09000033",
                    local_area_label="Westminster",
                ),
                SchoolMetricBenchmarkYearlyRow(
                    metric_key="overall_attendance_pct",
                    academic_year="2024/25",
                    school_value=93.2,
                    national_value=92.0,
                    local_value=92.7,
                    local_scope="local_authority_district",
                    local_area_code="E09000033",
                    local_area_label="Westminster",
                ),
                SchoolMetricBenchmarkYearlyRow(
                    metric_key="attainment8_average",
                    academic_year="2024/25",
                    school_value=54.0,
                    national_value=49.5,
                    local_value=51.2,
                    local_scope="local_authority_district",
                    local_area_code="E09000033",
                    local_area_label="Westminster",
                ),
                SchoolMetricBenchmarkYearlyRow(
                    metric_key="area_crime_incidents_per_1000",
                    academic_year="2024",
                    school_value=51.0,
                    national_value=64.2,
                    local_value=47.5,
                    local_scope="local_authority_district",
                    local_area_code="E09000033",
                    local_area_label="Westminster",
                ),
            ),
            latest_updated_at=None,
        ),
    )
    use_case = GetSchoolTrendDashboardUseCase(school_trends_repository=repository)

    result = use_case.execute(urn="123456")

    sections = {section.key: section for section in result.sections}
    assert "demographics" in sections
    assert "attendance" in sections
    assert "performance" in sections
    assert "area" in sections

    demographics_metrics = {metric.metric_key for metric in sections["demographics"].metrics}
    performance_metrics = {metric.metric_key for metric in sections["performance"].metrics}
    area_metrics = {metric.metric_key for metric in sections["area"].metrics}

    assert "fsm_pct" in demographics_metrics
    assert "attainment8_average" in performance_metrics
    assert "area_crime_incidents_per_1000" in area_metrics
    assert result.completeness.status == "partial"


def test_get_school_trend_dashboard_raises_not_found_when_school_is_missing() -> None:
    repository = FakeSchoolTrendsRepository(
        demographics=None,
        attendance=None,
        behaviour=None,
        workforce=None,
        benchmarks=None,
    )
    use_case = GetSchoolTrendDashboardUseCase(school_trends_repository=repository)

    with pytest.raises(SchoolTrendsNotFoundError, match="School with URN '999999' was not found."):
        use_case.execute(urn="999999")
