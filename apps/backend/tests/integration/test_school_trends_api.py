from __future__ import annotations

from fastapi.testclient import TestClient

from civitas.api.dependencies import get_school_trends_use_case
from civitas.api.main import app
from civitas.application.school_trends.dto import (
    SchoolTrendPointDto,
    SchoolTrendsCompletenessDto,
    SchoolTrendsHistoryQualityDto,
    SchoolTrendsResponseDto,
    SchoolTrendsSeriesDto,
)
from civitas.application.school_trends.errors import (
    SchoolTrendsDataUnavailableError,
    SchoolTrendsNotFoundError,
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


def setup_function() -> None:
    app.dependency_overrides.clear()


def teardown_function() -> None:
    app.dependency_overrides.clear()


def test_get_school_trends_returns_expected_contract() -> None:
    fake_use_case = FakeGetSchoolTrendsUseCase(
        result=SchoolTrendsResponseDto(
            urn="123456",
            years_available=("2024/25",),
            history_quality=SchoolTrendsHistoryQualityDto(
                is_partial_history=True,
                min_years_for_delta=2,
                years_count=1,
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
            ),
            completeness=SchoolTrendsCompletenessDto(
                status="partial",
                reason_code="insufficient_years_published",
                last_updated_at=None,
                years_available=("2024/25",),
            ),
        )
    )
    app.dependency_overrides[get_school_trends_use_case] = lambda: fake_use_case

    response = client.get("/api/v1/schools/123456/trends")

    assert response.status_code == 200
    assert response.json() == {
        "urn": "123456",
        "years_available": ["2024/25"],
        "history_quality": {
            "is_partial_history": True,
            "min_years_for_delta": 2,
            "years_count": 1,
        },
        "series": {
            "disadvantaged_pct": [
                {
                    "academic_year": "2024/25",
                    "value": 17.2,
                    "delta": None,
                    "direction": None,
                }
            ],
            "sen_pct": [
                {
                    "academic_year": "2024/25",
                    "value": 13.0,
                    "delta": None,
                    "direction": None,
                }
            ],
            "ehcp_pct": [
                {
                    "academic_year": "2024/25",
                    "value": 2.1,
                    "delta": None,
                    "direction": None,
                }
            ],
            "eal_pct": [
                {
                    "academic_year": "2024/25",
                    "value": 8.4,
                    "delta": None,
                    "direction": None,
                }
            ],
        },
        "completeness": {
            "status": "partial",
            "reason_code": "insufficient_years_published",
            "last_updated_at": None,
            "years_available": ["2024/25"],
        },
    }
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
