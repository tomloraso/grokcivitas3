from __future__ import annotations

from datetime import date, datetime, timezone

from fastapi.testclient import TestClient

from civitas.api.dependencies import get_school_profile_use_case
from civitas.api.main import app
from civitas.application.school_profiles.dto import (
    SchoolAreaContextCoverageDto,
    SchoolAreaContextDto,
    SchoolAreaCrimeCategoryDto,
    SchoolAreaCrimeDto,
    SchoolAreaDeprivationDto,
    SchoolDemographicsCoverageDto,
    SchoolDemographicsLatestDto,
    SchoolOfstedLatestDto,
    SchoolOfstedTimelineCoverageDto,
    SchoolOfstedTimelineDto,
    SchoolOfstedTimelineEventDto,
    SchoolProfileCompletenessDto,
    SchoolProfileResponseDto,
    SchoolProfileSchoolDto,
    SchoolProfileSectionCompletenessDto,
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
                fsm_pct=16.9,
                sen_pct=13.0,
                ehcp_pct=2.1,
                eal_pct=8.4,
                first_language_english_pct=90.6,
                first_language_unclassified_pct=1.0,
                coverage=SchoolDemographicsCoverageDto(
                    fsm_supported=True,
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
            ofsted_timeline=SchoolOfstedTimelineDto(
                events=(
                    SchoolOfstedTimelineEventDto(
                        inspection_number="10426709",
                        inspection_start_date=date(2025, 11, 11),
                        publication_date=date(2026, 1, 11),
                        inspection_type="S5 Inspection",
                        overall_effectiveness_label=None,
                        headline_outcome_text="Strong standard",
                        category_of_concern=None,
                    ),
                ),
                coverage=SchoolOfstedTimelineCoverageDto(
                    is_partial_history=False,
                    earliest_event_date=date(2015, 9, 14),
                    latest_event_date=date(2026, 1, 15),
                    events_count=9,
                ),
            ),
            area_context=SchoolAreaContextDto(
                deprivation=SchoolAreaDeprivationDto(
                    lsoa_code="E01004736",
                    imd_decile=3,
                    idaci_score=0.241,
                    idaci_decile=2,
                    source_release="IoD2025",
                ),
                crime=SchoolAreaCrimeDto(
                    radius_miles=1.0,
                    latest_month="2026-01",
                    total_incidents=486,
                    categories=(
                        SchoolAreaCrimeCategoryDto(
                            category="violent-crime",
                            incident_count=132,
                        ),
                    ),
                ),
                coverage=SchoolAreaContextCoverageDto(
                    has_deprivation=True,
                    has_crime=True,
                    crime_months_available=12,
                ),
            ),
            completeness=SchoolProfileCompletenessDto(
                demographics=SchoolProfileSectionCompletenessDto(
                    status="partial",
                    reason_code="partial_metric_coverage",
                    last_updated_at=datetime(2026, 1, 31, 9, 0, tzinfo=timezone.utc),
                    years_available=None,
                ),
                ofsted_latest=SchoolProfileSectionCompletenessDto(
                    status="available",
                    reason_code=None,
                    last_updated_at=datetime(2026, 1, 20, 10, 0, tzinfo=timezone.utc),
                    years_available=None,
                ),
                ofsted_timeline=SchoolProfileSectionCompletenessDto(
                    status="available",
                    reason_code=None,
                    last_updated_at=datetime(2026, 1, 18, 11, 0, tzinfo=timezone.utc),
                    years_available=None,
                ),
                area_deprivation=SchoolProfileSectionCompletenessDto(
                    status="available",
                    reason_code=None,
                    last_updated_at=datetime(2026, 1, 10, 12, 0, tzinfo=timezone.utc),
                    years_available=None,
                ),
                area_crime=SchoolProfileSectionCompletenessDto(
                    status="available",
                    reason_code=None,
                    last_updated_at=datetime(2026, 1, 31, 13, 0, tzinfo=timezone.utc),
                    years_available=None,
                ),
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
            "fsm_pct": 16.9,
            "sen_pct": 13.0,
            "ehcp_pct": 2.1,
            "eal_pct": 8.4,
            "first_language_english_pct": 90.6,
            "first_language_unclassified_pct": 1.0,
            "coverage": {
                "fsm_supported": True,
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
        "ofsted_timeline": {
            "events": [
                {
                    "inspection_number": "10426709",
                    "inspection_start_date": "2025-11-11",
                    "publication_date": "2026-01-11",
                    "inspection_type": "S5 Inspection",
                    "overall_effectiveness_label": None,
                    "headline_outcome_text": "Strong standard",
                    "category_of_concern": None,
                }
            ],
            "coverage": {
                "is_partial_history": False,
                "earliest_event_date": "2015-09-14",
                "latest_event_date": "2026-01-15",
                "events_count": 9,
            },
        },
        "area_context": {
            "deprivation": {
                "lsoa_code": "E01004736",
                "imd_decile": 3,
                "idaci_score": 0.241,
                "idaci_decile": 2,
                "source_release": "IoD2025",
            },
            "crime": {
                "radius_miles": 1.0,
                "latest_month": "2026-01",
                "total_incidents": 486,
                "categories": [
                    {
                        "category": "violent-crime",
                        "incident_count": 132,
                    }
                ],
            },
            "coverage": {
                "has_deprivation": True,
                "has_crime": True,
                "crime_months_available": 12,
            },
        },
        "completeness": {
            "demographics": {
                "status": "partial",
                "reason_code": "partial_metric_coverage",
                "last_updated_at": "2026-01-31T09:00:00Z",
                "years_available": None,
            },
            "ofsted_latest": {
                "status": "available",
                "reason_code": None,
                "last_updated_at": "2026-01-20T10:00:00Z",
                "years_available": None,
            },
            "ofsted_timeline": {
                "status": "available",
                "reason_code": None,
                "last_updated_at": "2026-01-18T11:00:00Z",
                "years_available": None,
            },
            "area_deprivation": {
                "status": "available",
                "reason_code": None,
                "last_updated_at": "2026-01-10T12:00:00Z",
                "years_available": None,
            },
            "area_crime": {
                "status": "available",
                "reason_code": None,
                "last_updated_at": "2026-01-31T13:00:00Z",
                "years_available": None,
            },
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
            ofsted_timeline=None,
            area_context=None,
            completeness=SchoolProfileCompletenessDto(
                demographics=SchoolProfileSectionCompletenessDto(
                    status="unavailable",
                    reason_code="source_file_missing_for_year",
                    last_updated_at=None,
                    years_available=None,
                ),
                ofsted_latest=SchoolProfileSectionCompletenessDto(
                    status="unavailable",
                    reason_code="source_missing",
                    last_updated_at=None,
                    years_available=None,
                ),
                ofsted_timeline=SchoolProfileSectionCompletenessDto(
                    status="unavailable",
                    reason_code="source_missing",
                    last_updated_at=None,
                    years_available=None,
                ),
                area_deprivation=SchoolProfileSectionCompletenessDto(
                    status="unavailable",
                    reason_code="not_joined_yet",
                    last_updated_at=None,
                    years_available=None,
                ),
                area_crime=SchoolProfileSectionCompletenessDto(
                    status="unavailable",
                    reason_code="not_joined_yet",
                    last_updated_at=None,
                    years_available=None,
                ),
            ),
        )
    )
    app.dependency_overrides[get_school_profile_use_case] = lambda: fake_use_case

    response = client.get("/api/v1/schools/123456")

    assert response.status_code == 200
    assert response.json()["demographics_latest"] is None
    assert response.json()["ofsted_latest"] is None
    assert response.json()["ofsted_timeline"] == {
        "events": [],
        "coverage": {
            "is_partial_history": True,
            "earliest_event_date": None,
            "latest_event_date": None,
            "events_count": 0,
        },
    }
    assert response.json()["area_context"] == {
        "deprivation": None,
        "crime": None,
        "coverage": {
            "has_deprivation": False,
            "has_crime": False,
            "crime_months_available": 0,
        },
    }
    assert response.json()["completeness"] == {
        "demographics": {
            "status": "unavailable",
            "reason_code": "source_file_missing_for_year",
            "last_updated_at": None,
            "years_available": None,
        },
        "ofsted_latest": {
            "status": "unavailable",
            "reason_code": "source_missing",
            "last_updated_at": None,
            "years_available": None,
        },
        "ofsted_timeline": {
            "status": "unavailable",
            "reason_code": "source_missing",
            "last_updated_at": None,
            "years_available": None,
        },
        "area_deprivation": {
            "status": "unavailable",
            "reason_code": "not_joined_yet",
            "last_updated_at": None,
            "years_available": None,
        },
        "area_crime": {
            "status": "unavailable",
            "reason_code": "not_joined_yet",
            "last_updated_at": None,
            "years_available": None,
        },
    }


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
