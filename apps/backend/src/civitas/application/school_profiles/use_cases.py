from civitas.application.school_profiles.dto import (
    SchoolDemographicsCoverageDto,
    SchoolDemographicsLatestDto,
    SchoolOfstedLatestDto,
    SchoolProfileResponseDto,
    SchoolProfileSchoolDto,
)
from civitas.application.school_profiles.errors import SchoolProfileNotFoundError
from civitas.application.school_profiles.ports.school_profile_repository import (
    SchoolProfileRepository,
)


class GetSchoolProfileUseCase:
    def __init__(self, school_profile_repository: SchoolProfileRepository) -> None:
        self._school_profile_repository = school_profile_repository

    def execute(self, *, urn: str) -> SchoolProfileResponseDto:
        normalized_urn = urn.strip()
        profile = self._school_profile_repository.get_school_profile(normalized_urn)
        if profile is None:
            raise SchoolProfileNotFoundError(normalized_urn)

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
            )

        ofsted_latest = None
        if profile.ofsted_latest is not None:
            ofsted_latest = SchoolOfstedLatestDto(
                overall_effectiveness_code=profile.ofsted_latest.overall_effectiveness_code,
                overall_effectiveness_label=profile.ofsted_latest.overall_effectiveness_label,
                inspection_start_date=profile.ofsted_latest.inspection_start_date,
                publication_date=profile.ofsted_latest.publication_date,
                is_graded=profile.ofsted_latest.is_graded,
                ungraded_outcome=profile.ofsted_latest.ungraded_outcome,
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
            ofsted_latest=ofsted_latest,
        )
