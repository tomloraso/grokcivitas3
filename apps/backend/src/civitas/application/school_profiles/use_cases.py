import re
from uuid import UUID

from civitas.application.access.dto import SectionAccessDto
from civitas.application.access.policies import (
    SCHOOL_PROFILE_AI_ANALYST_REQUIREMENT,
    SCHOOL_PROFILE_NEIGHBOURHOOD_REQUIREMENT,
    get_access_requirement,
)
from civitas.application.access.use_cases import EvaluateAccessUseCase
from civitas.application.favourites.dto import (
    SavedSchoolStateDto,
    anonymous_saved_school_state,
)
from civitas.application.favourites.ports.saved_school_state_resolver import (
    SavedSchoolStateResolver,
)
from civitas.application.school_profiles.dto import (
    SchoolAdmissionsLatestDto,
    SchoolAreaContextCoverageDto,
    SchoolAreaContextDto,
    SchoolAreaCrimeAnnualRateDto,
    SchoolAreaCrimeCategoryDto,
    SchoolAreaCrimeDto,
    SchoolAreaDeprivationDto,
    SchoolAreaHousePricePointDto,
    SchoolAreaHousePricesDto,
    SchoolAttendanceLatestDto,
    SchoolBehaviourLatestDto,
    SchoolBenchmarkContextDto,
    SchoolDemographicsCoverageDto,
    SchoolDemographicsEthnicityGroupDto,
    SchoolDemographicsHomeLanguageDto,
    SchoolDemographicsLatestDto,
    SchoolDemographicsSendPrimaryNeedDto,
    SchoolDestinationsLatestDto,
    SchoolDestinationStageLatestDto,
    SchoolFinanceLatestDto,
    SchoolLeadershipSnapshotDto,
    SchoolOfstedLatestDto,
    SchoolOfstedTimelineCoverageDto,
    SchoolOfstedTimelineDto,
    SchoolOfstedTimelineEventDto,
    SchoolPerformanceDto,
    SchoolPerformanceYearDto,
    SchoolProfileAnalystSectionDto,
    SchoolProfileBenchmarksDto,
    SchoolProfileCompletenessDto,
    SchoolProfileMetricBenchmarkDto,
    SchoolProfileNeighbourhoodSectionDto,
    SchoolProfileResponseDto,
    SchoolProfileSchoolDto,
    SchoolProfileSectionCompletenessDto,
    SchoolWorkforceBreakdownItemDto,
    SchoolWorkforceLatestDto,
)
from civitas.application.school_profiles.errors import SchoolProfileNotFoundError
from civitas.application.school_profiles.ports.postcode_context_resolver import (
    PostcodeContextResolver,
)
from civitas.application.school_profiles.ports.school_profile_repository import (
    SchoolProfileRepository,
)
from civitas.application.school_summaries.ports.summary_repository import SummaryRepository
from civitas.application.school_trends.ports.school_trends_repository import (
    SchoolTrendsRepository,
)
from civitas.application.subject_performance.dto import (
    SchoolSubjectPerformanceGroupRowDto,
    SchoolSubjectPerformanceLatestDto,
    SchoolSubjectSummaryDto,
)
from civitas.application.subject_performance.ports.subject_performance_repository import (
    SubjectPerformanceRepository,
)
from civitas.domain.access.value_objects import AccessDecisionReasonCode
from civitas.domain.school_profiles.models import SchoolDestinationStageLatest, SchoolProfile
from civitas.domain.school_trends.models import SchoolMetricBenchmarkYearlyRow
from civitas.domain.subject_performance.models import (
    SchoolSubjectPerformanceLatest,
    SchoolSubjectSummary,
)

ANALYST_DISCLAIMER = (
    "This analyst view is AI-generated from public government data. "
    "It highlights patterns in the published evidence, but it is not official advice or a recommendation."
)
STUDY_16_18_DESTINATIONS_ENABLED = False
STUDY_16_18_SUBJECT_PERFORMANCE_ENABLED = False


class GetSchoolProfileUseCase:
    def __init__(
        self,
        school_profile_repository: SchoolProfileRepository,
        refresh_school_profile_repository: SchoolProfileRepository | None = None,
        postcode_context_resolver: PostcodeContextResolver | None = None,
        school_trends_repository: SchoolTrendsRepository | None = None,
        subject_performance_repository: SubjectPerformanceRepository | None = None,
        summary_repository: SummaryRepository | None = None,
        evaluate_access_use_case: EvaluateAccessUseCase | None = None,
        saved_school_state_resolver: SavedSchoolStateResolver | None = None,
    ) -> None:
        self._school_profile_repository = school_profile_repository
        self._refresh_school_profile_repository = refresh_school_profile_repository
        self._postcode_context_resolver = postcode_context_resolver
        self._school_trends_repository = school_trends_repository
        self._subject_performance_repository = subject_performance_repository
        self._summary_repository = summary_repository
        self._evaluate_access_use_case = evaluate_access_use_case
        self._saved_school_state_resolver = saved_school_state_resolver

    def execute(
        self,
        *,
        urn: str,
        viewer_user_id: UUID | None = None,
        skip_access_checks: bool = False,
    ) -> SchoolProfileResponseDto:
        normalized_urn = urn.strip()
        profile = self._school_profile_repository.get_school_profile(normalized_urn)
        if profile is None:
            raise SchoolProfileNotFoundError(normalized_urn)
        profile = self._refresh_profile_context_if_needed(
            urn=normalized_urn,
            profile=profile,
        )

        demographics_latest = None
        if profile.demographics_latest is not None:
            demographics_latest = SchoolDemographicsLatestDto(
                academic_year=profile.demographics_latest.academic_year,
                disadvantaged_pct=profile.demographics_latest.disadvantaged_pct,
                fsm_pct=profile.demographics_latest.fsm_pct,
                fsm6_pct=profile.demographics_latest.fsm6_pct,
                sen_pct=profile.demographics_latest.sen_pct,
                ehcp_pct=profile.demographics_latest.ehcp_pct,
                eal_pct=profile.demographics_latest.eal_pct,
                first_language_english_pct=profile.demographics_latest.first_language_english_pct,
                first_language_unclassified_pct=profile.demographics_latest.first_language_unclassified_pct,
                male_pct=profile.demographics_latest.male_pct,
                female_pct=profile.demographics_latest.female_pct,
                pupil_mobility_pct=profile.demographics_latest.pupil_mobility_pct,
                coverage=SchoolDemographicsCoverageDto(
                    fsm_supported=profile.demographics_latest.coverage.fsm_supported,
                    fsm6_supported=profile.demographics_latest.coverage.fsm6_supported,
                    gender_supported=profile.demographics_latest.coverage.gender_supported,
                    mobility_supported=profile.demographics_latest.coverage.mobility_supported,
                    send_primary_need_supported=(
                        profile.demographics_latest.coverage.send_primary_need_supported
                    ),
                    ethnicity_supported=profile.demographics_latest.coverage.ethnicity_supported,
                    top_languages_supported=profile.demographics_latest.coverage.top_languages_supported,
                ),
                ethnicity_breakdown=tuple(
                    SchoolDemographicsEthnicityGroupDto(
                        key=group.key,
                        label=group.label,
                        percentage=group.percentage,
                        count=group.count,
                    )
                    for group in profile.demographics_latest.ethnicity_breakdown
                ),
                send_primary_needs=tuple(
                    SchoolDemographicsSendPrimaryNeedDto(
                        key=need.key,
                        label=need.label,
                        percentage=need.percentage,
                        count=need.count,
                    )
                    for need in profile.demographics_latest.send_primary_needs
                ),
                top_home_languages=tuple(
                    SchoolDemographicsHomeLanguageDto(
                        key=language.key,
                        label=language.label,
                        rank=language.rank,
                        percentage=language.percentage,
                        count=language.count,
                    )
                    for language in profile.demographics_latest.top_home_languages
                ),
            )

        attendance_latest = None
        if profile.attendance_latest is not None:
            attendance_latest = SchoolAttendanceLatestDto(
                academic_year=profile.attendance_latest.academic_year,
                overall_attendance_pct=profile.attendance_latest.overall_attendance_pct,
                overall_absence_pct=profile.attendance_latest.overall_absence_pct,
                persistent_absence_pct=profile.attendance_latest.persistent_absence_pct,
            )

        behaviour_latest = None
        if profile.behaviour_latest is not None:
            behaviour_latest = SchoolBehaviourLatestDto(
                academic_year=profile.behaviour_latest.academic_year,
                suspensions_count=profile.behaviour_latest.suspensions_count,
                suspensions_rate=profile.behaviour_latest.suspensions_rate,
                permanent_exclusions_count=profile.behaviour_latest.permanent_exclusions_count,
                permanent_exclusions_rate=profile.behaviour_latest.permanent_exclusions_rate,
            )

        workforce_latest = None
        if profile.workforce_latest is not None:
            workforce_latest = SchoolWorkforceLatestDto(
                academic_year=profile.workforce_latest.academic_year,
                pupil_teacher_ratio=profile.workforce_latest.pupil_teacher_ratio,
                supply_staff_pct=profile.workforce_latest.supply_staff_pct,
                teachers_3plus_years_pct=profile.workforce_latest.teachers_3plus_years_pct,
                teacher_turnover_pct=profile.workforce_latest.teacher_turnover_pct,
                qts_pct=profile.workforce_latest.qts_pct,
                qualifications_level6_plus_pct=(
                    profile.workforce_latest.qualifications_level6_plus_pct
                ),
                teacher_headcount_total=profile.workforce_latest.teacher_headcount_total,
                teacher_fte_total=profile.workforce_latest.teacher_fte_total,
                support_staff_headcount_total=profile.workforce_latest.support_staff_headcount_total,
                support_staff_fte_total=profile.workforce_latest.support_staff_fte_total,
                leadership_headcount=profile.workforce_latest.leadership_headcount,
                teacher_average_mean_salary_gbp=(
                    profile.workforce_latest.teacher_average_mean_salary_gbp
                ),
                teacher_absence_pct=profile.workforce_latest.teacher_absence_pct,
                teacher_vacancy_rate=profile.workforce_latest.teacher_vacancy_rate,
                third_party_support_staff_headcount=(
                    profile.workforce_latest.third_party_support_staff_headcount
                ),
                teacher_sex_breakdown=tuple(
                    SchoolWorkforceBreakdownItemDto(
                        key=item.key,
                        label=item.label,
                        headcount=item.headcount,
                        fte=item.fte,
                        headcount_pct=item.headcount_pct,
                        fte_pct=item.fte_pct,
                    )
                    for item in profile.workforce_latest.teacher_sex_breakdown
                ),
                teacher_age_breakdown=tuple(
                    SchoolWorkforceBreakdownItemDto(
                        key=item.key,
                        label=item.label,
                        headcount=item.headcount,
                        fte=item.fte,
                        headcount_pct=item.headcount_pct,
                        fte_pct=item.fte_pct,
                    )
                    for item in profile.workforce_latest.teacher_age_breakdown
                ),
                teacher_ethnicity_breakdown=tuple(
                    SchoolWorkforceBreakdownItemDto(
                        key=item.key,
                        label=item.label,
                        headcount=item.headcount,
                        fte=item.fte,
                        headcount_pct=item.headcount_pct,
                        fte_pct=item.fte_pct,
                    )
                    for item in profile.workforce_latest.teacher_ethnicity_breakdown
                ),
                teacher_qualification_breakdown=tuple(
                    SchoolWorkforceBreakdownItemDto(
                        key=item.key,
                        label=item.label,
                        headcount=item.headcount,
                        fte=item.fte,
                        headcount_pct=item.headcount_pct,
                        fte_pct=item.fte_pct,
                    )
                    for item in profile.workforce_latest.teacher_qualification_breakdown
                ),
                support_staff_post_mix=tuple(
                    SchoolWorkforceBreakdownItemDto(
                        key=item.key,
                        label=item.label,
                        headcount=item.headcount,
                        fte=item.fte,
                        headcount_pct=item.headcount_pct,
                        fte_pct=item.fte_pct,
                    )
                    for item in profile.workforce_latest.support_staff_post_mix
                ),
            )

        finance_latest = None
        if profile.finance_latest is not None:
            finance_latest = SchoolFinanceLatestDto(
                academic_year=profile.finance_latest.academic_year,
                total_income_gbp=profile.finance_latest.total_income_gbp,
                total_expenditure_gbp=profile.finance_latest.total_expenditure_gbp,
                income_per_pupil_gbp=profile.finance_latest.income_per_pupil_gbp,
                expenditure_per_pupil_gbp=profile.finance_latest.expenditure_per_pupil_gbp,
                total_staff_costs_gbp=profile.finance_latest.total_staff_costs_gbp,
                staff_costs_pct_of_expenditure=(
                    profile.finance_latest.staff_costs_pct_of_expenditure
                ),
                revenue_reserve_gbp=profile.finance_latest.revenue_reserve_gbp,
                revenue_reserve_per_pupil_gbp=(
                    profile.finance_latest.revenue_reserve_per_pupil_gbp
                ),
                in_year_balance_gbp=profile.finance_latest.in_year_balance_gbp,
                total_grant_funding_gbp=profile.finance_latest.total_grant_funding_gbp,
                total_self_generated_funding_gbp=(
                    profile.finance_latest.total_self_generated_funding_gbp
                ),
                teaching_staff_costs_gbp=profile.finance_latest.teaching_staff_costs_gbp,
                supply_teaching_staff_costs_gbp=(
                    profile.finance_latest.supply_teaching_staff_costs_gbp
                ),
                education_support_staff_costs_gbp=(
                    profile.finance_latest.education_support_staff_costs_gbp
                ),
                other_staff_costs_gbp=profile.finance_latest.other_staff_costs_gbp,
                premises_costs_gbp=profile.finance_latest.premises_costs_gbp,
                educational_supplies_costs_gbp=(
                    profile.finance_latest.educational_supplies_costs_gbp
                ),
                bought_in_professional_services_costs_gbp=(
                    profile.finance_latest.bought_in_professional_services_costs_gbp
                ),
                catering_costs_gbp=profile.finance_latest.catering_costs_gbp,
                supply_staff_costs_pct_of_staff_costs=(
                    profile.finance_latest.supply_staff_costs_pct_of_staff_costs
                ),
            )

        admissions_latest = None
        if profile.admissions_latest is not None:
            admissions_latest = SchoolAdmissionsLatestDto(
                academic_year=profile.admissions_latest.academic_year,
                places_offered_total=profile.admissions_latest.places_offered_total,
                applications_any_preference=profile.admissions_latest.applications_any_preference,
                applications_first_preference=(
                    profile.admissions_latest.applications_first_preference
                ),
                oversubscription_ratio=profile.admissions_latest.oversubscription_ratio,
                first_preference_offer_rate=profile.admissions_latest.first_preference_offer_rate,
                any_preference_offer_rate=profile.admissions_latest.any_preference_offer_rate,
                admissions_policy=profile.admissions_latest.admissions_policy,
            )

        destinations_latest = None
        if profile.destinations_latest is not None:
            destinations_latest = SchoolDestinationsLatestDto(
                ks4=_to_destination_stage_latest_dto(profile.destinations_latest.ks4),
                study_16_18=(
                    _to_destination_stage_latest_dto(profile.destinations_latest.study_16_18)
                    if STUDY_16_18_DESTINATIONS_ENABLED
                    else None
                ),
            )

        leadership_snapshot = None
        if profile.leadership_snapshot is not None:
            leadership_snapshot = SchoolLeadershipSnapshotDto(
                headteacher_name=profile.leadership_snapshot.headteacher_name,
                headteacher_start_date=profile.leadership_snapshot.headteacher_start_date,
                headteacher_tenure_years=profile.leadership_snapshot.headteacher_tenure_years,
                leadership_turnover_score=profile.leadership_snapshot.leadership_turnover_score,
            )

        ofsted_latest = None
        if profile.ofsted_latest is not None:
            ofsted_latest = SchoolOfstedLatestDto(
                overall_effectiveness_code=profile.ofsted_latest.overall_effectiveness_code,
                overall_effectiveness_label=profile.ofsted_latest.overall_effectiveness_label,
                inspection_start_date=profile.ofsted_latest.inspection_start_date,
                publication_date=profile.ofsted_latest.publication_date,
                latest_oeif_inspection_start_date=profile.ofsted_latest.latest_oeif_inspection_start_date,
                latest_oeif_publication_date=profile.ofsted_latest.latest_oeif_publication_date,
                quality_of_education_code=profile.ofsted_latest.quality_of_education_code,
                quality_of_education_label=profile.ofsted_latest.quality_of_education_label,
                behaviour_and_attitudes_code=profile.ofsted_latest.behaviour_and_attitudes_code,
                behaviour_and_attitudes_label=profile.ofsted_latest.behaviour_and_attitudes_label,
                personal_development_code=profile.ofsted_latest.personal_development_code,
                personal_development_label=profile.ofsted_latest.personal_development_label,
                leadership_and_management_code=profile.ofsted_latest.leadership_and_management_code,
                leadership_and_management_label=profile.ofsted_latest.leadership_and_management_label,
                latest_ungraded_inspection_date=profile.ofsted_latest.latest_ungraded_inspection_date,
                latest_ungraded_publication_date=profile.ofsted_latest.latest_ungraded_publication_date,
                most_recent_inspection_date=profile.ofsted_latest.most_recent_inspection_date,
                days_since_most_recent_inspection=profile.ofsted_latest.days_since_most_recent_inspection,
                is_graded=profile.ofsted_latest.is_graded,
                ungraded_outcome=profile.ofsted_latest.ungraded_outcome,
                provider_page_url=profile.ofsted_latest.provider_page_url,
            )

        ofsted_timeline = None
        if profile.ofsted_timeline is not None:
            ofsted_timeline = SchoolOfstedTimelineDto(
                events=tuple(
                    SchoolOfstedTimelineEventDto(
                        inspection_number=event.inspection_number,
                        inspection_start_date=event.inspection_start_date,
                        publication_date=event.publication_date,
                        inspection_type=event.inspection_type,
                        overall_effectiveness_label=event.overall_effectiveness_label,
                        headline_outcome_text=event.headline_outcome_text,
                        category_of_concern=event.category_of_concern,
                    )
                    for event in profile.ofsted_timeline.events
                ),
                coverage=SchoolOfstedTimelineCoverageDto(
                    is_partial_history=profile.ofsted_timeline.coverage.is_partial_history,
                    earliest_event_date=profile.ofsted_timeline.coverage.earliest_event_date,
                    latest_event_date=profile.ofsted_timeline.coverage.latest_event_date,
                    events_count=profile.ofsted_timeline.coverage.events_count,
                ),
            )

        performance = None
        if profile.performance is not None:
            performance = SchoolPerformanceDto(
                latest=(
                    SchoolPerformanceYearDto(
                        academic_year=profile.performance.latest.academic_year,
                        attainment8_average=profile.performance.latest.attainment8_average,
                        progress8_average=profile.performance.latest.progress8_average,
                        progress8_disadvantaged=profile.performance.latest.progress8_disadvantaged,
                        progress8_not_disadvantaged=profile.performance.latest.progress8_not_disadvantaged,
                        progress8_disadvantaged_gap=profile.performance.latest.progress8_disadvantaged_gap,
                        engmath_5_plus_pct=profile.performance.latest.engmath_5_plus_pct,
                        engmath_4_plus_pct=profile.performance.latest.engmath_4_plus_pct,
                        ebacc_entry_pct=profile.performance.latest.ebacc_entry_pct,
                        ebacc_5_plus_pct=profile.performance.latest.ebacc_5_plus_pct,
                        ebacc_4_plus_pct=profile.performance.latest.ebacc_4_plus_pct,
                        ks2_reading_expected_pct=profile.performance.latest.ks2_reading_expected_pct,
                        ks2_writing_expected_pct=profile.performance.latest.ks2_writing_expected_pct,
                        ks2_maths_expected_pct=profile.performance.latest.ks2_maths_expected_pct,
                        ks2_combined_expected_pct=profile.performance.latest.ks2_combined_expected_pct,
                        ks2_reading_higher_pct=profile.performance.latest.ks2_reading_higher_pct,
                        ks2_writing_higher_pct=profile.performance.latest.ks2_writing_higher_pct,
                        ks2_maths_higher_pct=profile.performance.latest.ks2_maths_higher_pct,
                        ks2_combined_higher_pct=profile.performance.latest.ks2_combined_higher_pct,
                    )
                    if profile.performance.latest is not None
                    else None
                ),
                history=tuple(
                    SchoolPerformanceYearDto(
                        academic_year=year.academic_year,
                        attainment8_average=year.attainment8_average,
                        progress8_average=year.progress8_average,
                        progress8_disadvantaged=year.progress8_disadvantaged,
                        progress8_not_disadvantaged=year.progress8_not_disadvantaged,
                        progress8_disadvantaged_gap=year.progress8_disadvantaged_gap,
                        engmath_5_plus_pct=year.engmath_5_plus_pct,
                        engmath_4_plus_pct=year.engmath_4_plus_pct,
                        ebacc_entry_pct=year.ebacc_entry_pct,
                        ebacc_5_plus_pct=year.ebacc_5_plus_pct,
                        ebacc_4_plus_pct=year.ebacc_4_plus_pct,
                        ks2_reading_expected_pct=year.ks2_reading_expected_pct,
                        ks2_writing_expected_pct=year.ks2_writing_expected_pct,
                        ks2_maths_expected_pct=year.ks2_maths_expected_pct,
                        ks2_combined_expected_pct=year.ks2_combined_expected_pct,
                        ks2_reading_higher_pct=year.ks2_reading_higher_pct,
                        ks2_writing_higher_pct=year.ks2_writing_higher_pct,
                        ks2_maths_higher_pct=year.ks2_maths_higher_pct,
                        ks2_combined_higher_pct=year.ks2_combined_higher_pct,
                    )
                    for year in profile.performance.history
                ),
            )

        area_context = None
        if profile.area_context is not None:
            deprivation = None
            if profile.area_context.deprivation is not None:
                deprivation = SchoolAreaDeprivationDto(
                    lsoa_code=profile.area_context.deprivation.lsoa_code,
                    imd_score=profile.area_context.deprivation.imd_score,
                    imd_rank=profile.area_context.deprivation.imd_rank,
                    imd_decile=profile.area_context.deprivation.imd_decile,
                    idaci_score=profile.area_context.deprivation.idaci_score,
                    idaci_decile=profile.area_context.deprivation.idaci_decile,
                    income_score=profile.area_context.deprivation.income_score,
                    income_rank=profile.area_context.deprivation.income_rank,
                    income_decile=profile.area_context.deprivation.income_decile,
                    employment_score=profile.area_context.deprivation.employment_score,
                    employment_rank=profile.area_context.deprivation.employment_rank,
                    employment_decile=profile.area_context.deprivation.employment_decile,
                    education_score=profile.area_context.deprivation.education_score,
                    education_rank=profile.area_context.deprivation.education_rank,
                    education_decile=profile.area_context.deprivation.education_decile,
                    health_score=profile.area_context.deprivation.health_score,
                    health_rank=profile.area_context.deprivation.health_rank,
                    health_decile=profile.area_context.deprivation.health_decile,
                    crime_score=profile.area_context.deprivation.crime_score,
                    crime_rank=profile.area_context.deprivation.crime_rank,
                    crime_decile=profile.area_context.deprivation.crime_decile,
                    barriers_score=profile.area_context.deprivation.barriers_score,
                    barriers_rank=profile.area_context.deprivation.barriers_rank,
                    barriers_decile=profile.area_context.deprivation.barriers_decile,
                    living_environment_score=(
                        profile.area_context.deprivation.living_environment_score
                    ),
                    living_environment_rank=(
                        profile.area_context.deprivation.living_environment_rank
                    ),
                    living_environment_decile=(
                        profile.area_context.deprivation.living_environment_decile
                    ),
                    population_total=profile.area_context.deprivation.population_total,
                    local_authority_district_code=(
                        profile.area_context.deprivation.local_authority_district_code
                    ),
                    local_authority_district_name=(
                        profile.area_context.deprivation.local_authority_district_name
                    ),
                    source_release=profile.area_context.deprivation.source_release,
                )

            crime = None
            if profile.area_context.crime is not None:
                crime = SchoolAreaCrimeDto(
                    radius_miles=profile.area_context.crime.radius_miles,
                    latest_month=profile.area_context.crime.latest_month,
                    total_incidents=profile.area_context.crime.total_incidents,
                    population_denominator=profile.area_context.crime.population_denominator,
                    incidents_per_1000=profile.area_context.crime.incidents_per_1000,
                    annual_incidents_per_1000=tuple(
                        SchoolAreaCrimeAnnualRateDto(
                            year=row.year,
                            total_incidents=row.total_incidents,
                            incidents_per_1000=row.incidents_per_1000,
                        )
                        for row in profile.area_context.crime.annual_incidents_per_1000
                    ),
                    categories=tuple(
                        SchoolAreaCrimeCategoryDto(
                            category=category.category,
                            incident_count=category.incident_count,
                        )
                        for category in profile.area_context.crime.categories
                    ),
                )

            house_prices = None
            if profile.area_context.house_prices is not None:
                house_prices = SchoolAreaHousePricesDto(
                    area_code=profile.area_context.house_prices.area_code,
                    area_name=profile.area_context.house_prices.area_name,
                    latest_month=profile.area_context.house_prices.latest_month,
                    average_price=profile.area_context.house_prices.average_price,
                    annual_change_pct=profile.area_context.house_prices.annual_change_pct,
                    monthly_change_pct=profile.area_context.house_prices.monthly_change_pct,
                    three_year_change_pct=profile.area_context.house_prices.three_year_change_pct,
                    trend=tuple(
                        SchoolAreaHousePricePointDto(
                            month=point.month,
                            average_price=point.average_price,
                            annual_change_pct=point.annual_change_pct,
                            monthly_change_pct=point.monthly_change_pct,
                        )
                        for point in profile.area_context.house_prices.trend
                    ),
                )

            area_context = SchoolAreaContextDto(
                deprivation=deprivation,
                crime=crime,
                house_prices=house_prices,
                coverage=SchoolAreaContextCoverageDto(
                    has_deprivation=profile.area_context.coverage.has_deprivation,
                    has_crime=profile.area_context.coverage.has_crime,
                    crime_months_available=profile.area_context.coverage.crime_months_available,
                    has_house_prices=profile.area_context.coverage.has_house_prices,
                    house_price_months_available=(
                        profile.area_context.coverage.house_price_months_available
                    ),
                ),
            )

        completeness = SchoolProfileCompletenessDto(
            demographics=SchoolProfileSectionCompletenessDto(
                status=profile.completeness.demographics.status,
                reason_code=profile.completeness.demographics.reason_code,
                last_updated_at=profile.completeness.demographics.last_updated_at,
                years_available=profile.completeness.demographics.years_available,
            ),
            attendance=SchoolProfileSectionCompletenessDto(
                status=profile.completeness.attendance.status,
                reason_code=profile.completeness.attendance.reason_code,
                last_updated_at=profile.completeness.attendance.last_updated_at,
                years_available=profile.completeness.attendance.years_available,
            ),
            behaviour=SchoolProfileSectionCompletenessDto(
                status=profile.completeness.behaviour.status,
                reason_code=profile.completeness.behaviour.reason_code,
                last_updated_at=profile.completeness.behaviour.last_updated_at,
                years_available=profile.completeness.behaviour.years_available,
            ),
            workforce=SchoolProfileSectionCompletenessDto(
                status=profile.completeness.workforce.status,
                reason_code=profile.completeness.workforce.reason_code,
                last_updated_at=profile.completeness.workforce.last_updated_at,
                years_available=profile.completeness.workforce.years_available,
            ),
            admissions=SchoolProfileSectionCompletenessDto(
                status=profile.completeness.admissions.status,
                reason_code=profile.completeness.admissions.reason_code,
                last_updated_at=profile.completeness.admissions.last_updated_at,
                years_available=profile.completeness.admissions.years_available,
            ),
            destinations=SchoolProfileSectionCompletenessDto(
                status=profile.completeness.destinations.status,
                reason_code=profile.completeness.destinations.reason_code,
                last_updated_at=profile.completeness.destinations.last_updated_at,
                years_available=profile.completeness.destinations.years_available,
            ),
            finance=SchoolProfileSectionCompletenessDto(
                status=profile.completeness.finance.status,
                reason_code=profile.completeness.finance.reason_code,
                last_updated_at=profile.completeness.finance.last_updated_at,
                years_available=profile.completeness.finance.years_available,
            ),
            leadership=SchoolProfileSectionCompletenessDto(
                status=profile.completeness.leadership.status,
                reason_code=profile.completeness.leadership.reason_code,
                last_updated_at=profile.completeness.leadership.last_updated_at,
                years_available=profile.completeness.leadership.years_available,
            ),
            performance=SchoolProfileSectionCompletenessDto(
                status=profile.completeness.performance.status,
                reason_code=profile.completeness.performance.reason_code,
                last_updated_at=profile.completeness.performance.last_updated_at,
                years_available=profile.completeness.performance.years_available,
            ),
            ofsted_latest=SchoolProfileSectionCompletenessDto(
                status=profile.completeness.ofsted_latest.status,
                reason_code=profile.completeness.ofsted_latest.reason_code,
                last_updated_at=profile.completeness.ofsted_latest.last_updated_at,
                years_available=profile.completeness.ofsted_latest.years_available,
            ),
            ofsted_timeline=SchoolProfileSectionCompletenessDto(
                status=profile.completeness.ofsted_timeline.status,
                reason_code=profile.completeness.ofsted_timeline.reason_code,
                last_updated_at=profile.completeness.ofsted_timeline.last_updated_at,
                years_available=profile.completeness.ofsted_timeline.years_available,
            ),
            area_deprivation=SchoolProfileSectionCompletenessDto(
                status=profile.completeness.area_deprivation.status,
                reason_code=profile.completeness.area_deprivation.reason_code,
                last_updated_at=profile.completeness.area_deprivation.last_updated_at,
                years_available=profile.completeness.area_deprivation.years_available,
            ),
            area_crime=SchoolProfileSectionCompletenessDto(
                status=profile.completeness.area_crime.status,
                reason_code=profile.completeness.area_crime.reason_code,
                last_updated_at=profile.completeness.area_crime.last_updated_at,
                years_available=profile.completeness.area_crime.years_available,
            ),
            area_house_prices=SchoolProfileSectionCompletenessDto(
                status=profile.completeness.area_house_prices.status,
                reason_code=profile.completeness.area_house_prices.reason_code,
                last_updated_at=profile.completeness.area_house_prices.last_updated_at,
                years_available=profile.completeness.area_house_prices.years_available,
            ),
        )
        benchmarks = self._build_profile_benchmarks(normalized_urn)
        overview_summary = None
        analyst_summary = None
        if self._summary_repository is not None:
            overview_summary = self._summary_repository.get_summary(normalized_urn, "overview")
            analyst_summary = self._summary_repository.get_summary(normalized_urn, "analyst")
        access_uc = None if skip_access_checks else self._evaluate_access_use_case
        analyst = _build_analyst_section(
            school_name=profile.school.name,
            analyst_text=analyst_summary.text if analyst_summary is not None else None,
            viewer_user_id=viewer_user_id,
            evaluate_access_use_case=access_uc,
        )
        neighbourhood = _build_neighbourhood_section(
            school_name=profile.school.name,
            area_context=area_context,
            viewer_user_id=viewer_user_id,
            evaluate_access_use_case=access_uc,
        )
        saved_state = _resolve_saved_school_state(
            school_urn=normalized_urn,
            viewer_user_id=viewer_user_id,
            saved_school_state_resolver=self._saved_school_state_resolver,
        )
        subject_performance = None
        if self._subject_performance_repository is not None:
            subject_performance = _to_subject_performance_latest_dto(
                self._subject_performance_repository.get_latest_subject_performance(
                    normalized_urn,
                    include_16_to_18=STUDY_16_18_SUBJECT_PERFORMANCE_ENABLED,
                )
            )

        return SchoolProfileResponseDto(
            school=SchoolProfileSchoolDto(
                urn=profile.school.urn,
                name=profile.school.name,
                phase=profile.school.phase,
                school_type=profile.school.school_type,
                status=profile.school.status,
                postcode=profile.school.postcode,
                website=profile.school.website,
                telephone=profile.school.telephone,
                head_title=profile.school.head_title,
                head_first_name=profile.school.head_first_name,
                head_last_name=profile.school.head_last_name,
                head_job_title=profile.school.head_job_title,
                address_street=profile.school.address_street,
                address_locality=profile.school.address_locality,
                address_line3=profile.school.address_line3,
                address_town=profile.school.address_town,
                address_county=profile.school.address_county,
                statutory_low_age=profile.school.statutory_low_age,
                statutory_high_age=profile.school.statutory_high_age,
                gender=profile.school.gender,
                religious_character=profile.school.religious_character,
                diocese=profile.school.diocese,
                admissions_policy=profile.school.admissions_policy,
                sixth_form=profile.school.sixth_form,
                nursery_provision=profile.school.nursery_provision,
                boarders=profile.school.boarders,
                fsm_pct_gias=profile.school.fsm_pct_gias,
                trust_name=profile.school.trust_name,
                trust_flag=profile.school.trust_flag,
                federation_name=profile.school.federation_name,
                federation_flag=profile.school.federation_flag,
                la_name=profile.school.la_name,
                la_code=profile.school.la_code,
                urban_rural=profile.school.urban_rural,
                number_of_boys=profile.school.number_of_boys,
                number_of_girls=profile.school.number_of_girls,
                lsoa_code=profile.school.lsoa_code,
                lsoa_name=profile.school.lsoa_name,
                last_changed_date=profile.school.last_changed_date,
                lat=profile.school.lat,
                lng=profile.school.lng,
            ),
            overview_text=overview_summary.text if overview_summary is not None else None,
            analyst=analyst,
            demographics_latest=demographics_latest,
            attendance_latest=attendance_latest,
            behaviour_latest=behaviour_latest,
            workforce_latest=workforce_latest,
            admissions_latest=admissions_latest,
            destinations_latest=destinations_latest,
            finance_latest=finance_latest,
            leadership_snapshot=leadership_snapshot,
            performance=performance,
            ofsted_latest=ofsted_latest,
            ofsted_timeline=ofsted_timeline,
            neighbourhood=neighbourhood,
            saved_state=saved_state,
            benchmarks=benchmarks,
            completeness=completeness,
            subject_performance=subject_performance,
        )

    def _build_profile_benchmarks(self, urn: str) -> SchoolProfileBenchmarksDto:
        if self._school_trends_repository is None:
            return SchoolProfileBenchmarksDto(metrics=())

        benchmark_series = self._school_trends_repository.get_metric_benchmark_series(urn)
        if benchmark_series is None:
            return SchoolProfileBenchmarksDto(metrics=())

        latest_by_metric: dict[str, SchoolMetricBenchmarkYearlyRow] = {}
        for row in benchmark_series.rows:
            existing = latest_by_metric.get(row.metric_key)
            if existing is None or existing.academic_year < row.academic_year:
                latest_by_metric[row.metric_key] = row

        metrics = tuple(
            SchoolProfileMetricBenchmarkDto(
                metric_key=row.metric_key,
                academic_year=row.academic_year,
                school_value=row.school_value,
                national_value=row.national_value,
                local_value=row.local_value,
                school_vs_national_delta=_to_optional_delta(
                    school_value=row.school_value,
                    benchmark_value=row.national_value,
                ),
                school_vs_local_delta=_to_optional_delta(
                    school_value=row.school_value,
                    benchmark_value=row.local_value,
                ),
                local_scope=row.local_scope,
                local_area_code=row.local_area_code,
                local_area_label=row.local_area_label,
                contexts=tuple(
                    SchoolBenchmarkContextDto(
                        scope=context.scope,
                        label=context.label,
                        value=context.value,
                        percentile_rank=context.percentile_rank,
                        school_count=context.school_count,
                        area_code=context.area_code,
                    )
                    for context in row.contexts
                ),
            )
            for row in sorted(
                latest_by_metric.values(),
                key=lambda item: item.metric_key,
            )
        )
        return SchoolProfileBenchmarksDto(metrics=metrics)

    def _refresh_profile_context_if_needed(
        self,
        *,
        urn: str,
        profile: SchoolProfile,
    ) -> SchoolProfile:
        if self._postcode_context_resolver is None:
            return profile

        postcode = profile.school.postcode
        if postcode is None or not postcode.strip():
            return profile

        area_context = profile.area_context
        has_deprivation = area_context is not None and area_context.coverage.has_deprivation
        if has_deprivation:
            return profile

        try:
            self._postcode_context_resolver.resolve(postcode)
        except Exception:
            return profile

        refresh_repository = (
            self._refresh_school_profile_repository or self._school_profile_repository
        )
        refreshed_profile = refresh_repository.get_school_profile(urn)
        if refreshed_profile is None:
            return profile
        return refreshed_profile


def _to_optional_delta(
    *,
    school_value: float | int | None,
    benchmark_value: float | None,
) -> float | None:
    if school_value is None or benchmark_value is None:
        return None
    return float(school_value) - float(benchmark_value)


def _to_destination_stage_latest_dto(
    stage: SchoolDestinationStageLatest | None,
) -> SchoolDestinationStageLatestDto | None:
    if stage is None:
        return None
    return SchoolDestinationStageLatestDto(
        academic_year=stage.academic_year,
        cohort_count=stage.cohort_count,
        qualification_group=stage.qualification_group,
        qualification_level=stage.qualification_level,
        overall_pct=stage.overall_pct,
        education_pct=stage.education_pct,
        apprenticeship_pct=stage.apprenticeship_pct,
        employment_pct=stage.employment_pct,
        not_sustained_pct=stage.not_sustained_pct,
        activity_unknown_pct=stage.activity_unknown_pct,
        fe_pct=stage.fe_pct,
        other_education_pct=stage.other_education_pct,
        school_sixth_form_pct=stage.school_sixth_form_pct,
        sixth_form_college_pct=stage.sixth_form_college_pct,
        higher_education_pct=stage.higher_education_pct,
    )


def _to_subject_performance_latest_dto(
    value: SchoolSubjectPerformanceLatest | None,
) -> SchoolSubjectPerformanceLatestDto | None:
    if value is None:
        return None
    return SchoolSubjectPerformanceLatestDto(
        strongest_subjects=tuple(
            _to_subject_summary_dto(item) for item in value.strongest_subjects
        ),
        weakest_subjects=tuple(_to_subject_summary_dto(item) for item in value.weakest_subjects),
        stage_breakdowns=tuple(
            SchoolSubjectPerformanceGroupRowDto(
                academic_year=row.academic_year,
                key_stage=row.key_stage,
                qualification_family=row.qualification_family,
                exam_cohort=row.exam_cohort,
                subjects=tuple(_to_subject_summary_dto(item) for item in row.subjects),
            )
            for row in value.stage_breakdowns
        ),
        latest_updated_at=value.latest_updated_at,
    )


def _to_subject_summary_dto(value: SchoolSubjectSummary) -> SchoolSubjectSummaryDto:
    return SchoolSubjectSummaryDto(
        academic_year=value.academic_year,
        key_stage=value.key_stage,
        qualification_family=value.qualification_family,
        exam_cohort=value.exam_cohort,
        subject=value.subject,
        source_version=value.source_version,
        entries_count_total=value.entries_count_total,
        high_grade_count=value.high_grade_count,
        high_grade_share_pct=value.high_grade_share_pct,
        pass_grade_count=value.pass_grade_count,
        pass_grade_share_pct=value.pass_grade_share_pct,
        ranking_eligible=value.ranking_eligible,
    )


def _build_analyst_section(
    *,
    school_name: str,
    analyst_text: str | None,
    viewer_user_id: UUID | None,
    evaluate_access_use_case: EvaluateAccessUseCase | None,
) -> SchoolProfileAnalystSectionDto:
    normalized_text = _normalize_text(analyst_text)
    if normalized_text is None:
        return SchoolProfileAnalystSectionDto(
            access=_unavailable_section_access(
                requirement_key=SCHOOL_PROFILE_AI_ANALYST_REQUIREMENT,
                reason_code="artefact_not_published",
            ),
        )

    access = _resolve_section_access(
        requirement_key=SCHOOL_PROFILE_AI_ANALYST_REQUIREMENT,
        viewer_user_id=viewer_user_id,
        evaluate_access_use_case=evaluate_access_use_case,
        school_name=school_name,
    )
    if access.state == "available":
        return SchoolProfileAnalystSectionDto(
            access=access,
            text=normalized_text,
            disclaimer=ANALYST_DISCLAIMER,
        )

    return SchoolProfileAnalystSectionDto(
        access=access,
        teaser_text=_build_analyst_teaser_text(normalized_text),
        disclaimer=ANALYST_DISCLAIMER,
    )


def _build_neighbourhood_section(
    *,
    school_name: str,
    area_context: SchoolAreaContextDto | None,
    viewer_user_id: UUID | None,
    evaluate_access_use_case: EvaluateAccessUseCase | None,
) -> SchoolProfileNeighbourhoodSectionDto:
    if not _has_neighbourhood_content(area_context):
        return SchoolProfileNeighbourhoodSectionDto(
            access=_unavailable_section_access(
                requirement_key=SCHOOL_PROFILE_NEIGHBOURHOOD_REQUIREMENT,
                reason_code="artefact_not_published",
            ),
        )

    access = _resolve_section_access(
        requirement_key=SCHOOL_PROFILE_NEIGHBOURHOOD_REQUIREMENT,
        viewer_user_id=viewer_user_id,
        evaluate_access_use_case=evaluate_access_use_case,
        school_name=school_name,
    )
    if access.state == "available":
        return SchoolProfileNeighbourhoodSectionDto(
            access=access,
            area_context=area_context,
        )

    return SchoolProfileNeighbourhoodSectionDto(
        access=access,
        teaser_text=_build_neighbourhood_teaser_text(
            school_name=school_name,
            area_context=area_context,
        ),
    )


def _resolve_section_access(
    *,
    requirement_key: str,
    viewer_user_id: UUID | None,
    evaluate_access_use_case: EvaluateAccessUseCase | None,
    school_name: str,
) -> SectionAccessDto:
    requirement = get_access_requirement(requirement_key)
    if evaluate_access_use_case is None:
        return SectionAccessDto(
            state="available",
            capability_key=requirement.capability_key,
            reason_code=None,
            product_codes=(),
            requires_auth=False,
            requires_purchase=False,
        )

    decision = evaluate_access_use_case.execute(
        requirement_key=requirement_key,
        user_id=viewer_user_id,
    )
    return SectionAccessDto(
        state=decision.section_state,
        capability_key=decision.capability_key,
        reason_code=decision.reason_code,
        product_codes=decision.available_product_codes,
        requires_auth=decision.requires_auth,
        requires_purchase=decision.requires_purchase,
        school_name=school_name if decision.section_state == "locked" else None,
    )


def _unavailable_section_access(
    *,
    requirement_key: str,
    reason_code: AccessDecisionReasonCode,
) -> SectionAccessDto:
    requirement = get_access_requirement(requirement_key)
    return SectionAccessDto(
        state="unavailable",
        capability_key=requirement.capability_key,
        reason_code=reason_code,
        product_codes=(),
        requires_auth=False,
        requires_purchase=False,
    )


def _has_neighbourhood_content(area_context: SchoolAreaContextDto | None) -> bool:
    if area_context is None:
        return False
    return (
        area_context.deprivation is not None
        or area_context.crime is not None
        or area_context.house_prices is not None
    )


def _build_neighbourhood_teaser_text(
    *,
    school_name: str,
    area_context: SchoolAreaContextDto | None,
) -> str:
    segments: list[str] = []
    if area_context is not None:
        if area_context.deprivation is not None:
            segments.append("deprivation context")
        if area_context.crime is not None:
            segments.append("local crime context")
        if area_context.house_prices is not None:
            segments.append("house-price context")

    if not segments:
        return f"Premium neighbourhood context is available for {school_name}."
    return (
        f"Premium neighbourhood context is available for {school_name}, including "
        f"{_join_with_commas(segments)}."
    )


def _build_analyst_teaser_text(text: str) -> str:
    sentences = [item.strip() for item in re.split(r"(?<=[.!?])\s+", text) if item.strip()]
    if not sentences:
        return text
    if len(sentences) == 1:
        return _truncate_text(sentences[0], limit=240)

    teaser = " ".join(sentences[:2])
    if len(teaser) < 220 and len(sentences) > 2:
        teaser = " ".join(sentences[:3])
    return teaser


def _join_with_commas(parts: list[str]) -> str:
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return f"{parts[0]} and {parts[1]}"
    return f"{', '.join(parts[:-1])}, and {parts[-1]}"


def _normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _truncate_text(value: str, *, limit: int) -> str:
    if len(value) <= limit:
        return value
    return f"{value[: limit - 3].rstrip()}..."


def _resolve_saved_school_state(
    *,
    school_urn: str,
    viewer_user_id: UUID | None,
    saved_school_state_resolver: SavedSchoolStateResolver | None,
) -> SavedSchoolStateDto:
    if saved_school_state_resolver is None:
        if viewer_user_id is None:
            return anonymous_saved_school_state()
        return SavedSchoolStateDto(
            status="not_saved",
            saved_at=None,
            capability_key=None,
            reason_code=None,
        )

    return saved_school_state_resolver.execute(
        user_id=viewer_user_id,
        school_urns=(school_urn,),
    ).get(school_urn, anonymous_saved_school_state())
