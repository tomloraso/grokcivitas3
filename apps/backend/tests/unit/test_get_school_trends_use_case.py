import pytest

from civitas.application.school_trends.errors import SchoolTrendsNotFoundError
from civitas.application.school_trends.use_cases import GetSchoolTrendsUseCase
from civitas.domain.school_trends.models import (
    SchoolDemographicsSeries,
    SchoolDemographicsYearlyRow,
)


class FakeSchoolTrendsRepository:
    def __init__(self, series: SchoolDemographicsSeries | None) -> None:
        self._series = series
        self.received_urns: list[str] = []

    def get_demographics_series(self, urn: str) -> SchoolDemographicsSeries | None:
        self.received_urns.append(urn)
        return self._series


def test_get_school_trends_returns_expected_delta_and_direction() -> None:
    repository = FakeSchoolTrendsRepository(
        series=SchoolDemographicsSeries(
            urn="123456",
            rows=(
                SchoolDemographicsYearlyRow(
                    academic_year="2022/23",
                    disadvantaged_pct=20.0,
                    sen_pct=10.0,
                    ehcp_pct=2.0,
                    eal_pct=8.0,
                ),
                SchoolDemographicsYearlyRow(
                    academic_year="2023/24",
                    disadvantaged_pct=19.0,
                    sen_pct=10.0,
                    ehcp_pct=2.5,
                    eal_pct=8.0,
                ),
                SchoolDemographicsYearlyRow(
                    academic_year="2024/25",
                    disadvantaged_pct=21.0,
                    sen_pct=None,
                    ehcp_pct=2.0,
                    eal_pct=9.0,
                ),
            ),
            latest_updated_at=None,
        )
    )
    use_case = GetSchoolTrendsUseCase(school_trends_repository=repository)

    result = use_case.execute(urn=" 123456 ")

    assert repository.received_urns == ["123456"]
    assert result.urn == "123456"
    assert result.years_available == ("2022/23", "2023/24", "2024/25")
    assert result.history_quality.min_years_for_delta == 2
    assert result.history_quality.years_count == 3
    assert result.history_quality.is_partial_history is False
    assert result.completeness.status == "available"
    assert result.completeness.reason_code is None
    assert result.completeness.years_available == ("2022/23", "2023/24", "2024/25")

    assert result.series.disadvantaged_pct[0].delta is None
    assert result.series.disadvantaged_pct[1].delta == -1.0
    assert result.series.disadvantaged_pct[1].direction == "down"
    assert result.series.disadvantaged_pct[2].delta == 2.0
    assert result.series.disadvantaged_pct[2].direction == "up"

    assert result.series.sen_pct[1].delta == 0.0
    assert result.series.sen_pct[1].direction == "flat"
    assert result.series.sen_pct[2].value is None
    assert result.series.sen_pct[2].delta is None
    assert result.series.sen_pct[2].direction is None

    assert result.series.ehcp_pct[1].delta == 0.5
    assert result.series.ehcp_pct[1].direction == "up"
    assert result.series.ehcp_pct[2].delta == -0.5
    assert result.series.ehcp_pct[2].direction == "down"

    assert result.series.eal_pct[1].delta == 0.0
    assert result.series.eal_pct[1].direction == "flat"
    assert result.series.eal_pct[2].delta == 1.0
    assert result.series.eal_pct[2].direction == "up"


def test_get_school_trends_marks_partial_history_when_only_one_year_is_available() -> None:
    repository = FakeSchoolTrendsRepository(
        series=SchoolDemographicsSeries(
            urn="123456",
            rows=(
                SchoolDemographicsYearlyRow(
                    academic_year="2024/25",
                    disadvantaged_pct=17.2,
                    sen_pct=13.0,
                    ehcp_pct=2.1,
                    eal_pct=8.4,
                ),
            ),
            latest_updated_at=None,
        )
    )
    use_case = GetSchoolTrendsUseCase(school_trends_repository=repository)

    result = use_case.execute(urn="123456")

    assert result.years_available == ("2024/25",)
    assert result.history_quality.years_count == 1
    assert result.history_quality.is_partial_history is True
    assert result.completeness.status == "partial"
    assert result.completeness.reason_code == "source_missing"
    assert result.completeness.years_available == ("2024/25",)
    assert result.series.disadvantaged_pct[0].delta is None
    assert result.series.disadvantaged_pct[0].direction is None


def test_get_school_trends_returns_empty_series_for_school_without_demographics_rows() -> None:
    repository = FakeSchoolTrendsRepository(
        series=SchoolDemographicsSeries(
            urn="123456",
            rows=(),
            latest_updated_at=None,
        )
    )
    use_case = GetSchoolTrendsUseCase(school_trends_repository=repository)

    result = use_case.execute(urn="123456")

    assert result.urn == "123456"
    assert result.years_available == ()
    assert result.history_quality.years_count == 0
    assert result.history_quality.is_partial_history is True
    assert result.completeness.status == "unavailable"
    assert result.completeness.reason_code == "source_missing"
    assert result.completeness.years_available == ()
    assert result.series.disadvantaged_pct == ()
    assert result.series.sen_pct == ()
    assert result.series.ehcp_pct == ()
    assert result.series.eal_pct == ()


def test_get_school_trends_raises_not_found_when_school_is_missing() -> None:
    repository = FakeSchoolTrendsRepository(series=None)
    use_case = GetSchoolTrendsUseCase(school_trends_repository=repository)

    with pytest.raises(SchoolTrendsNotFoundError, match="School with URN '999999' was not found."):
        use_case.execute(urn="999999")
