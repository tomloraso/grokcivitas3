from __future__ import annotations

from civitas.api.schemas.access import SectionAccessResponse
from civitas.api.schemas.school_profiles import (
    SchoolProfileAnalystSectionResponse,
    SchoolProfileAreaContextCoverageResponse,
    SchoolProfileAreaContextResponse,
    SchoolProfileAreaCrimeAnnualRateResponse,
    SchoolProfileAreaCrimeCategoryResponse,
    SchoolProfileAreaCrimeResponse,
    SchoolProfileAreaDeprivationResponse,
    SchoolProfileAreaHousePricePointResponse,
    SchoolProfileAreaHousePricesResponse,
    SchoolProfileAttendanceLatestResponse,
    SchoolProfileBehaviourLatestResponse,
    SchoolProfileBenchmarksResponse,
    SchoolProfileCompletenessResponse,
    SchoolProfileDemographicsCoverageResponse,
    SchoolProfileDemographicsEthnicityGroupResponse,
    SchoolProfileDemographicsHomeLanguageResponse,
    SchoolProfileDemographicsLatestResponse,
    SchoolProfileDemographicsSendPrimaryNeedResponse,
    SchoolProfileLeadershipSnapshotResponse,
    SchoolProfileMetricBenchmarkResponse,
    SchoolProfileNeighbourhoodSectionResponse,
    SchoolProfileOfstedLatestResponse,
    SchoolProfileOfstedTimelineCoverageResponse,
    SchoolProfileOfstedTimelineEventResponse,
    SchoolProfileOfstedTimelineResponse,
    SchoolProfilePerformanceResponse,
    SchoolProfilePerformanceYearResponse,
    SchoolProfileResponse,
    SchoolProfileSchoolResponse,
    SchoolProfileSectionCompletenessResponse,
    SchoolProfileWorkforceLatestResponse,
)
from civitas.application.access.dto import SectionAccessDto
from civitas.application.school_profiles.dto import (
    SchoolAreaContextDto,
    SchoolProfileResponseDto,
    SchoolProfileSectionCompletenessDto,
)


def to_school_profile_response(result: SchoolProfileResponseDto) -> SchoolProfileResponse:
    demographics_latest = None
    if result.demographics_latest is not None:
        demographics_latest = SchoolProfileDemographicsLatestResponse(
            academic_year=result.demographics_latest.academic_year,
            disadvantaged_pct=result.demographics_latest.disadvantaged_pct,
            fsm_pct=result.demographics_latest.fsm_pct,
            fsm6_pct=result.demographics_latest.fsm6_pct,
            sen_pct=result.demographics_latest.sen_pct,
            ehcp_pct=result.demographics_latest.ehcp_pct,
            eal_pct=result.demographics_latest.eal_pct,
            first_language_english_pct=result.demographics_latest.first_language_english_pct,
            first_language_unclassified_pct=result.demographics_latest.first_language_unclassified_pct,
            male_pct=result.demographics_latest.male_pct,
            female_pct=result.demographics_latest.female_pct,
            pupil_mobility_pct=result.demographics_latest.pupil_mobility_pct,
            coverage=SchoolProfileDemographicsCoverageResponse(
                fsm_supported=result.demographics_latest.coverage.fsm_supported,
                fsm6_supported=result.demographics_latest.coverage.fsm6_supported,
                gender_supported=result.demographics_latest.coverage.gender_supported,
                mobility_supported=result.demographics_latest.coverage.mobility_supported,
                send_primary_need_supported=(
                    result.demographics_latest.coverage.send_primary_need_supported
                ),
                ethnicity_supported=result.demographics_latest.coverage.ethnicity_supported,
                top_languages_supported=result.demographics_latest.coverage.top_languages_supported,
            ),
            ethnicity_breakdown=[
                SchoolProfileDemographicsEthnicityGroupResponse(
                    key=group.key,
                    label=group.label,
                    percentage=group.percentage,
                    count=group.count,
                )
                for group in result.demographics_latest.ethnicity_breakdown
            ],
            send_primary_needs=[
                SchoolProfileDemographicsSendPrimaryNeedResponse(
                    key=need.key,
                    label=need.label,
                    percentage=need.percentage,
                    count=need.count,
                )
                for need in result.demographics_latest.send_primary_needs
            ],
            top_home_languages=[
                SchoolProfileDemographicsHomeLanguageResponse(
                    key=language.key,
                    label=language.label,
                    rank=language.rank,
                    percentage=language.percentage,
                    count=language.count,
                )
                for language in result.demographics_latest.top_home_languages
            ],
        )

    attendance_latest = None
    if result.attendance_latest is not None:
        attendance_latest = SchoolProfileAttendanceLatestResponse(
            academic_year=result.attendance_latest.academic_year,
            overall_attendance_pct=result.attendance_latest.overall_attendance_pct,
            overall_absence_pct=result.attendance_latest.overall_absence_pct,
            persistent_absence_pct=result.attendance_latest.persistent_absence_pct,
        )

    behaviour_latest = None
    if result.behaviour_latest is not None:
        behaviour_latest = SchoolProfileBehaviourLatestResponse(
            academic_year=result.behaviour_latest.academic_year,
            suspensions_count=result.behaviour_latest.suspensions_count,
            suspensions_rate=result.behaviour_latest.suspensions_rate,
            permanent_exclusions_count=result.behaviour_latest.permanent_exclusions_count,
            permanent_exclusions_rate=result.behaviour_latest.permanent_exclusions_rate,
        )

    workforce_latest = None
    if result.workforce_latest is not None:
        workforce_latest = SchoolProfileWorkforceLatestResponse(
            academic_year=result.workforce_latest.academic_year,
            pupil_teacher_ratio=result.workforce_latest.pupil_teacher_ratio,
            supply_staff_pct=result.workforce_latest.supply_staff_pct,
            teachers_3plus_years_pct=result.workforce_latest.teachers_3plus_years_pct,
            teacher_turnover_pct=result.workforce_latest.teacher_turnover_pct,
            qts_pct=result.workforce_latest.qts_pct,
            qualifications_level6_plus_pct=result.workforce_latest.qualifications_level6_plus_pct,
        )

    leadership_snapshot = None
    if result.leadership_snapshot is not None:
        leadership_snapshot = SchoolProfileLeadershipSnapshotResponse(
            headteacher_name=result.leadership_snapshot.headteacher_name,
            headteacher_start_date=result.leadership_snapshot.headteacher_start_date,
            headteacher_tenure_years=result.leadership_snapshot.headteacher_tenure_years,
            leadership_turnover_score=result.leadership_snapshot.leadership_turnover_score,
        )

    ofsted_latest = None
    if result.ofsted_latest is not None:
        ofsted_latest = SchoolProfileOfstedLatestResponse(
            overall_effectiveness_code=result.ofsted_latest.overall_effectiveness_code,
            overall_effectiveness_label=result.ofsted_latest.overall_effectiveness_label,
            inspection_start_date=result.ofsted_latest.inspection_start_date,
            publication_date=result.ofsted_latest.publication_date,
            latest_oeif_inspection_start_date=result.ofsted_latest.latest_oeif_inspection_start_date,
            latest_oeif_publication_date=result.ofsted_latest.latest_oeif_publication_date,
            quality_of_education_code=result.ofsted_latest.quality_of_education_code,
            quality_of_education_label=result.ofsted_latest.quality_of_education_label,
            behaviour_and_attitudes_code=result.ofsted_latest.behaviour_and_attitudes_code,
            behaviour_and_attitudes_label=result.ofsted_latest.behaviour_and_attitudes_label,
            personal_development_code=result.ofsted_latest.personal_development_code,
            personal_development_label=result.ofsted_latest.personal_development_label,
            leadership_and_management_code=result.ofsted_latest.leadership_and_management_code,
            leadership_and_management_label=result.ofsted_latest.leadership_and_management_label,
            latest_ungraded_inspection_date=result.ofsted_latest.latest_ungraded_inspection_date,
            latest_ungraded_publication_date=result.ofsted_latest.latest_ungraded_publication_date,
            most_recent_inspection_date=result.ofsted_latest.most_recent_inspection_date,
            days_since_most_recent_inspection=result.ofsted_latest.days_since_most_recent_inspection,
            is_graded=result.ofsted_latest.is_graded,
            ungraded_outcome=result.ofsted_latest.ungraded_outcome,
            provider_page_url=result.ofsted_latest.provider_page_url,
        )

    ofsted_timeline = SchoolProfileOfstedTimelineResponse(
        events=[
            SchoolProfileOfstedTimelineEventResponse(
                inspection_number=event.inspection_number,
                inspection_start_date=event.inspection_start_date,
                publication_date=event.publication_date,
                inspection_type=event.inspection_type,
                overall_effectiveness_label=event.overall_effectiveness_label,
                headline_outcome_text=event.headline_outcome_text,
                category_of_concern=event.category_of_concern,
            )
            for event in result.ofsted_timeline.events
        ]
        if result.ofsted_timeline is not None
        else [],
        coverage=SchoolProfileOfstedTimelineCoverageResponse(
            is_partial_history=result.ofsted_timeline.coverage.is_partial_history,
            earliest_event_date=result.ofsted_timeline.coverage.earliest_event_date,
            latest_event_date=result.ofsted_timeline.coverage.latest_event_date,
            events_count=result.ofsted_timeline.coverage.events_count,
        )
        if result.ofsted_timeline is not None
        else SchoolProfileOfstedTimelineCoverageResponse(
            is_partial_history=True,
            earliest_event_date=None,
            latest_event_date=None,
            events_count=0,
        ),
    )

    performance = None
    if result.performance is not None:
        latest = None
        if result.performance.latest is not None:
            latest = SchoolProfilePerformanceYearResponse(
                academic_year=result.performance.latest.academic_year,
                attainment8_average=result.performance.latest.attainment8_average,
                progress8_average=result.performance.latest.progress8_average,
                progress8_disadvantaged=result.performance.latest.progress8_disadvantaged,
                progress8_not_disadvantaged=result.performance.latest.progress8_not_disadvantaged,
                progress8_disadvantaged_gap=result.performance.latest.progress8_disadvantaged_gap,
                engmath_5_plus_pct=result.performance.latest.engmath_5_plus_pct,
                engmath_4_plus_pct=result.performance.latest.engmath_4_plus_pct,
                ebacc_entry_pct=result.performance.latest.ebacc_entry_pct,
                ebacc_5_plus_pct=result.performance.latest.ebacc_5_plus_pct,
                ebacc_4_plus_pct=result.performance.latest.ebacc_4_plus_pct,
                ks2_reading_expected_pct=result.performance.latest.ks2_reading_expected_pct,
                ks2_writing_expected_pct=result.performance.latest.ks2_writing_expected_pct,
                ks2_maths_expected_pct=result.performance.latest.ks2_maths_expected_pct,
                ks2_combined_expected_pct=result.performance.latest.ks2_combined_expected_pct,
                ks2_reading_higher_pct=result.performance.latest.ks2_reading_higher_pct,
                ks2_writing_higher_pct=result.performance.latest.ks2_writing_higher_pct,
                ks2_maths_higher_pct=result.performance.latest.ks2_maths_higher_pct,
                ks2_combined_higher_pct=result.performance.latest.ks2_combined_higher_pct,
            )

        performance = SchoolProfilePerformanceResponse(
            latest=latest,
            history=[
                SchoolProfilePerformanceYearResponse(
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
                for year in result.performance.history
            ],
        )

    return SchoolProfileResponse(
        school=SchoolProfileSchoolResponse(
            urn=result.school.urn,
            name=result.school.name,
            phase=result.school.phase,
            type=result.school.school_type,
            status=result.school.status,
            postcode=result.school.postcode,
            website=result.school.website,
            telephone=result.school.telephone,
            head_title=result.school.head_title,
            head_first_name=result.school.head_first_name,
            head_last_name=result.school.head_last_name,
            head_job_title=result.school.head_job_title,
            address_street=result.school.address_street,
            address_locality=result.school.address_locality,
            address_line3=result.school.address_line3,
            address_town=result.school.address_town,
            address_county=result.school.address_county,
            statutory_low_age=result.school.statutory_low_age,
            statutory_high_age=result.school.statutory_high_age,
            gender=result.school.gender,
            religious_character=result.school.religious_character,
            diocese=result.school.diocese,
            admissions_policy=result.school.admissions_policy,
            sixth_form=result.school.sixth_form,
            nursery_provision=result.school.nursery_provision,
            boarders=result.school.boarders,
            fsm_pct_gias=result.school.fsm_pct_gias,
            trust_name=result.school.trust_name,
            trust_flag=result.school.trust_flag,
            federation_name=result.school.federation_name,
            federation_flag=result.school.federation_flag,
            la_name=result.school.la_name,
            la_code=result.school.la_code,
            urban_rural=result.school.urban_rural,
            number_of_boys=result.school.number_of_boys,
            number_of_girls=result.school.number_of_girls,
            lsoa_code=result.school.lsoa_code,
            lsoa_name=result.school.lsoa_name,
            last_changed_date=result.school.last_changed_date,
            lat=result.school.lat,
            lng=result.school.lng,
        ),
        overview_text=result.overview_text,
        analyst=SchoolProfileAnalystSectionResponse(
            access=_to_section_access_response(result.analyst.access),
            text=result.analyst.text,
            teaser_text=result.analyst.teaser_text,
            disclaimer=result.analyst.disclaimer,
        ),
        demographics_latest=demographics_latest,
        attendance_latest=attendance_latest,
        behaviour_latest=behaviour_latest,
        workforce_latest=workforce_latest,
        leadership_snapshot=leadership_snapshot,
        performance=performance,
        ofsted_latest=ofsted_latest,
        ofsted_timeline=ofsted_timeline,
        neighbourhood=SchoolProfileNeighbourhoodSectionResponse(
            access=_to_section_access_response(result.neighbourhood.access),
            area_context=_to_area_context_response(result.neighbourhood.area_context),
            teaser_text=result.neighbourhood.teaser_text,
        ),
        benchmarks=SchoolProfileBenchmarksResponse(
            metrics=[
                SchoolProfileMetricBenchmarkResponse(
                    metric_key=metric.metric_key,
                    academic_year=metric.academic_year,
                    school_value=metric.school_value,
                    national_value=metric.national_value,
                    local_value=metric.local_value,
                    school_vs_national_delta=metric.school_vs_national_delta,
                    school_vs_local_delta=metric.school_vs_local_delta,
                    local_scope=metric.local_scope,
                    local_area_code=metric.local_area_code,
                    local_area_label=metric.local_area_label,
                )
                for metric in result.benchmarks.metrics
            ],
        ),
        completeness=SchoolProfileCompletenessResponse(
            demographics=_to_section_completeness_response(result.completeness.demographics),
            attendance=_to_section_completeness_response(result.completeness.attendance),
            behaviour=_to_section_completeness_response(result.completeness.behaviour),
            workforce=_to_section_completeness_response(result.completeness.workforce),
            leadership=_to_section_completeness_response(result.completeness.leadership),
            performance=_to_section_completeness_response(result.completeness.performance),
            ofsted_latest=_to_section_completeness_response(result.completeness.ofsted_latest),
            ofsted_timeline=_to_section_completeness_response(result.completeness.ofsted_timeline),
            area_deprivation=_to_section_completeness_response(
                result.completeness.area_deprivation
            ),
            area_crime=_to_section_completeness_response(result.completeness.area_crime),
            area_house_prices=_to_section_completeness_response(
                result.completeness.area_house_prices
            ),
        ),
    )


def _to_section_access_response(value: SectionAccessDto) -> SectionAccessResponse:
    return SectionAccessResponse(
        state=value.state,
        capability_key=value.capability_key,
        reason_code=value.reason_code,
        product_codes=list(value.product_codes),
        requires_auth=value.requires_auth,
        requires_purchase=value.requires_purchase,
        school_name=value.school_name,
    )


def _to_area_context_response(
    value: SchoolAreaContextDto | None,
) -> SchoolProfileAreaContextResponse | None:
    if value is None:
        return None

    deprivation = None
    if value.deprivation is not None:
        deprivation = SchoolProfileAreaDeprivationResponse(
            lsoa_code=value.deprivation.lsoa_code,
            imd_score=value.deprivation.imd_score,
            imd_rank=value.deprivation.imd_rank,
            imd_decile=value.deprivation.imd_decile,
            idaci_score=value.deprivation.idaci_score,
            idaci_decile=value.deprivation.idaci_decile,
            income_score=value.deprivation.income_score,
            income_rank=value.deprivation.income_rank,
            income_decile=value.deprivation.income_decile,
            employment_score=value.deprivation.employment_score,
            employment_rank=value.deprivation.employment_rank,
            employment_decile=value.deprivation.employment_decile,
            education_score=value.deprivation.education_score,
            education_rank=value.deprivation.education_rank,
            education_decile=value.deprivation.education_decile,
            health_score=value.deprivation.health_score,
            health_rank=value.deprivation.health_rank,
            health_decile=value.deprivation.health_decile,
            crime_score=value.deprivation.crime_score,
            crime_rank=value.deprivation.crime_rank,
            crime_decile=value.deprivation.crime_decile,
            barriers_score=value.deprivation.barriers_score,
            barriers_rank=value.deprivation.barriers_rank,
            barriers_decile=value.deprivation.barriers_decile,
            living_environment_score=value.deprivation.living_environment_score,
            living_environment_rank=value.deprivation.living_environment_rank,
            living_environment_decile=value.deprivation.living_environment_decile,
            population_total=value.deprivation.population_total,
            local_authority_district_code=value.deprivation.local_authority_district_code,
            local_authority_district_name=value.deprivation.local_authority_district_name,
            source_release=value.deprivation.source_release,
        )

    crime = None
    if value.crime is not None:
        crime = SchoolProfileAreaCrimeResponse(
            radius_miles=value.crime.radius_miles,
            latest_month=value.crime.latest_month,
            total_incidents=value.crime.total_incidents,
            population_denominator=value.crime.population_denominator,
            incidents_per_1000=value.crime.incidents_per_1000,
            annual_incidents_per_1000=[
                SchoolProfileAreaCrimeAnnualRateResponse(
                    year=annual_rate.year,
                    total_incidents=annual_rate.total_incidents,
                    incidents_per_1000=annual_rate.incidents_per_1000,
                )
                for annual_rate in value.crime.annual_incidents_per_1000
            ],
            categories=[
                SchoolProfileAreaCrimeCategoryResponse(
                    category=category.category,
                    incident_count=category.incident_count,
                )
                for category in value.crime.categories
            ],
        )

    house_prices = None
    if value.house_prices is not None:
        house_prices = SchoolProfileAreaHousePricesResponse(
            area_code=value.house_prices.area_code,
            area_name=value.house_prices.area_name,
            latest_month=value.house_prices.latest_month,
            average_price=value.house_prices.average_price,
            annual_change_pct=value.house_prices.annual_change_pct,
            monthly_change_pct=value.house_prices.monthly_change_pct,
            three_year_change_pct=value.house_prices.three_year_change_pct,
            trend=[
                SchoolProfileAreaHousePricePointResponse(
                    month=point.month,
                    average_price=point.average_price,
                    annual_change_pct=point.annual_change_pct,
                    monthly_change_pct=point.monthly_change_pct,
                )
                for point in value.house_prices.trend
            ],
        )

    return SchoolProfileAreaContextResponse(
        deprivation=deprivation,
        crime=crime,
        house_prices=house_prices,
        coverage=SchoolProfileAreaContextCoverageResponse(
            has_deprivation=value.coverage.has_deprivation,
            has_crime=value.coverage.has_crime,
            crime_months_available=value.coverage.crime_months_available,
            has_house_prices=value.coverage.has_house_prices,
            house_price_months_available=value.coverage.house_price_months_available,
        ),
    )


def _to_section_completeness_response(
    value: SchoolProfileSectionCompletenessDto,
) -> SchoolProfileSectionCompletenessResponse:
    return SchoolProfileSectionCompletenessResponse(
        status=value.status,
        reason_code=value.reason_code,
        last_updated_at=value.last_updated_at,
        years_available=list(value.years_available) if value.years_available is not None else None,
    )
