from civitas.application.school_profiles.dto import (
    SchoolAreaContextCoverageDto,
    SchoolAreaContextDto,
    SchoolAreaCrimeCategoryDto,
    SchoolAreaCrimeDto,
    SchoolAreaDeprivationDto,
    SchoolDemographicsCoverageDto,
    SchoolDemographicsEthnicityGroupDto,
    SchoolDemographicsLatestDto,
    SchoolOfstedLatestDto,
    SchoolOfstedTimelineCoverageDto,
    SchoolOfstedTimelineDto,
    SchoolOfstedTimelineEventDto,
    SchoolPerformanceDto,
    SchoolPerformanceYearDto,
    SchoolProfileCompletenessDto,
    SchoolProfileResponseDto,
    SchoolProfileSchoolDto,
    SchoolProfileSectionCompletenessDto,
)
from civitas.application.school_profiles.errors import SchoolProfileNotFoundError
from civitas.application.school_profiles.ports.postcode_context_resolver import (
    PostcodeContextResolver,
)
from civitas.application.school_profiles.ports.school_profile_repository import (
    SchoolProfileRepository,
)
from civitas.domain.school_profiles.models import SchoolProfile


class GetSchoolProfileUseCase:
    def __init__(
        self,
        school_profile_repository: SchoolProfileRepository,
        postcode_context_resolver: PostcodeContextResolver | None = None,
    ) -> None:
        self._school_profile_repository = school_profile_repository
        self._postcode_context_resolver = postcode_context_resolver

    def execute(self, *, urn: str) -> SchoolProfileResponseDto:
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
                sen_pct=profile.demographics_latest.sen_pct,
                ehcp_pct=profile.demographics_latest.ehcp_pct,
                eal_pct=profile.demographics_latest.eal_pct,
                first_language_english_pct=profile.demographics_latest.first_language_english_pct,
                first_language_unclassified_pct=profile.demographics_latest.first_language_unclassified_pct,
                coverage=SchoolDemographicsCoverageDto(
                    fsm_supported=profile.demographics_latest.coverage.fsm_supported,
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
                    source_release=profile.area_context.deprivation.source_release,
                )

            crime = None
            if profile.area_context.crime is not None:
                crime = SchoolAreaCrimeDto(
                    radius_miles=profile.area_context.crime.radius_miles,
                    latest_month=profile.area_context.crime.latest_month,
                    total_incidents=profile.area_context.crime.total_incidents,
                    categories=tuple(
                        SchoolAreaCrimeCategoryDto(
                            category=category.category,
                            incident_count=category.incident_count,
                        )
                        for category in profile.area_context.crime.categories
                    ),
                )

            area_context = SchoolAreaContextDto(
                deprivation=deprivation,
                crime=crime,
                coverage=SchoolAreaContextCoverageDto(
                    has_deprivation=profile.area_context.coverage.has_deprivation,
                    has_crime=profile.area_context.coverage.has_crime,
                    crime_months_available=profile.area_context.coverage.crime_months_available,
                ),
            )

        completeness = SchoolProfileCompletenessDto(
            demographics=SchoolProfileSectionCompletenessDto(
                status=profile.completeness.demographics.status,
                reason_code=profile.completeness.demographics.reason_code,
                last_updated_at=profile.completeness.demographics.last_updated_at,
                years_available=profile.completeness.demographics.years_available,
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
        )

        return SchoolProfileResponseDto(
            school=SchoolProfileSchoolDto(
                urn=profile.school.urn,
                name=profile.school.name,
                phase=profile.school.phase,
                school_type=profile.school.school_type,
                status=profile.school.status,
                postcode=profile.school.postcode,
                lat=profile.school.lat,
                lng=profile.school.lng,
            ),
            demographics_latest=demographics_latest,
            performance=performance,
            ofsted_latest=ofsted_latest,
            ofsted_timeline=ofsted_timeline,
            area_context=area_context,
            completeness=completeness,
        )

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

        refreshed_profile = self._school_profile_repository.get_school_profile(urn)
        if refreshed_profile is None:
            return profile
        return refreshed_profile
