from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient

from civitas.api.dependencies import get_school_profile_use_case
from civitas.api.main import app
from civitas.application.school_profiles.dto import (
    SchoolDemographicsCoverageDto,
    SchoolDemographicsLatestDto,
    SchoolOfstedLatestDto,
    SchoolProfileResponseDto,
    SchoolProfileSchoolDto,
)
from civitas.application.school_profiles.errors import (
    SchoolProfileDataUnavailableError,
    SchoolProfileNotFoundError,
)

client = TestClient(app)


class FakeGetSchoolProfileUseCase:
    def __init__(
        self, result: SchoolProfileResponseDto | None = None, error: Exception | None = None
    ) -> None:
        self._result = result
        self._error = error
        self.calls: list[str] = []

    def execute(self, *, urn: str) -> SchoolProfileResponseDto:
        self.calls.append(urn)
        if self._error is not None:
            raise self._error
        if self._result is None:
            raise AssertionError("FakeGetSchoolProfileUseCase configured without result or error")
        return self._result


def setup_function() -> None:
    app.dependency_overrides.clear()


def teardown_function() -> None:
    app.dependency_overrides.clear()


def test_get_school_profile_returns_expected_contract() -> None:
    fake_use_case = FakeGetSchoolProfileUseCase(
        result=SchoolProfileResponseDto(
            school=SchoolProfileSchoolDto(
                urn="123456",
                name="Example School",
                phase="Primary",
                school_type="Academy",
                status="Open",
                postcode="SW1A 1AA",
                lat=51.5010,
                lng=-0.1416,
            ),
            demographics_latest=SchoolDemographicsLatestDto(
                academic_year="2024/25",
                disadvantaged_pct=17.2,
                fsm_pct=None,
                sen_pct=13.0,
                ehcp_pct=2.1,
                eal_pct=8.4,
                first_language_english_pct=90.6,
                first_language_unclassified_pct=1.0,
                coverage=SchoolDemographicsCoverageDto(
                    fsm_supported=False,
                    ethnicity_supported=False,
                    top_languages_supported=False,
                ),
            ),
            ofsted_latest=SchoolOfstedLatestDto(
                overall_effectiveness_code="2",
                overall_effectiveness_label="Good",
                inspection_start_date=date(2025, 10, 10),
                publication_date=date(2025, 11, 15),
                is_graded=True,
                ungraded_outcome=None,
            ),
        )
    )
    app.dependency_overrides[get_school_profile_use_case] = lambda: fake_use_case

    response = client.get("/api/v1/schools/123456")

    assert response.status_code == 200
    assert response.json() == {
        "school": {
            "urn": "123456",
            "name": "Example School",
            "phase": "Primary",
            "type": "Academy",
            "status": "Open",
            "postcode": "SW1A 1AA",
            "lat": 51.501,
            "lng": -0.1416,
        },
        "demographics_latest": {
            "academic_year": "2024/25",
            "disadvantaged_pct": 17.2,
            "fsm_pct": None,
            "sen_pct": 13.0,
            "ehcp_pct": 2.1,
            "eal_pct": 8.4,
            "first_language_english_pct": 90.6,
            "first_language_unclassified_pct": 1.0,
            "coverage": {
                "fsm_supported": False,
                "ethnicity_supported": False,
                "top_languages_supported": False,
            },
        },
        "ofsted_latest": {
            "overall_effectiveness_code": "2",
            "overall_effectiveness_label": "Good",
            "inspection_start_date": "2025-10-10",
            "publication_date": "2025-11-15",
            "is_graded": True,
            "ungraded_outcome": None,
        },
    }
    assert fake_use_case.calls == ["123456"]


def test_get_school_profile_returns_null_subsections_when_data_missing() -> None:
    fake_use_case = FakeGetSchoolProfileUseCase(
        result=SchoolProfileResponseDto(
            school=SchoolProfileSchoolDto(
                urn="123456",
                name="Example School",
                phase="Primary",
                school_type="Academy",
                status="Open",
                postcode="SW1A 1AA",
                lat=51.5010,
                lng=-0.1416,
            ),
            demographics_latest=None,
            ofsted_latest=None,
        )
    )
    app.dependency_overrides[get_school_profile_use_case] = lambda: fake_use_case

    response = client.get("/api/v1/schools/123456")

    assert response.status_code == 200
    assert response.json()["demographics_latest"] is None
    assert response.json()["ofsted_latest"] is None


def test_get_school_profile_returns_404_for_unknown_urn() -> None:
    fake_use_case = FakeGetSchoolProfileUseCase(error=SchoolProfileNotFoundError("999999"))
    app.dependency_overrides[get_school_profile_use_case] = lambda: fake_use_case

    response = client.get("/api/v1/schools/999999")

    assert response.status_code == 404
    assert response.json() == {"detail": "School with URN '999999' was not found."}


def test_get_school_profile_returns_503_when_datastore_is_unavailable() -> None:
    fake_use_case = FakeGetSchoolProfileUseCase(
        error=SchoolProfileDataUnavailableError("School profile datastore is unavailable.")
    )
    app.dependency_overrides[get_school_profile_use_case] = lambda: fake_use_case

    response = client.get("/api/v1/schools/123456")

    assert response.status_code == 503
    assert response.json() == {"detail": "School profile datastore is unavailable."}
