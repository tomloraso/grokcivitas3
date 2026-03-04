from datetime import date

import pytest

from civitas.application.school_profiles.errors import SchoolProfileNotFoundError
from civitas.application.school_profiles.use_cases import GetSchoolProfileUseCase
from civitas.domain.school_profiles.models import (
    SchoolAreaContext,
    SchoolAreaContextCoverage,
    SchoolAreaCrime,
    SchoolAreaCrimeCategory,
    SchoolAreaDeprivation,
    SchoolDemographicsCoverage,
    SchoolDemographicsLatest,
    SchoolOfstedLatest,
    SchoolOfstedTimeline,
    SchoolOfstedTimelineCoverage,
    SchoolOfstedTimelineEvent,
    SchoolProfile,
    SchoolProfileCompleteness,
    SchoolProfileSchool,
    SchoolProfileSectionCompleteness,
)
from civitas.domain.schools.models import PostcodeCoordinates


class FakeSchoolProfileRepository:
    def __init__(
        self,
        profile: SchoolProfile | None = None,
        profile_sequence: tuple[SchoolProfile | None, ...] | None = None,
    ) -> None:
        self._profile = profile
        self._profile_sequence = list(profile_sequence) if profile_sequence is not None else None
        self.received_urns: list[str] = []

    def get_school_profile(self, urn: str) -> SchoolProfile | None:
        self.received_urns.append(urn)
        if self._profile_sequence is not None:
            if len(self._profile_sequence) > 1:
                return self._profile_sequence.pop(0)
            return self._profile_sequence[0]
        return self._profile


class FakePostcodeContextResolver:
    def __init__(self, error: Exception | None = None) -> None:
        self._error = error
        self.calls: list[str] = []

    def resolve(self, postcode: str) -> PostcodeCoordinates:
        self.calls.append(postcode)
        if self._error is not None:
            raise self._error
        return PostcodeCoordinates(
            postcode=postcode,
            lat=51.5,
            lng=-0.14,
            lsoa="Westminster 018C",
            admin_district="Westminster",
            lsoa_code="E01004736",
        )


def _profile(
    demographics_latest: SchoolDemographicsLatest | None = None,
    ofsted_latest: SchoolOfstedLatest | None = None,
    ofsted_timeline: SchoolOfstedTimeline | None = None,
    area_context: SchoolAreaContext | None = None,
    completeness: SchoolProfileCompleteness | None = None,
) -> SchoolProfile:
    if ofsted_timeline is None:
        ofsted_timeline = SchoolOfstedTimeline(
            events=(),
            coverage=SchoolOfstedTimelineCoverage(
                is_partial_history=True,
                earliest_event_date=None,
                latest_event_date=None,
                events_count=0,
            ),
        )
    if area_context is None:
        area_context = SchoolAreaContext(
            deprivation=None,
            crime=None,
            coverage=SchoolAreaContextCoverage(
                has_deprivation=False,
                has_crime=False,
                crime_months_available=0,
            ),
        )
    if completeness is None:
        ofsted_timeline_status = (
            "unavailable"
            if len(ofsted_timeline.events) == 0
            else ("partial" if ofsted_timeline.coverage.is_partial_history else "available")
        )
        completeness = SchoolProfileCompleteness(
            demographics=SchoolProfileSectionCompleteness(
                status="available" if demographics_latest is not None else "unavailable",
                reason_code=None if demographics_latest is not None else "source_missing",
                last_updated_at=None,
                years_available=None,
            ),
            ofsted_latest=SchoolProfileSectionCompleteness(
                status="available" if ofsted_latest is not None else "unavailable",
                reason_code=None if ofsted_latest is not None else "source_missing",
                last_updated_at=None,
                years_available=None,
            ),
            ofsted_timeline=SchoolProfileSectionCompleteness(
                status=ofsted_timeline_status,
                reason_code=None if ofsted_timeline_status == "available" else "source_missing",
                last_updated_at=None,
                years_available=None,
            ),
            area_deprivation=SchoolProfileSectionCompleteness(
                status="available" if area_context.deprivation is not None else "unavailable",
                reason_code=None if area_context.deprivation is not None else "not_joined_yet",
                last_updated_at=None,
                years_available=None,
            ),
            area_crime=SchoolProfileSectionCompleteness(
                status="available" if area_context.crime is not None else "unavailable",
                reason_code=None if area_context.crime is not None else "not_joined_yet",
                last_updated_at=None,
                years_available=None,
            ),
        )
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
        ofsted_timeline=ofsted_timeline,
        area_context=area_context,
        completeness=completeness,
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
            ofsted_timeline=SchoolOfstedTimeline(
                events=(
                    SchoolOfstedTimelineEvent(
                        inspection_number="10426709",
                        inspection_start_date=date(2025, 11, 11),
                        publication_date=date(2026, 1, 11),
                        inspection_type="S5 Inspection",
                        overall_effectiveness_label=None,
                        headline_outcome_text="Strong standard",
                        category_of_concern=None,
                    ),
                ),
                coverage=SchoolOfstedTimelineCoverage(
                    is_partial_history=False,
                    earliest_event_date=date(2015, 9, 14),
                    latest_event_date=date(2025, 11, 11),
                    events_count=1,
                ),
            ),
            area_context=SchoolAreaContext(
                deprivation=SchoolAreaDeprivation(
                    lsoa_code="E01004736",
                    imd_decile=3,
                    idaci_score=0.241,
                    idaci_decile=2,
                    source_release="IoD2025",
                ),
                crime=SchoolAreaCrime(
                    radius_miles=1.0,
                    latest_month="2026-01",
                    total_incidents=486,
                    categories=(
                        SchoolAreaCrimeCategory(
                            category="violent-crime",
                            incident_count=132,
                        ),
                    ),
                ),
                coverage=SchoolAreaContextCoverage(
                    has_deprivation=True,
                    has_crime=True,
                    crime_months_available=12,
                ),
            ),
            completeness=SchoolProfileCompleteness(
                demographics=SchoolProfileSectionCompleteness(
                    status="partial",
                    reason_code="source_not_provided",
                    last_updated_at=None,
                    years_available=None,
                ),
                ofsted_latest=SchoolProfileSectionCompleteness(
                    status="available",
                    reason_code=None,
                    last_updated_at=None,
                    years_available=None,
                ),
                ofsted_timeline=SchoolProfileSectionCompleteness(
                    status="available",
                    reason_code=None,
                    last_updated_at=None,
                    years_available=None,
                ),
                area_deprivation=SchoolProfileSectionCompleteness(
                    status="available",
                    reason_code=None,
                    last_updated_at=None,
                    years_available=None,
                ),
                area_crime=SchoolProfileSectionCompleteness(
                    status="available",
                    reason_code=None,
                    last_updated_at=None,
                    years_available=None,
                ),
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
    assert result.ofsted_timeline is not None
    assert result.ofsted_timeline.coverage.is_partial_history is False
    assert result.ofsted_timeline.events[0].inspection_number == "10426709"
    assert result.area_context is not None
    assert result.area_context.coverage.has_deprivation is True
    assert result.area_context.coverage.has_crime is True
    assert result.completeness.demographics.status == "partial"
    assert result.completeness.demographics.reason_code == "source_not_provided"


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
    assert result.ofsted_timeline is not None
    assert result.ofsted_timeline.events == ()
    assert result.area_context is not None
    assert result.area_context.deprivation is None
    assert result.area_context.crime is None
    assert result.completeness.demographics.status == "unavailable"
    assert result.completeness.ofsted_timeline.status == "unavailable"
    assert result.completeness.area_deprivation.reason_code == "not_joined_yet"


def test_get_school_profile_rehydrates_area_context_when_deprivation_is_missing() -> None:
    repository = FakeSchoolProfileRepository(
        profile_sequence=(
            _profile(),
            _profile(
                area_context=SchoolAreaContext(
                    deprivation=SchoolAreaDeprivation(
                        lsoa_code="E01004736",
                        imd_decile=3,
                        idaci_score=0.241,
                        idaci_decile=2,
                        source_release="IoD2025",
                    ),
                    crime=SchoolAreaCrime(
                        radius_miles=1.0,
                        latest_month="2026-01",
                        total_incidents=486,
                        categories=(
                            SchoolAreaCrimeCategory(
                                category="violent-crime",
                                incident_count=132,
                            ),
                        ),
                    ),
                    coverage=SchoolAreaContextCoverage(
                        has_deprivation=True,
                        has_crime=True,
                        crime_months_available=12,
                    ),
                ),
            ),
        )
    )
    resolver = FakePostcodeContextResolver()
    use_case = GetSchoolProfileUseCase(
        school_profile_repository=repository,
        postcode_context_resolver=resolver,
    )

    result = use_case.execute(urn="123456")

    assert repository.received_urns == ["123456", "123456"]
    assert resolver.calls == ["SW1A 1AA"]
    assert result.area_context is not None
    assert result.area_context.coverage.has_deprivation is True
    assert result.area_context.deprivation is not None
    assert result.area_context.deprivation.lsoa_code == "E01004736"


def test_get_school_profile_keeps_profile_when_context_rehydrate_fails() -> None:
    repository = FakeSchoolProfileRepository(profile=_profile())
    resolver = FakePostcodeContextResolver(error=RuntimeError("resolver unavailable"))
    use_case = GetSchoolProfileUseCase(
        school_profile_repository=repository,
        postcode_context_resolver=resolver,
    )

    result = use_case.execute(urn="123456")

    assert repository.received_urns == ["123456"]
    assert resolver.calls == ["SW1A 1AA"]
    assert result.area_context is not None
    assert result.area_context.coverage.has_deprivation is False
