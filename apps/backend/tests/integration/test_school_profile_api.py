from __future__ import annotations

from datetime import date, datetime, timezone
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from civitas.api.dependencies import get_current_session_use_case, get_school_profile_use_case
from civitas.api.main import app
from civitas.application.access.dto import SectionAccessDto
from civitas.application.favourites.dto import SavedSchoolStateDto
from civitas.application.identity.dto import CurrentSessionDto
from civitas.application.school_profiles.dto import (
    SchoolAdmissionsLatestDto,
    SchoolAreaContextCoverageDto,
    SchoolAreaContextDto,
    SchoolAreaCrimeDto,
    SchoolAreaDeprivationDto,
    SchoolAttendanceLatestDto,
    SchoolBehaviourLatestDto,
    SchoolDemographicsCoverageDto,
    SchoolDemographicsLatestDto,
    SchoolDestinationsLatestDto,
    SchoolDestinationStageLatestDto,
    SchoolFinanceLatestDto,
    SchoolLeadershipSnapshotDto,
    SchoolOfstedLatestDto,
    SchoolOfstedTimelineCoverageDto,
    SchoolOfstedTimelineDto,
    SchoolPerformanceDto,
    SchoolPerformanceYearDto,
    SchoolProfileAnalystSectionDto,
    SchoolProfileCompletenessDto,
    SchoolProfileNeighbourhoodSectionDto,
    SchoolProfileResponseDto,
    SchoolProfileSchoolDto,
    SchoolProfileSectionCompletenessDto,
    SchoolWorkforceBreakdownItemDto,
    SchoolWorkforceLatestDto,
)
from civitas.application.school_profiles.errors import (
    SchoolProfileDataUnavailableError,
    SchoolProfileNotFoundError,
)
from civitas.application.subject_performance.dto import (
    SchoolSubjectPerformanceGroupRowDto,
    SchoolSubjectPerformanceLatestDto,
    SchoolSubjectSummaryDto,
)

client = TestClient(app)


class FakeCurrentSessionUseCase:
    def execute(self, *, session_token: str | None) -> CurrentSessionDto:
        return CurrentSessionDto.anonymous(reason="missing")


class FakeGetSchoolProfileUseCase:
    def __init__(
        self,
        result: SchoolProfileResponseDto | None = None,
        error: Exception | None = None,
    ) -> None:
        self._result = result
        self._error = error
        self.calls: list[tuple[str, str | None]] = []

    def execute(
        self,
        *,
        urn: str,
        viewer_user_id: UUID | None = None,
    ) -> SchoolProfileResponseDto:
        self.calls.append((urn, viewer_user_id))
        if self._error is not None:
            raise self._error
        if self._result is None:
            raise AssertionError("FakeGetSchoolProfileUseCase configured without result or error")
        return self._result


def setup_function() -> None:
    app.dependency_overrides.clear()
    app.dependency_overrides[get_current_session_use_case] = lambda: FakeCurrentSessionUseCase()


def teardown_function() -> None:
    app.dependency_overrides.clear()


def _section(status: str = "available", reason_code: str | None = None) -> SectionAccessDto:
    return SectionAccessDto(
        state=status,
        capability_key="premium_neighbourhood" if status != "available" else "premium_ai_analyst",
        reason_code=reason_code,
        product_codes=("premium_launch",) if status == "locked" else (),
        requires_auth=status == "locked",
        requires_purchase=False,
        school_name="Example School" if status == "locked" else None,
    )


def _profile_response() -> SchoolProfileResponseDto:
    timestamp = datetime(2026, 1, 31, 9, 0, tzinfo=timezone.utc)
    return SchoolProfileResponseDto(
        school=SchoolProfileSchoolDto(
            urn="123456",
            name="Example School",
            phase="Primary",
            school_type="Academy",
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
            lat=51.5010,
            lng=-0.1416,
        ),
        overview_text="AI-generated overview text.",
        analyst=SchoolProfileAnalystSectionDto(
            access=SectionAccessDto(
                state="locked",
                capability_key="premium_ai_analyst",
                reason_code="anonymous_user",
                product_codes=("premium_launch",),
                requires_auth=True,
                requires_purchase=False,
                school_name="Example School",
            ),
            teaser_text="First sentence. Second sentence.",
            disclaimer="AI-generated from public data.",
        ),
        demographics_latest=SchoolDemographicsLatestDto(
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
            coverage=SchoolDemographicsCoverageDto(
                fsm_supported=True,
                ethnicity_supported=True,
                top_languages_supported=False,
                fsm6_supported=True,
                gender_supported=True,
                mobility_supported=True,
                send_primary_need_supported=False,
            ),
        ),
        attendance_latest=SchoolAttendanceLatestDto(
            academic_year="2024/25",
            overall_attendance_pct=93.2,
            overall_absence_pct=6.8,
            persistent_absence_pct=14.1,
        ),
        behaviour_latest=SchoolBehaviourLatestDto(
            academic_year="2024/25",
            suspensions_count=121,
            suspensions_rate=16.4,
            permanent_exclusions_count=1,
            permanent_exclusions_rate=0.1,
        ),
        workforce_latest=SchoolWorkforceLatestDto(
            academic_year="2024/25",
            pupil_teacher_ratio=16.3,
            supply_staff_pct=2.4,
            teachers_3plus_years_pct=76.5,
            teacher_turnover_pct=9.8,
            qts_pct=95.2,
            qualifications_level6_plus_pct=81.1,
            teacher_headcount_total=42.0,
            teacher_fte_total=39.5,
            support_staff_headcount_total=28.0,
            support_staff_fte_total=22.4,
            leadership_headcount=4.0,
            teacher_average_mean_salary_gbp=46850.0,
            teacher_absence_pct=8.6,
            teacher_vacancy_rate=1.7,
            third_party_support_staff_headcount=3.0,
            teacher_sex_breakdown=(
                SchoolWorkforceBreakdownItemDto(
                    key="female",
                    label="Female",
                    headcount=28.0,
                    fte=25.8,
                    headcount_pct=66.7,
                    fte_pct=65.3,
                ),
                SchoolWorkforceBreakdownItemDto(
                    key="male",
                    label="Male",
                    headcount=14.0,
                    fte=13.7,
                    headcount_pct=33.3,
                    fte_pct=34.7,
                ),
            ),
            teacher_age_breakdown=(
                SchoolWorkforceBreakdownItemDto(
                    key="30_to_39",
                    label="30 to 39",
                    headcount=18.0,
                    fte=17.0,
                    headcount_pct=42.9,
                    fte_pct=43.0,
                ),
            ),
            teacher_ethnicity_breakdown=(
                SchoolWorkforceBreakdownItemDto(
                    key="white",
                    label="White",
                    headcount=31.0,
                    fte=29.0,
                    headcount_pct=73.8,
                    fte_pct=73.4,
                ),
            ),
            teacher_qualification_breakdown=(
                SchoolWorkforceBreakdownItemDto(
                    key="qualified_teacher_status",
                    label="Qualified teacher status",
                    headcount=40.0,
                    fte=37.9,
                    headcount_pct=95.2,
                    fte_pct=96.0,
                ),
            ),
            support_staff_post_mix=(
                SchoolWorkforceBreakdownItemDto(
                    key="teaching_assistant",
                    label="Teaching assistant",
                    headcount=11.0,
                    fte=8.5,
                ),
                SchoolWorkforceBreakdownItemDto(
                    key="administrative_clerical",
                    label="Administrative / clerical",
                    headcount=6.0,
                    fte=5.2,
                ),
            ),
        ),
        admissions_latest=SchoolAdmissionsLatestDto(
            academic_year="2024/25",
            places_offered_total=90,
            applications_any_preference=126,
            applications_first_preference=98,
            oversubscription_ratio=1.4,
            first_preference_offer_rate=0.918,
            any_preference_offer_rate=0.714,
            admissions_policy="Not applicable",
        ),
        destinations_latest=SchoolDestinationsLatestDto(
            ks4=SchoolDestinationStageLatestDto(
                academic_year="2023/24",
                cohort_count=120,
                qualification_group=None,
                qualification_level=None,
                overall_pct=92.0,
                education_pct=61.0,
                apprenticeship_pct=6.0,
                employment_pct=21.0,
                not_sustained_pct=7.0,
                activity_unknown_pct=4.0,
                fe_pct=28.0,
                other_education_pct=7.0,
                school_sixth_form_pct=19.0,
                sixth_form_college_pct=7.0,
                higher_education_pct=None,
            ),
            study_16_18=None,
        ),
        finance_latest=SchoolFinanceLatestDto(
            academic_year="2023/24",
            total_income_gbp=2070000.0,
            total_expenditure_gbp=2030000.0,
            income_per_pupil_gbp=6634.62,
            expenditure_per_pupil_gbp=6506.41,
            total_staff_costs_gbp=1559500.0,
            staff_costs_pct_of_expenditure=0.7682,
            revenue_reserve_gbp=275000.0,
            revenue_reserve_per_pupil_gbp=881.41,
            in_year_balance_gbp=40000.0,
            total_grant_funding_gbp=1810000.0,
            total_self_generated_funding_gbp=260000.0,
            teaching_staff_costs_gbp=1045000.0,
            supply_teaching_staff_costs_gbp=62500.0,
            education_support_staff_costs_gbp=282000.0,
            other_staff_costs_gbp=170000.0,
            premises_costs_gbp=190000.0,
            educational_supplies_costs_gbp=118000.0,
            bought_in_professional_services_costs_gbp=93000.0,
            catering_costs_gbp=71000.0,
            supply_staff_costs_pct_of_staff_costs=0.0401,
        ),
        leadership_snapshot=SchoolLeadershipSnapshotDto(
            headteacher_name="A. Jones",
            headteacher_start_date=date(2020, 9, 1),
            headteacher_tenure_years=4.5,
            leadership_turnover_score=1.2,
        ),
        performance=SchoolPerformanceDto(
            latest=SchoolPerformanceYearDto(
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
        ofsted_latest=SchoolOfstedLatestDto(
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
            days_since_most_recent_inspection=61,
            is_graded=True,
            ungraded_outcome=None,
            provider_page_url="https://reports.ofsted.gov.uk/provider/21/123456",
        ),
        ofsted_timeline=SchoolOfstedTimelineDto(
            events=(),
            coverage=SchoolOfstedTimelineCoverageDto(
                is_partial_history=False,
                earliest_event_date=date(2015, 9, 14),
                latest_event_date=date(2026, 1, 15),
                events_count=9,
            ),
        ),
        neighbourhood=SchoolProfileNeighbourhoodSectionDto(
            access=SectionAccessDto(
                state="available",
                capability_key="premium_neighbourhood",
                reason_code=None,
                product_codes=(),
                requires_auth=False,
                requires_purchase=False,
            ),
            area_context=SchoolAreaContextDto(
                deprivation=SchoolAreaDeprivationDto(
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
                crime=SchoolAreaCrimeDto(
                    radius_miles=1.0,
                    latest_month="2026-01",
                    total_incidents=486,
                    population_denominator=2000,
                    incidents_per_1000=243.0,
                    annual_incidents_per_1000=(),
                    categories=(),
                ),
                house_prices=None,
                coverage=SchoolAreaContextCoverageDto(
                    has_deprivation=True,
                    has_crime=True,
                    crime_months_available=12,
                    has_house_prices=False,
                    house_price_months_available=0,
                ),
            ),
        ),
        completeness=SchoolProfileCompletenessDto(
            demographics=SchoolProfileSectionCompletenessDto(
                status="partial",
                reason_code="partial_metric_coverage",
                last_updated_at=timestamp,
                years_available=None,
            ),
            attendance=SchoolProfileSectionCompletenessDto(
                status="available",
                reason_code=None,
                last_updated_at=timestamp,
                years_available=None,
            ),
            behaviour=SchoolProfileSectionCompletenessDto(
                status="available",
                reason_code=None,
                last_updated_at=timestamp,
                years_available=None,
            ),
            workforce=SchoolProfileSectionCompletenessDto(
                status="available",
                reason_code=None,
                last_updated_at=timestamp,
                years_available=None,
            ),
            admissions=SchoolProfileSectionCompletenessDto(
                status="available",
                reason_code=None,
                last_updated_at=timestamp,
                years_available=None,
            ),
            destinations=SchoolProfileSectionCompletenessDto(
                status="partial",
                reason_code="unsupported_stage",
                last_updated_at=timestamp,
                years_available=None,
            ),
            finance=SchoolProfileSectionCompletenessDto(
                status="available",
                reason_code=None,
                last_updated_at=timestamp,
                years_available=None,
            ),
            leadership=SchoolProfileSectionCompletenessDto(
                status="available",
                reason_code=None,
                last_updated_at=timestamp,
                years_available=None,
            ),
            performance=SchoolProfileSectionCompletenessDto(
                status="partial",
                reason_code="insufficient_years_published",
                last_updated_at=timestamp,
                years_available=("2023/24", "2024/25"),
            ),
            ofsted_latest=SchoolProfileSectionCompletenessDto(
                status="available",
                reason_code=None,
                last_updated_at=timestamp,
                years_available=None,
            ),
            ofsted_timeline=SchoolProfileSectionCompletenessDto(
                status="available",
                reason_code=None,
                last_updated_at=timestamp,
                years_available=None,
            ),
            area_deprivation=SchoolProfileSectionCompletenessDto(
                status="available",
                reason_code=None,
                last_updated_at=timestamp,
                years_available=None,
            ),
            area_crime=SchoolProfileSectionCompletenessDto(
                status="available",
                reason_code=None,
                last_updated_at=timestamp,
                years_available=None,
            ),
            area_house_prices=SchoolProfileSectionCompletenessDto(
                status="partial",
                reason_code="insufficient_years_published",
                last_updated_at=timestamp,
                years_available=None,
            ),
        ),
        subject_performance=SchoolSubjectPerformanceLatestDto(
            strongest_subjects=(
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
            ),
            weakest_subjects=(
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
            stage_breakdowns=(
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
            latest_updated_at=timestamp,
        ),
        saved_state=SavedSchoolStateDto(
            status="requires_auth",
            saved_at=None,
            capability_key=None,
            reason_code="anonymous_user",
        ),
    )


def test_get_school_profile_returns_expected_contract() -> None:
    fake_use_case = FakeGetSchoolProfileUseCase(result=_profile_response())
    app.dependency_overrides[get_school_profile_use_case] = lambda: fake_use_case

    response = client.get("/api/v1/schools/123456")

    assert response.status_code == 200
    payload = response.json()
    assert payload["school"]["urn"] == "123456"
    assert payload["overview_text"] == "AI-generated overview text."
    assert payload["analyst"] == {
        "access": {
            "state": "locked",
            "capability_key": "premium_ai_analyst",
            "reason_code": "anonymous_user",
            "product_codes": ["premium_launch"],
            "requires_auth": True,
            "requires_purchase": False,
            "school_name": "Example School",
        },
        "text": None,
        "teaser_text": "First sentence. Second sentence.",
        "disclaimer": "AI-generated from public data.",
    }
    assert payload["neighbourhood"]["access"]["state"] == "available"
    assert payload["neighbourhood"]["area_context"]["coverage"]["has_deprivation"] is True
    assert payload["saved_state"] == {
        "status": "requires_auth",
        "saved_at": None,
        "capability_key": None,
        "reason_code": "anonymous_user",
    }
    assert payload["workforce_latest"]["teacher_headcount_total"] == 42.0
    assert payload["workforce_latest"]["teacher_average_mean_salary_gbp"] == 46850.0
    assert payload["workforce_latest"]["teacher_absence_pct"] == 8.6
    assert payload["workforce_latest"]["teacher_vacancy_rate"] == 1.7
    assert payload["workforce_latest"]["third_party_support_staff_headcount"] == 3.0
    assert payload["workforce_latest"]["teacher_sex_breakdown"][0]["key"] == "female"
    assert payload["workforce_latest"]["teacher_age_breakdown"][0]["label"] == "30 to 39"
    assert payload["workforce_latest"]["teacher_ethnicity_breakdown"][0]["label"] == "White"
    assert payload["workforce_latest"]["teacher_qualification_breakdown"][0]["headcount"] == 40.0
    assert payload["workforce_latest"]["support_staff_post_mix"][0]["label"] == "Teaching assistant"
    assert payload["admissions_latest"]["oversubscription_ratio"] == 1.4
    assert payload["admissions_latest"]["applications_any_preference"] == 126
    assert payload["destinations_latest"]["ks4"]["overall_pct"] == 92.0
    assert payload["destinations_latest"]["study_16_18"] is None
    assert payload["finance_latest"]["income_per_pupil_gbp"] == 6634.62
    assert payload["finance_latest"]["staff_costs_pct_of_expenditure"] == 0.7682
    assert payload["finance_latest"]["supply_staff_costs_pct_of_staff_costs"] == 0.0401
    assert payload["subject_performance"]["strongest_subjects"][0]["subject"] == "Mathematics"
    assert payload["subject_performance"]["weakest_subjects"][0]["subject"] == "History"
    assert payload["subject_performance"]["stage_breakdowns"][0]["qualification_family"] == "gcse"
    assert payload["subject_performance"]["stage_breakdowns"][0]["subjects"][1][
        "high_grade_share_pct"
    ] == pytest.approx(22.2222)
    assert payload["benchmarks"] == {"metrics": []}
    assert payload["completeness"]["admissions"]["status"] == "available"
    assert payload["completeness"]["destinations"]["reason_code"] == "unsupported_stage"
    assert payload["completeness"]["finance"]["status"] == "available"
    assert payload["completeness"]["performance"]["years_available"] == ["2023/24", "2024/25"]
    assert fake_use_case.calls == [("123456", None)]


def test_get_school_profile_returns_null_subsections_when_data_missing() -> None:
    result = _profile_response()
    result = SchoolProfileResponseDto(
        school=result.school,
        overview_text=None,
        analyst=SchoolProfileAnalystSectionDto(
            access=SectionAccessDto(
                state="unavailable",
                capability_key="premium_ai_analyst",
                reason_code="artefact_not_published",
                product_codes=(),
                requires_auth=False,
                requires_purchase=False,
            ),
        ),
        demographics_latest=None,
        attendance_latest=None,
        behaviour_latest=None,
        workforce_latest=None,
        admissions_latest=None,
        destinations_latest=None,
        finance_latest=None,
        leadership_snapshot=None,
        performance=None,
        ofsted_latest=None,
        ofsted_timeline=None,
        neighbourhood=SchoolProfileNeighbourhoodSectionDto(
            access=SectionAccessDto(
                state="unavailable",
                capability_key="premium_neighbourhood",
                reason_code="artefact_not_published",
                product_codes=(),
                requires_auth=False,
                requires_purchase=False,
            ),
        ),
        completeness=result.completeness,
        subject_performance=None,
        saved_state=SavedSchoolStateDto(
            status="not_saved",
            saved_at=None,
            capability_key=None,
            reason_code=None,
        ),
    )
    fake_use_case = FakeGetSchoolProfileUseCase(result=result)
    app.dependency_overrides[get_school_profile_use_case] = lambda: fake_use_case

    response = client.get("/api/v1/schools/123456")

    assert response.status_code == 200
    payload = response.json()
    assert payload["demographics_latest"] is None
    assert payload["attendance_latest"] is None
    assert payload["performance"] is None
    assert payload["admissions_latest"] is None
    assert payload["destinations_latest"] is None
    assert payload["finance_latest"] is None
    assert payload["subject_performance"] is None
    assert payload["ofsted_timeline"] == {
        "events": [],
        "coverage": {
            "is_partial_history": True,
            "earliest_event_date": None,
            "latest_event_date": None,
            "events_count": 0,
        },
    }
    assert payload["neighbourhood"] == {
        "access": {
            "state": "unavailable",
            "capability_key": "premium_neighbourhood",
            "reason_code": "artefact_not_published",
            "product_codes": [],
            "requires_auth": False,
            "requires_purchase": False,
            "school_name": None,
        },
        "area_context": None,
        "teaser_text": None,
    }
    assert payload["saved_state"] == {
        "status": "not_saved",
        "saved_at": None,
        "capability_key": None,
        "reason_code": None,
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
