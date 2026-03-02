from datetime import date

import pytest

from civitas.application.school_profiles.errors import SchoolProfileNotFoundError
from civitas.application.school_profiles.use_cases import GetSchoolProfileUseCase
from civitas.domain.school_profiles.models import (
    SchoolDemographicsCoverage,
    SchoolDemographicsLatest,
    SchoolOfstedLatest,
    SchoolProfile,
    SchoolProfileSchool,
)


class FakeSchoolProfileRepository:
    def __init__(self, profile: SchoolProfile | None) -> None:
        self._profile = profile
        self.received_urns: list[str] = []

    def get_school_profile(self, urn: str) -> SchoolProfile | None:
        self.received_urns.append(urn)
        return self._profile


def _profile(
    demographics_latest: SchoolDemographicsLatest | None = None,
    ofsted_latest: SchoolOfstedLatest | None = None,
) -> SchoolProfile:
    return SchoolProfile(
        school=SchoolProfileSchool(
            urn="123456",
            name="Example School",
            phase="Primary",
            school_type="Community school",
            status="Open",
            postcode="SW1A 1AA",
            lat=51.5,
            lng=-0.14,
        ),
        demographics_latest=demographics_latest,
        ofsted_latest=ofsted_latest,
    )


def test_get_school_profile_returns_contract_dto() -> None:
    repository = FakeSchoolProfileRepository(
        profile=_profile(
            demographics_latest=SchoolDemographicsLatest(
                academic_year="2024/25",
                disadvantaged_pct=17.2,
                fsm_pct=None,
                sen_pct=13.0,
                ehcp_pct=2.1,
                eal_pct=8.4,
                first_language_english_pct=90.6,
                first_language_unclassified_pct=1.0,
                coverage=SchoolDemographicsCoverage(
                    fsm_supported=False,
                    ethnicity_supported=False,
                    top_languages_supported=False,
                ),
            ),
            ofsted_latest=SchoolOfstedLatest(
                overall_effectiveness_code="2",
                overall_effectiveness_label="Good",
                inspection_start_date=date(2025, 10, 10),
                publication_date=date(2025, 11, 15),
                is_graded=True,
                ungraded_outcome=None,
            ),
        )
    )
    use_case = GetSchoolProfileUseCase(school_profile_repository=repository)

    result = use_case.execute(urn=" 123456 ")

    assert repository.received_urns == ["123456"]
    assert result.school.urn == "123456"
    assert result.school.name == "Example School"
    assert result.demographics_latest is not None
    assert result.demographics_latest.academic_year == "2024/25"
    assert result.demographics_latest.coverage.ethnicity_supported is False
    assert result.ofsted_latest is not None
    assert result.ofsted_latest.overall_effectiveness_label == "Good"


def test_get_school_profile_raises_not_found_when_repository_returns_none() -> None:
    repository = FakeSchoolProfileRepository(profile=None)
    use_case = GetSchoolProfileUseCase(school_profile_repository=repository)

    with pytest.raises(SchoolProfileNotFoundError, match="School with URN '999999' was not found."):
        use_case.execute(urn="999999")


def test_get_school_profile_preserves_null_subsections() -> None:
    repository = FakeSchoolProfileRepository(profile=_profile())
    use_case = GetSchoolProfileUseCase(school_profile_repository=repository)

    result = use_case.execute(urn="123456")

    assert result.demographics_latest is None
    assert result.ofsted_latest is None
