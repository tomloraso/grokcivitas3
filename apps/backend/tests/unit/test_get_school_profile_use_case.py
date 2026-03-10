from datetime import date, datetime, timezone
from typing import Callable

import pytest

from civitas.application.school_profiles.errors import SchoolProfileNotFoundError
from civitas.application.school_profiles.use_cases import GetSchoolProfileUseCase
from civitas.domain.access.models import AccessDecision
from civitas.domain.school_profiles.models import (
    SchoolAreaContext,
    SchoolAreaContextCoverage,
    SchoolAreaCrime,
    SchoolAreaCrimeAnnualRate,
    SchoolAreaCrimeCategory,
    SchoolAreaDeprivation,
    SchoolAttendanceLatest,
    SchoolBehaviourLatest,
    SchoolDemographicsCoverage,
    SchoolDemographicsEthnicityGroup,
    SchoolDemographicsLatest,
    SchoolLeadershipSnapshot,
    SchoolOfstedLatest,
    SchoolOfstedTimeline,
    SchoolOfstedTimelineCoverage,
    SchoolOfstedTimelineEvent,
    SchoolPerformance,
    SchoolProfile,
    SchoolProfileCompleteness,
    SchoolProfileSchool,
    SchoolProfileSectionCompleteness,
    SchoolWorkforceLatest,
)
from civitas.domain.school_summaries.models import SchoolSummary
from civitas.domain.schools.models import PostcodeCoordinates
from civitas.infrastructure.persistence.cached_school_profile_repository import (
    CachedSchoolProfileRepository,
)


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
    def __init__(
        self,
        error: Exception | None = None,
        on_resolve: Callable[[str], None] | None = None,
    ) -> None:
        self._error = error
        self._on_resolve = on_resolve
        self.calls: list[str] = []

    def resolve(self, postcode: str) -> PostcodeCoordinates:
        self.calls.append(postcode)
        if self._error is not None:
            raise self._error
        if self._on_resolve is not None:
            self._on_resolve(postcode)
        return PostcodeCoordinates(
            postcode=postcode,
            lat=51.5,
            lng=-0.14,
            lsoa="Westminster 018C",
            admin_district="Westminster",
            lsoa_code="E01004736",
        )


class FakeSummaryRepository:
    def __init__(self, summaries: dict[str, SchoolSummary] | None = None) -> None:
        self._summaries = summaries or {}
        self.calls: list[tuple[str, str]] = []

    def get_summary(self, urn: str, summary_kind: str) -> SchoolSummary | None:
        self.calls.append((urn, summary_kind))
        return self._summaries.get(summary_kind)


class MutableSchoolProfileRepository:
    def __init__(self, profile: SchoolProfile | None) -> None:
        self.profile = profile
        self.received_urns: list[str] = []

    def get_school_profile(self, urn: str) -> SchoolProfile | None:
        self.received_urns.append(urn)
        return self.profile


class FakeEvaluateAccessUseCase:
    def __init__(self, decisions: dict[str, AccessDecision]) -> None:
        self._decisions = decisions
        self.calls: list[tuple[str, object | None]] = []

    def execute(self, *, requirement_key: str, user_id: object | None, allow_preview: bool = True):
        self.calls.append((requirement_key, user_id))
        return self._decisions[requirement_key]


def _profile(
    demographics_latest: SchoolDemographicsLatest | None = None,
    attendance_latest: SchoolAttendanceLatest | None = None,
    behaviour_latest: SchoolBehaviourLatest | None = None,
    workforce_latest: SchoolWorkforceLatest | None = None,
    leadership_snapshot: SchoolLeadershipSnapshot | None = None,
    performance: SchoolPerformance | None = None,
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
            house_prices=None,
            coverage=SchoolAreaContextCoverage(
                has_deprivation=False,
                has_crime=False,
                crime_months_available=0,
                has_house_prices=False,
                house_price_months_available=0,
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
                reason_code=(
                    None if demographics_latest is not None else "source_file_missing_for_year"
                ),
                last_updated_at=None,
                years_available=None,
            ),
            attendance=SchoolProfileSectionCompleteness(
                status="available" if attendance_latest is not None else "unavailable",
                reason_code=None if attendance_latest is not None else "source_missing",
                last_updated_at=None,
                years_available=None,
            ),
            behaviour=SchoolProfileSectionCompleteness(
                status="available" if behaviour_latest is not None else "unavailable",
                reason_code=None if behaviour_latest is not None else "source_missing",
                last_updated_at=None,
                years_available=None,
            ),
            workforce=SchoolProfileSectionCompleteness(
                status="available" if workforce_latest is not None else "unavailable",
                reason_code=None if workforce_latest is not None else "source_missing",
                last_updated_at=None,
                years_available=None,
            ),
            leadership=SchoolProfileSectionCompleteness(
                status="available" if leadership_snapshot is not None else "unavailable",
                reason_code=None if leadership_snapshot is not None else "source_missing",
                last_updated_at=None,
                years_available=None,
            ),
            performance=SchoolProfileSectionCompleteness(
                status="unavailable",
                reason_code="source_missing",
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
            area_house_prices=SchoolProfileSectionCompleteness(
                status="available" if area_context.house_prices is not None else "unavailable",
                reason_code=None if area_context.house_prices is not None else "not_joined_yet",
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
            website="https://example-school.test",
            telephone="+442079460123",
            head_title="Dr",
            head_first_name="Ada",
            head_last_name="Lovelace",
            head_job_title="Headteacher",
            address_street="1 Example Street",
            address_locality="Westminster",
            address_line3=None,
            address_town="London",
            address_county="Greater London",
            statutory_low_age=4,
            statutory_high_age=11,
            gender="Mixed",
            religious_character="None",
            diocese=None,
            admissions_policy="Not applicable",
            sixth_form="Does not have a sixth form",
            nursery_provision="No Nursery Classes",
            boarders="No boarders",
            fsm_pct_gias=12.4,
            trust_name=None,
            trust_flag="Not applicable",
            federation_name=None,
            federation_flag="Not applicable",
            la_name="Westminster",
            la_code="213",
            urban_rural="Urban major conurbation",
            number_of_boys=155,
            number_of_girls=157,
            lsoa_code="E01004736",
            lsoa_name="Westminster 018A",
            last_changed_date=date(2026, 1, 15),
            lat=51.5,
            lng=-0.14,
        ),
        demographics_latest=demographics_latest,
        attendance_latest=attendance_latest,
        behaviour_latest=behaviour_latest,
        workforce_latest=workforce_latest,
        leadership_snapshot=leadership_snapshot,
        performance=performance,
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
                fsm_pct=16.8,
                sen_pct=13.0,
                ehcp_pct=2.1,
                eal_pct=8.4,
                first_language_english_pct=90.6,
                first_language_unclassified_pct=1.0,
                coverage=SchoolDemographicsCoverage(
                    fsm_supported=True,
                    ethnicity_supported=True,
                    top_languages_supported=False,
                ),
                ethnicity_breakdown=(
                    SchoolDemographicsEthnicityGroup(
                        key="white_british",
                        label="White British",
                        percentage=49.0,
                        count=98,
                    ),
                ),
            ),
            attendance_latest=SchoolAttendanceLatest(
                academic_year="2024/25",
                overall_attendance_pct=93.2,
                overall_absence_pct=6.8,
                persistent_absence_pct=14.1,
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
            leadership_snapshot=SchoolLeadershipSnapshot(
                headteacher_name="A. Jones",
                headteacher_start_date=date(2020, 9, 1),
                headteacher_tenure_years=4.5,
                leadership_turnover_score=1.2,
            ),
            ofsted_latest=SchoolOfstedLatest(
                overall_effectiveness_code="2",
                overall_effectiveness_label="Good",
                inspection_start_date=date(2025, 10, 10),
                publication_date=date(2025, 11, 15),
                latest_oeif_inspection_start_date=date(2025, 10, 10),
                latest_oeif_publication_date=date(2025, 11, 15),
                quality_of_education_code="2",
                quality_of_education_label="Good",
                behaviour_and_attitudes_code="2",
                behaviour_and_attitudes_label="Good",
                personal_development_code="2",
                personal_development_label="Good",
                leadership_and_management_code="2",
                leadership_and_management_label="Good",
                latest_ungraded_inspection_date=date(2026, 1, 2),
                latest_ungraded_publication_date=date(2026, 1, 20),
                most_recent_inspection_date=date(2026, 1, 2),
                days_since_most_recent_inspection=60,
                is_graded=True,
                ungraded_outcome=None,
                provider_page_url="https://reports.ofsted.gov.uk/provider/21/123456",
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
                    imd_score=27.1,
                    imd_rank=4825,
                    imd_decile=3,
                    idaci_score=0.241,
                    idaci_decile=2,
                    income_score=0.12,
                    income_rank=7200,
                    income_decile=2,
                    employment_score=0.11,
                    employment_rank=7000,
                    employment_decile=2,
                    education_score=0.16,
                    education_rank=8100,
                    education_decile=3,
                    health_score=0.13,
                    health_rank=7600,
                    health_decile=3,
                    crime_score=0.18,
                    crime_rank=8900,
                    crime_decile=4,
                    barriers_score=0.14,
                    barriers_rank=7800,
                    barriers_decile=3,
                    living_environment_score=0.17,
                    living_environment_rank=8400,
                    living_environment_decile=4,
                    population_total=2000,
                    local_authority_district_code="E09000033",
                    local_authority_district_name="Westminster",
                    source_release="IoD2025",
                ),
                crime=SchoolAreaCrime(
                    radius_miles=1.0,
                    latest_month="2026-01",
                    total_incidents=486,
                    population_denominator=2000,
                    incidents_per_1000=243.0,
                    annual_incidents_per_1000=(
                        SchoolAreaCrimeAnnualRate(
                            year=2025,
                            total_incidents=240,
                            incidents_per_1000=120.0,
                        ),
                        SchoolAreaCrimeAnnualRate(
                            year=2026,
                            total_incidents=486,
                            incidents_per_1000=243.0,
                        ),
                    ),
                    categories=(
                        SchoolAreaCrimeCategory(
                            category="violent-crime",
                            incident_count=132,
                        ),
                    ),
                ),
                house_prices=None,
                coverage=SchoolAreaContextCoverage(
                    has_deprivation=True,
                    has_crime=True,
                    crime_months_available=12,
                    has_house_prices=False,
                    house_price_months_available=0,
                ),
            ),
            completeness=SchoolProfileCompleteness(
                demographics=SchoolProfileSectionCompleteness(
                    status="partial",
                    reason_code="partial_metric_coverage",
                    last_updated_at=None,
                    years_available=None,
                ),
                attendance=SchoolProfileSectionCompleteness(
                    status="available",
                    reason_code=None,
                    last_updated_at=None,
                    years_available=None,
                ),
                behaviour=SchoolProfileSectionCompleteness(
                    status="available",
                    reason_code=None,
                    last_updated_at=None,
                    years_available=None,
                ),
                workforce=SchoolProfileSectionCompleteness(
                    status="available",
                    reason_code=None,
                    last_updated_at=None,
                    years_available=None,
                ),
                leadership=SchoolProfileSectionCompleteness(
                    status="available",
                    reason_code=None,
                    last_updated_at=None,
                    years_available=None,
                ),
                performance=SchoolProfileSectionCompleteness(
                    status="available",
                    reason_code=None,
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
                area_house_prices=SchoolProfileSectionCompleteness(
                    status="unavailable",
                    reason_code="not_joined_yet",
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
    assert result.school.website == "https://example-school.test"
    assert result.school.telephone == "+442079460123"
    assert result.school.head_first_name == "Ada"
    assert result.school.head_last_name == "Lovelace"
    assert result.school.statutory_low_age == 4
    assert result.school.statutory_high_age == 11
    assert result.school.la_name == "Westminster"
    assert result.school.lsoa_code == "E01004736"
    assert result.overview_text is None
    assert result.analyst.access.state == "unavailable"
    assert result.analyst.access.reason_code == "artefact_not_published"
    assert result.analyst.text is None
    assert result.demographics_latest is not None
    assert result.demographics_latest.academic_year == "2024/25"
    assert result.demographics_latest.coverage.ethnicity_supported is True
    assert result.demographics_latest.ethnicity_breakdown[0].key == "white_british"
    assert result.demographics_latest.ethnicity_breakdown[0].percentage == 49.0
    assert result.attendance_latest is not None
    assert result.attendance_latest.overall_attendance_pct == 93.2
    assert result.behaviour_latest is not None
    assert result.behaviour_latest.suspensions_count == 121
    assert result.workforce_latest is not None
    assert result.workforce_latest.pupil_teacher_ratio == 16.3
    assert result.leadership_snapshot is not None
    assert result.leadership_snapshot.headteacher_name == "A. Jones"
    assert result.ofsted_latest is not None
    assert result.ofsted_latest.overall_effectiveness_label == "Good"
    assert result.ofsted_latest.quality_of_education_label == "Good"
    assert result.ofsted_latest.days_since_most_recent_inspection == 60
    assert (
        result.ofsted_latest.provider_page_url == "https://reports.ofsted.gov.uk/provider/21/123456"
    )
    assert result.ofsted_timeline is not None
    assert result.ofsted_timeline.coverage.is_partial_history is False
    assert result.ofsted_timeline.events[0].inspection_number == "10426709"
    assert result.neighbourhood.access.state == "available"
    assert result.neighbourhood.area_context is not None
    assert result.neighbourhood.area_context.coverage.has_deprivation is True
    assert result.neighbourhood.area_context.deprivation is not None
    assert result.neighbourhood.area_context.deprivation.imd_score == 27.1
    assert result.neighbourhood.area_context.deprivation.imd_rank == 4825
    assert result.neighbourhood.area_context.coverage.has_crime is True
    assert result.neighbourhood.area_context.coverage.has_house_prices is False
    assert result.completeness.demographics.status == "partial"
    assert result.completeness.attendance.status == "available"
    assert result.completeness.behaviour.status == "available"
    assert result.completeness.workforce.status == "available"
    assert result.completeness.leadership.status == "available"
    assert result.completeness.performance.status == "available"
    assert result.completeness.demographics.reason_code == "partial_metric_coverage"
    assert result.completeness.area_house_prices.status == "unavailable"


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
    assert result.attendance_latest is None
    assert result.behaviour_latest is None
    assert result.workforce_latest is None
    assert result.leadership_snapshot is None
    assert result.ofsted_latest is None
    assert result.ofsted_timeline is not None
    assert result.ofsted_timeline.events == ()
    assert result.analyst.access.state == "unavailable"
    assert result.neighbourhood.access.state == "unavailable"
    assert result.neighbourhood.area_context is None
    assert result.completeness.demographics.status == "unavailable"
    assert result.completeness.workforce.status == "unavailable"
    assert result.completeness.leadership.status == "unavailable"
    assert result.completeness.performance.status == "unavailable"
    assert result.completeness.ofsted_timeline.status == "unavailable"
    assert result.completeness.area_deprivation.reason_code == "not_joined_yet"
    assert result.completeness.area_house_prices.reason_code == "not_joined_yet"


def test_get_school_profile_includes_overview_summary_when_available() -> None:
    repository = FakeSchoolProfileRepository(profile=_profile())
    summary_repository = FakeSummaryRepository(
        summaries={
            "overview": SchoolSummary(
                urn="123456",
                summary_kind="overview",
                text="AI-generated overview text.",
                data_version_hash="hash-123",
                prompt_version="overview.v1",
                model_id="grok-test",
                generated_at=datetime(2026, 3, 5, 12, 0, tzinfo=timezone.utc),
                generation_duration_ms=145,
            ),
            "analyst": SchoolSummary(
                urn="123456",
                summary_kind="analyst",
                text="AI-generated analyst text.",
                data_version_hash="hash-456",
                prompt_version="analyst.v1",
                model_id="grok-test",
                generated_at=datetime(2026, 3, 5, 12, 5, tzinfo=timezone.utc),
                generation_duration_ms=165,
            ),
        }
    )
    use_case = GetSchoolProfileUseCase(
        school_profile_repository=repository,
        summary_repository=summary_repository,
    )

    result = use_case.execute(urn="123456")

    assert result.overview_text == "AI-generated overview text."
    assert result.analyst.access.state == "available"
    assert result.analyst.text == "AI-generated analyst text."
    assert result.analyst.disclaimer is not None
    assert summary_repository.calls == [("123456", "overview"), ("123456", "analyst")]


def test_get_school_profile_returns_locked_preview_sections_for_free_viewer() -> None:
    repository = FakeSchoolProfileRepository(
        profile=_profile(
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
                crime=None,
                house_prices=None,
                coverage=SchoolAreaContextCoverage(
                    has_deprivation=True,
                    has_crime=False,
                    crime_months_available=0,
                    has_house_prices=False,
                    house_price_months_available=0,
                ),
            )
        )
    )
    summary_repository = FakeSummaryRepository(
        summaries={
            "analyst": SchoolSummary(
                urn="123456",
                summary_kind="analyst",
                text="First sentence. Second sentence. Third sentence. Fourth sentence.",
                data_version_hash="hash-456",
                prompt_version="analyst.v1",
                model_id="grok-test",
                generated_at=datetime(2026, 3, 5, 12, 5, tzinfo=timezone.utc),
                generation_duration_ms=165,
            ),
        }
    )
    evaluate_access_use_case = FakeEvaluateAccessUseCase(
        decisions={
            "school_profile.ai_analyst": AccessDecision(
                requirement_key="school_profile.ai_analyst",
                access_level="preview_only",
                section_state="locked",
                capability_key="premium_ai_analyst",
                reason_code="anonymous_user",
                available_product_codes=("premium_launch",),
                requires_auth=True,
                requires_purchase=False,
            ),
            "school_profile.neighbourhood": AccessDecision(
                requirement_key="school_profile.neighbourhood",
                access_level="preview_only",
                section_state="locked",
                capability_key="premium_neighbourhood",
                reason_code="anonymous_user",
                available_product_codes=("premium_launch",),
                requires_auth=True,
                requires_purchase=False,
            ),
        }
    )
    use_case = GetSchoolProfileUseCase(
        school_profile_repository=repository,
        summary_repository=summary_repository,
        evaluate_access_use_case=evaluate_access_use_case,
    )

    result = use_case.execute(urn="123456")

    assert result.analyst.access.state == "locked"
    assert result.analyst.access.school_name == "Example School"
    assert result.analyst.text is None
    assert result.analyst.teaser_text == "First sentence. Second sentence. Third sentence."
    assert result.neighbourhood.access.state == "locked"
    assert result.neighbourhood.area_context is None
    assert result.neighbourhood.teaser_text is not None


def test_get_school_profile_rehydrates_area_context_when_deprivation_is_missing() -> None:
    repository = FakeSchoolProfileRepository(
        profile_sequence=(
            _profile(),
            _profile(
                area_context=SchoolAreaContext(
                    deprivation=SchoolAreaDeprivation(
                        lsoa_code="E01004736",
                        imd_score=27.1,
                        imd_rank=4825,
                        imd_decile=3,
                        idaci_score=0.241,
                        idaci_decile=2,
                        income_score=0.12,
                        income_rank=7200,
                        income_decile=2,
                        employment_score=0.11,
                        employment_rank=7000,
                        employment_decile=2,
                        education_score=0.16,
                        education_rank=8100,
                        education_decile=3,
                        health_score=0.13,
                        health_rank=7600,
                        health_decile=3,
                        crime_score=0.18,
                        crime_rank=8900,
                        crime_decile=4,
                        barriers_score=0.14,
                        barriers_rank=7800,
                        barriers_decile=3,
                        living_environment_score=0.17,
                        living_environment_rank=8400,
                        living_environment_decile=4,
                        population_total=2000,
                        local_authority_district_code="E09000033",
                        local_authority_district_name="Westminster",
                        source_release="IoD2025",
                    ),
                    crime=SchoolAreaCrime(
                        radius_miles=1.0,
                        latest_month="2026-01",
                        total_incidents=486,
                        population_denominator=2000,
                        incidents_per_1000=243.0,
                        annual_incidents_per_1000=(
                            SchoolAreaCrimeAnnualRate(
                                year=2025,
                                total_incidents=240,
                                incidents_per_1000=120.0,
                            ),
                            SchoolAreaCrimeAnnualRate(
                                year=2026,
                                total_incidents=486,
                                incidents_per_1000=243.0,
                            ),
                        ),
                        categories=(
                            SchoolAreaCrimeCategory(
                                category="violent-crime",
                                incident_count=132,
                            ),
                        ),
                    ),
                    house_prices=None,
                    coverage=SchoolAreaContextCoverage(
                        has_deprivation=True,
                        has_crime=True,
                        crime_months_available=12,
                        has_house_prices=False,
                        house_price_months_available=0,
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
    assert result.neighbourhood.area_context is not None
    assert result.neighbourhood.area_context.coverage.has_deprivation is True
    assert result.neighbourhood.area_context.deprivation is not None
    assert result.neighbourhood.area_context.deprivation.lsoa_code == "E01004736"


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
    assert result.neighbourhood.access.state == "unavailable"
    assert result.neighbourhood.area_context is None


def test_get_school_profile_uses_refresh_repository_to_bypass_cached_profile_on_rehydrate() -> None:
    cached_delegate = MutableSchoolProfileRepository(_profile())
    refresh_repository = MutableSchoolProfileRepository(_profile())
    resolver = FakePostcodeContextResolver(
        on_resolve=lambda _postcode: setattr(
            refresh_repository,
            "profile",
            _profile(
                area_context=SchoolAreaContext(
                    deprivation=SchoolAreaDeprivation(
                        lsoa_code="E01004736",
                        imd_score=27.1,
                        imd_rank=4825,
                        imd_decile=3,
                        idaci_score=0.241,
                        idaci_decile=2,
                        income_score=0.12,
                        income_rank=7200,
                        income_decile=2,
                        employment_score=0.11,
                        employment_rank=7000,
                        employment_decile=2,
                        education_score=0.16,
                        education_rank=8100,
                        education_decile=3,
                        health_score=0.13,
                        health_rank=7600,
                        health_decile=3,
                        crime_score=0.18,
                        crime_rank=8900,
                        crime_decile=4,
                        barriers_score=0.14,
                        barriers_rank=7800,
                        barriers_decile=3,
                        living_environment_score=0.17,
                        living_environment_rank=8400,
                        living_environment_decile=4,
                        population_total=2000,
                        local_authority_district_code="E09000033",
                        local_authority_district_name="Westminster",
                        source_release="IoD2025",
                    ),
                    crime=None,
                    house_prices=None,
                    coverage=SchoolAreaContextCoverage(
                        has_deprivation=True,
                        has_crime=False,
                        crime_months_available=0,
                        has_house_prices=False,
                        house_price_months_available=0,
                    ),
                )
            ),
        )
    )
    use_case = GetSchoolProfileUseCase(
        school_profile_repository=CachedSchoolProfileRepository(
            delegate=cached_delegate,
            ttl_seconds=300,
        ),
        refresh_school_profile_repository=refresh_repository,
        postcode_context_resolver=resolver,
    )

    result = use_case.execute(urn="123456")

    assert cached_delegate.received_urns == ["123456"]
    assert refresh_repository.received_urns == ["123456"]
    assert resolver.calls == ["SW1A 1AA"]
    assert result.neighbourhood.area_context is not None
    assert result.neighbourhood.area_context.coverage.has_deprivation is True
    assert result.neighbourhood.area_context.deprivation is not None
    assert result.neighbourhood.area_context.deprivation.lsoa_code == "E01004736"
