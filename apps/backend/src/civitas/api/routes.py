from collections.abc import Sequence

from fastapi import APIRouter, Depends, HTTPException, Query

from civitas.api.dependencies import (
    get_create_task_use_case,
    get_list_tasks_use_case,
    get_school_compare_use_case,
    get_school_profile_use_case,
    get_school_trend_dashboard_use_case,
    get_school_trends_use_case,
    get_search_schools_by_name_use_case,
    get_search_schools_by_postcode_use_case,
)
from civitas.api.schemas.school_compare import SchoolCompareResponse
from civitas.api.schemas.school_profiles import (
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
from civitas.api.schemas.school_trends import (
    SchoolTrendBenchmarkPointResponse,
    SchoolTrendDashboardMetricResponse,
    SchoolTrendDashboardResponse,
    SchoolTrendDashboardSectionResponse,
    SchoolTrendPointResponse,
    SchoolTrendsBenchmarksResponse,
    SchoolTrendsCompletenessResponse,
    SchoolTrendsHistoryQualityResponse,
    SchoolTrendsResponse,
    SchoolTrendsSectionCompletenessResponse,
    SchoolTrendsSeriesResponse,
)
from civitas.api.schemas.schools import (
    PostcodeSchoolSearchItemResponse,
    SchoolNameSearchResponse,
    SchoolSearchAcademicMetricResponse,
    SchoolSearchItemResponse,
    SchoolSearchLatestOfstedResponse,
    SchoolsSearchCenterResponse,
    SchoolsSearchQueryResponse,
    SchoolsSearchResponse,
)
from civitas.api.schemas.tasks import TaskCreateRequest, TaskResponse
from civitas.api.school_compare_presenter import to_school_compare_response
from civitas.application.school_compare.errors import (
    InvalidSchoolCompareParametersError,
    SchoolCompareDataUnavailableError,
    SchoolCompareNotFoundError,
)
from civitas.application.school_compare.use_cases import GetSchoolCompareUseCase
from civitas.application.school_profiles.errors import (
    SchoolProfileDataUnavailableError,
    SchoolProfileNotFoundError,
)
from civitas.application.school_profiles.use_cases import GetSchoolProfileUseCase
from civitas.application.school_trends.errors import (
    SchoolTrendsDataUnavailableError,
    SchoolTrendsNotFoundError,
)
from civitas.application.school_trends.use_cases import (
    GetSchoolTrendDashboardUseCase,
    GetSchoolTrendsUseCase,
)
from civitas.application.schools.errors import (
    InvalidSchoolSearchParametersError,
    PostcodeNotFoundError,
    PostcodeResolverUnavailableError,
)
from civitas.application.schools.use_cases import (
    SearchSchoolsByNameUseCase,
    SearchSchoolsByPostcodeUseCase,
)
from civitas.application.tasks.use_cases import CreateTaskUseCase, ListTasksUseCase

router = APIRouter(prefix="/api/v1", tags=["tasks"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/tasks", response_model=TaskResponse, status_code=201)
def create_task(
    request: TaskCreateRequest,
    use_case: CreateTaskUseCase = Depends(get_create_task_use_case),
) -> TaskResponse:
    task = use_case.execute(title=request.title)
    return TaskResponse(id=task.id, title=task.title, created_at=task.created_at)


@router.get("/tasks", response_model=list[TaskResponse])
def list_tasks(
    use_case: ListTasksUseCase = Depends(get_list_tasks_use_case),
) -> Sequence[TaskResponse]:
    tasks = use_case.execute()
    return [TaskResponse(id=t.id, title=t.title, created_at=t.created_at) for t in tasks]


@router.get(
    "/schools",
    response_model=SchoolsSearchResponse,
    tags=["schools"],
    responses={
        400: {"description": "Invalid postcode or radius parameter."},
        404: {"description": "Postcode not found."},
        503: {"description": "Postcode resolver unavailable."},
    },
)
def search_schools(
    postcode: str = Query(...),
    radius: float | None = Query(default=None),
    phase: list[str] | None = Query(default=None),
    sort: str | None = Query(default=None),
    use_case: SearchSchoolsByPostcodeUseCase = Depends(get_search_schools_by_postcode_use_case),
) -> SchoolsSearchResponse:
    try:
        result = use_case.execute(
            postcode=postcode,
            radius_miles=radius,
            phases=tuple(phase) if phase is not None else None,
            sort=sort,
        )
    except InvalidSchoolSearchParametersError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PostcodeNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PostcodeResolverUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return SchoolsSearchResponse(
        query=SchoolsSearchQueryResponse(
            postcode=result.query.postcode,
            radius_miles=result.query.radius_miles,
            phases=list(result.query.phases),
            sort=result.query.sort,
        ),
        center=SchoolsSearchCenterResponse(
            lat=result.center.lat,
            lng=result.center.lng,
        ),
        count=result.count,
        schools=[
            PostcodeSchoolSearchItemResponse(
                urn=school.urn,
                name=school.name,
                type=school.school_type,
                phase=school.phase,
                postcode=school.postcode,
                lat=school.lat,
                lng=school.lng,
                distance_miles=school.distance_miles,
                pupil_count=school.pupil_count,
                latest_ofsted=SchoolSearchLatestOfstedResponse(
                    label=school.latest_ofsted.label,
                    sort_rank=school.latest_ofsted.sort_rank,
                    availability=school.latest_ofsted.availability,
                ),
                academic_metric=SchoolSearchAcademicMetricResponse(
                    metric_key=school.academic_metric.metric_key,
                    label=school.academic_metric.label,
                    display_value=school.academic_metric.display_value,
                    sort_value=school.academic_metric.sort_value,
                    availability=school.academic_metric.availability,
                ),
            )
            for school in result.schools
        ],
    )


@router.get(
    "/schools/search",
    response_model=SchoolNameSearchResponse,
    tags=["schools"],
    responses={
        400: {"description": "Invalid name search parameter."},
    },
)
def search_schools_by_name(
    name: str = Query(..., min_length=3),
    use_case: SearchSchoolsByNameUseCase = Depends(get_search_schools_by_name_use_case),
) -> SchoolNameSearchResponse:
    try:
        result = use_case.execute(name=name)
    except InvalidSchoolSearchParametersError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return SchoolNameSearchResponse(
        count=result.count,
        schools=[
            SchoolSearchItemResponse(
                urn=school.urn,
                name=school.name,
                type=school.school_type,
                phase=school.phase,
                postcode=school.postcode,
                lat=school.lat,
                lng=school.lng,
                distance_miles=school.distance_miles,
            )
            for school in result.schools
        ],
    )


@router.get(
    "/schools/compare",
    response_model=SchoolCompareResponse,
    tags=["schools"],
    responses={
        400: {"description": "Invalid compare request parameters."},
        404: {"description": "One or more school URNs were not found."},
        503: {"description": "School compare datastore unavailable."},
    },
)
def get_school_compare(
    urns: str | None = Query(default=None),
    use_case: GetSchoolCompareUseCase = Depends(get_school_compare_use_case),
) -> SchoolCompareResponse:
    try:
        result = use_case.execute(urns=urns or "")
    except InvalidSchoolCompareParametersError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except SchoolCompareNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SchoolCompareDataUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return to_school_compare_response(result)


@router.get(
    "/schools/{urn}",
    response_model=SchoolProfileResponse,
    tags=["schools"],
    responses={
        404: {"description": "School URN not found."},
        503: {"description": "School profile datastore unavailable."},
    },
)
def get_school_profile(
    urn: str,
    use_case: GetSchoolProfileUseCase = Depends(get_school_profile_use_case),
) -> SchoolProfileResponse:
    try:
        result = use_case.execute(urn=urn)
    except SchoolProfileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SchoolProfileDataUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

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

    deprivation = None
    if result.area_context is not None and result.area_context.deprivation is not None:
        deprivation = SchoolProfileAreaDeprivationResponse(
            lsoa_code=result.area_context.deprivation.lsoa_code,
            imd_score=result.area_context.deprivation.imd_score,
            imd_rank=result.area_context.deprivation.imd_rank,
            imd_decile=result.area_context.deprivation.imd_decile,
            idaci_score=result.area_context.deprivation.idaci_score,
            idaci_decile=result.area_context.deprivation.idaci_decile,
            income_score=result.area_context.deprivation.income_score,
            income_rank=result.area_context.deprivation.income_rank,
            income_decile=result.area_context.deprivation.income_decile,
            employment_score=result.area_context.deprivation.employment_score,
            employment_rank=result.area_context.deprivation.employment_rank,
            employment_decile=result.area_context.deprivation.employment_decile,
            education_score=result.area_context.deprivation.education_score,
            education_rank=result.area_context.deprivation.education_rank,
            education_decile=result.area_context.deprivation.education_decile,
            health_score=result.area_context.deprivation.health_score,
            health_rank=result.area_context.deprivation.health_rank,
            health_decile=result.area_context.deprivation.health_decile,
            crime_score=result.area_context.deprivation.crime_score,
            crime_rank=result.area_context.deprivation.crime_rank,
            crime_decile=result.area_context.deprivation.crime_decile,
            barriers_score=result.area_context.deprivation.barriers_score,
            barriers_rank=result.area_context.deprivation.barriers_rank,
            barriers_decile=result.area_context.deprivation.barriers_decile,
            living_environment_score=result.area_context.deprivation.living_environment_score,
            living_environment_rank=result.area_context.deprivation.living_environment_rank,
            living_environment_decile=result.area_context.deprivation.living_environment_decile,
            population_total=result.area_context.deprivation.population_total,
            local_authority_district_code=(
                result.area_context.deprivation.local_authority_district_code
            ),
            local_authority_district_name=(
                result.area_context.deprivation.local_authority_district_name
            ),
            source_release=result.area_context.deprivation.source_release,
        )

    crime = None
    if result.area_context is not None and result.area_context.crime is not None:
        crime = SchoolProfileAreaCrimeResponse(
            radius_miles=result.area_context.crime.radius_miles,
            latest_month=result.area_context.crime.latest_month,
            total_incidents=result.area_context.crime.total_incidents,
            population_denominator=result.area_context.crime.population_denominator,
            incidents_per_1000=result.area_context.crime.incidents_per_1000,
            annual_incidents_per_1000=[
                SchoolProfileAreaCrimeAnnualRateResponse(
                    year=annual_rate.year,
                    total_incidents=annual_rate.total_incidents,
                    incidents_per_1000=annual_rate.incidents_per_1000,
                )
                for annual_rate in result.area_context.crime.annual_incidents_per_1000
            ],
            categories=[
                SchoolProfileAreaCrimeCategoryResponse(
                    category=category.category,
                    incident_count=category.incident_count,
                )
                for category in result.area_context.crime.categories
            ],
        )

    house_prices = None
    if result.area_context is not None and result.area_context.house_prices is not None:
        house_prices = SchoolProfileAreaHousePricesResponse(
            area_code=result.area_context.house_prices.area_code,
            area_name=result.area_context.house_prices.area_name,
            latest_month=result.area_context.house_prices.latest_month,
            average_price=result.area_context.house_prices.average_price,
            annual_change_pct=result.area_context.house_prices.annual_change_pct,
            monthly_change_pct=result.area_context.house_prices.monthly_change_pct,
            three_year_change_pct=result.area_context.house_prices.three_year_change_pct,
            trend=[
                SchoolProfileAreaHousePricePointResponse(
                    month=point.month,
                    average_price=point.average_price,
                    annual_change_pct=point.annual_change_pct,
                    monthly_change_pct=point.monthly_change_pct,
                )
                for point in result.area_context.house_prices.trend
            ],
        )

    area_context = SchoolProfileAreaContextResponse(
        deprivation=deprivation,
        crime=crime,
        house_prices=house_prices,
        coverage=SchoolProfileAreaContextCoverageResponse(
            has_deprivation=result.area_context.coverage.has_deprivation,
            has_crime=result.area_context.coverage.has_crime,
            crime_months_available=result.area_context.coverage.crime_months_available,
            has_house_prices=result.area_context.coverage.has_house_prices,
            house_price_months_available=result.area_context.coverage.house_price_months_available,
        )
        if result.area_context is not None
        else SchoolProfileAreaContextCoverageResponse(
            has_deprivation=False,
            has_crime=False,
            crime_months_available=0,
            has_house_prices=False,
            house_price_months_available=0,
        ),
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
        analyst_text=result.analyst_text,
        demographics_latest=demographics_latest,
        attendance_latest=attendance_latest,
        behaviour_latest=behaviour_latest,
        workforce_latest=workforce_latest,
        leadership_snapshot=leadership_snapshot,
        performance=performance,
        ofsted_latest=ofsted_latest,
        ofsted_timeline=ofsted_timeline,
        area_context=area_context,
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
            demographics=SchoolProfileSectionCompletenessResponse(
                status=result.completeness.demographics.status,
                reason_code=result.completeness.demographics.reason_code,
                last_updated_at=result.completeness.demographics.last_updated_at,
                years_available=(
                    list(result.completeness.demographics.years_available)
                    if result.completeness.demographics.years_available is not None
                    else None
                ),
            ),
            attendance=SchoolProfileSectionCompletenessResponse(
                status=result.completeness.attendance.status,
                reason_code=result.completeness.attendance.reason_code,
                last_updated_at=result.completeness.attendance.last_updated_at,
                years_available=(
                    list(result.completeness.attendance.years_available)
                    if result.completeness.attendance.years_available is not None
                    else None
                ),
            ),
            behaviour=SchoolProfileSectionCompletenessResponse(
                status=result.completeness.behaviour.status,
                reason_code=result.completeness.behaviour.reason_code,
                last_updated_at=result.completeness.behaviour.last_updated_at,
                years_available=(
                    list(result.completeness.behaviour.years_available)
                    if result.completeness.behaviour.years_available is not None
                    else None
                ),
            ),
            workforce=SchoolProfileSectionCompletenessResponse(
                status=result.completeness.workforce.status,
                reason_code=result.completeness.workforce.reason_code,
                last_updated_at=result.completeness.workforce.last_updated_at,
                years_available=(
                    list(result.completeness.workforce.years_available)
                    if result.completeness.workforce.years_available is not None
                    else None
                ),
            ),
            leadership=SchoolProfileSectionCompletenessResponse(
                status=result.completeness.leadership.status,
                reason_code=result.completeness.leadership.reason_code,
                last_updated_at=result.completeness.leadership.last_updated_at,
                years_available=(
                    list(result.completeness.leadership.years_available)
                    if result.completeness.leadership.years_available is not None
                    else None
                ),
            ),
            performance=SchoolProfileSectionCompletenessResponse(
                status=result.completeness.performance.status,
                reason_code=result.completeness.performance.reason_code,
                last_updated_at=result.completeness.performance.last_updated_at,
                years_available=(
                    list(result.completeness.performance.years_available)
                    if result.completeness.performance.years_available is not None
                    else None
                ),
            ),
            ofsted_latest=SchoolProfileSectionCompletenessResponse(
                status=result.completeness.ofsted_latest.status,
                reason_code=result.completeness.ofsted_latest.reason_code,
                last_updated_at=result.completeness.ofsted_latest.last_updated_at,
                years_available=(
                    list(result.completeness.ofsted_latest.years_available)
                    if result.completeness.ofsted_latest.years_available is not None
                    else None
                ),
            ),
            ofsted_timeline=SchoolProfileSectionCompletenessResponse(
                status=result.completeness.ofsted_timeline.status,
                reason_code=result.completeness.ofsted_timeline.reason_code,
                last_updated_at=result.completeness.ofsted_timeline.last_updated_at,
                years_available=(
                    list(result.completeness.ofsted_timeline.years_available)
                    if result.completeness.ofsted_timeline.years_available is not None
                    else None
                ),
            ),
            area_deprivation=SchoolProfileSectionCompletenessResponse(
                status=result.completeness.area_deprivation.status,
                reason_code=result.completeness.area_deprivation.reason_code,
                last_updated_at=result.completeness.area_deprivation.last_updated_at,
                years_available=(
                    list(result.completeness.area_deprivation.years_available)
                    if result.completeness.area_deprivation.years_available is not None
                    else None
                ),
            ),
            area_crime=SchoolProfileSectionCompletenessResponse(
                status=result.completeness.area_crime.status,
                reason_code=result.completeness.area_crime.reason_code,
                last_updated_at=result.completeness.area_crime.last_updated_at,
                years_available=(
                    list(result.completeness.area_crime.years_available)
                    if result.completeness.area_crime.years_available is not None
                    else None
                ),
            ),
            area_house_prices=SchoolProfileSectionCompletenessResponse(
                status=result.completeness.area_house_prices.status,
                reason_code=result.completeness.area_house_prices.reason_code,
                last_updated_at=result.completeness.area_house_prices.last_updated_at,
                years_available=(
                    list(result.completeness.area_house_prices.years_available)
                    if result.completeness.area_house_prices.years_available is not None
                    else None
                ),
            ),
        ),
    )


@router.get(
    "/schools/{urn}/trends",
    response_model=SchoolTrendsResponse,
    tags=["schools"],
    responses={
        404: {"description": "School URN not found."},
        503: {"description": "School trends datastore unavailable."},
    },
)
def get_school_trends(
    urn: str,
    use_case: GetSchoolTrendsUseCase = Depends(get_school_trends_use_case),
) -> SchoolTrendsResponse:
    try:
        result = use_case.execute(urn=urn)
    except SchoolTrendsNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SchoolTrendsDataUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return SchoolTrendsResponse(
        urn=result.urn,
        years_available=list(result.years_available),
        history_quality=SchoolTrendsHistoryQualityResponse(
            is_partial_history=result.history_quality.is_partial_history,
            min_years_for_delta=result.history_quality.min_years_for_delta,
            years_count=result.history_quality.years_count,
        ),
        series=SchoolTrendsSeriesResponse(
            disadvantaged_pct=[
                SchoolTrendPointResponse(
                    academic_year=point.academic_year,
                    value=point.value,
                    delta=point.delta,
                    direction=point.direction,
                )
                for point in result.series.disadvantaged_pct
            ],
            fsm_pct=[
                SchoolTrendPointResponse(
                    academic_year=point.academic_year,
                    value=point.value,
                    delta=point.delta,
                    direction=point.direction,
                )
                for point in result.series.fsm_pct
            ],
            fsm6_pct=[
                SchoolTrendPointResponse(
                    academic_year=point.academic_year,
                    value=point.value,
                    delta=point.delta,
                    direction=point.direction,
                )
                for point in result.series.fsm6_pct
            ],
            sen_pct=[
                SchoolTrendPointResponse(
                    academic_year=point.academic_year,
                    value=point.value,
                    delta=point.delta,
                    direction=point.direction,
                )
                for point in result.series.sen_pct
            ],
            ehcp_pct=[
                SchoolTrendPointResponse(
                    academic_year=point.academic_year,
                    value=point.value,
                    delta=point.delta,
                    direction=point.direction,
                )
                for point in result.series.ehcp_pct
            ],
            eal_pct=[
                SchoolTrendPointResponse(
                    academic_year=point.academic_year,
                    value=point.value,
                    delta=point.delta,
                    direction=point.direction,
                )
                for point in result.series.eal_pct
            ],
            first_language_english_pct=[
                SchoolTrendPointResponse(
                    academic_year=point.academic_year,
                    value=point.value,
                    delta=point.delta,
                    direction=point.direction,
                )
                for point in result.series.first_language_english_pct
            ],
            first_language_unclassified_pct=[
                SchoolTrendPointResponse(
                    academic_year=point.academic_year,
                    value=point.value,
                    delta=point.delta,
                    direction=point.direction,
                )
                for point in result.series.first_language_unclassified_pct
            ],
            male_pct=[
                SchoolTrendPointResponse(
                    academic_year=point.academic_year,
                    value=point.value,
                    delta=point.delta,
                    direction=point.direction,
                )
                for point in result.series.male_pct
            ],
            female_pct=[
                SchoolTrendPointResponse(
                    academic_year=point.academic_year,
                    value=point.value,
                    delta=point.delta,
                    direction=point.direction,
                )
                for point in result.series.female_pct
            ],
            pupil_mobility_pct=[
                SchoolTrendPointResponse(
                    academic_year=point.academic_year,
                    value=point.value,
                    delta=point.delta,
                    direction=point.direction,
                )
                for point in result.series.pupil_mobility_pct
            ],
            overall_attendance_pct=[
                SchoolTrendPointResponse(
                    academic_year=point.academic_year,
                    value=point.value,
                    delta=point.delta,
                    direction=point.direction,
                )
                for point in result.series.overall_attendance_pct
            ],
            overall_absence_pct=[
                SchoolTrendPointResponse(
                    academic_year=point.academic_year,
                    value=point.value,
                    delta=point.delta,
                    direction=point.direction,
                )
                for point in result.series.overall_absence_pct
            ],
            persistent_absence_pct=[
                SchoolTrendPointResponse(
                    academic_year=point.academic_year,
                    value=point.value,
                    delta=point.delta,
                    direction=point.direction,
                )
                for point in result.series.persistent_absence_pct
            ],
            suspensions_count=[
                SchoolTrendPointResponse(
                    academic_year=point.academic_year,
                    value=point.value,
                    delta=point.delta,
                    direction=point.direction,
                )
                for point in result.series.suspensions_count
            ],
            suspensions_rate=[
                SchoolTrendPointResponse(
                    academic_year=point.academic_year,
                    value=point.value,
                    delta=point.delta,
                    direction=point.direction,
                )
                for point in result.series.suspensions_rate
            ],
            permanent_exclusions_count=[
                SchoolTrendPointResponse(
                    academic_year=point.academic_year,
                    value=point.value,
                    delta=point.delta,
                    direction=point.direction,
                )
                for point in result.series.permanent_exclusions_count
            ],
            permanent_exclusions_rate=[
                SchoolTrendPointResponse(
                    academic_year=point.academic_year,
                    value=point.value,
                    delta=point.delta,
                    direction=point.direction,
                )
                for point in result.series.permanent_exclusions_rate
            ],
            pupil_teacher_ratio=[
                SchoolTrendPointResponse(
                    academic_year=point.academic_year,
                    value=point.value,
                    delta=point.delta,
                    direction=point.direction,
                )
                for point in result.series.pupil_teacher_ratio
            ],
            supply_staff_pct=[
                SchoolTrendPointResponse(
                    academic_year=point.academic_year,
                    value=point.value,
                    delta=point.delta,
                    direction=point.direction,
                )
                for point in result.series.supply_staff_pct
            ],
            teachers_3plus_years_pct=[
                SchoolTrendPointResponse(
                    academic_year=point.academic_year,
                    value=point.value,
                    delta=point.delta,
                    direction=point.direction,
                )
                for point in result.series.teachers_3plus_years_pct
            ],
            teacher_turnover_pct=[
                SchoolTrendPointResponse(
                    academic_year=point.academic_year,
                    value=point.value,
                    delta=point.delta,
                    direction=point.direction,
                )
                for point in result.series.teacher_turnover_pct
            ],
            qts_pct=[
                SchoolTrendPointResponse(
                    academic_year=point.academic_year,
                    value=point.value,
                    delta=point.delta,
                    direction=point.direction,
                )
                for point in result.series.qts_pct
            ],
            qualifications_level6_plus_pct=[
                SchoolTrendPointResponse(
                    academic_year=point.academic_year,
                    value=point.value,
                    delta=point.delta,
                    direction=point.direction,
                )
                for point in result.series.qualifications_level6_plus_pct
            ],
        ),
        benchmarks=SchoolTrendsBenchmarksResponse(
            disadvantaged_pct=[
                SchoolTrendBenchmarkPointResponse(**point.__dict__)
                for point in result.benchmarks.disadvantaged_pct
            ],
            fsm_pct=[
                SchoolTrendBenchmarkPointResponse(**point.__dict__)
                for point in result.benchmarks.fsm_pct
            ],
            fsm6_pct=[
                SchoolTrendBenchmarkPointResponse(**point.__dict__)
                for point in result.benchmarks.fsm6_pct
            ],
            sen_pct=[
                SchoolTrendBenchmarkPointResponse(**point.__dict__)
                for point in result.benchmarks.sen_pct
            ],
            ehcp_pct=[
                SchoolTrendBenchmarkPointResponse(**point.__dict__)
                for point in result.benchmarks.ehcp_pct
            ],
            eal_pct=[
                SchoolTrendBenchmarkPointResponse(**point.__dict__)
                for point in result.benchmarks.eal_pct
            ],
            first_language_english_pct=[
                SchoolTrendBenchmarkPointResponse(**point.__dict__)
                for point in result.benchmarks.first_language_english_pct
            ],
            first_language_unclassified_pct=[
                SchoolTrendBenchmarkPointResponse(**point.__dict__)
                for point in result.benchmarks.first_language_unclassified_pct
            ],
            male_pct=[
                SchoolTrendBenchmarkPointResponse(**point.__dict__)
                for point in result.benchmarks.male_pct
            ],
            female_pct=[
                SchoolTrendBenchmarkPointResponse(**point.__dict__)
                for point in result.benchmarks.female_pct
            ],
            pupil_mobility_pct=[
                SchoolTrendBenchmarkPointResponse(**point.__dict__)
                for point in result.benchmarks.pupil_mobility_pct
            ],
            overall_attendance_pct=[
                SchoolTrendBenchmarkPointResponse(**point.__dict__)
                for point in result.benchmarks.overall_attendance_pct
            ],
            overall_absence_pct=[
                SchoolTrendBenchmarkPointResponse(**point.__dict__)
                for point in result.benchmarks.overall_absence_pct
            ],
            persistent_absence_pct=[
                SchoolTrendBenchmarkPointResponse(**point.__dict__)
                for point in result.benchmarks.persistent_absence_pct
            ],
            suspensions_count=[
                SchoolTrendBenchmarkPointResponse(**point.__dict__)
                for point in result.benchmarks.suspensions_count
            ],
            suspensions_rate=[
                SchoolTrendBenchmarkPointResponse(**point.__dict__)
                for point in result.benchmarks.suspensions_rate
            ],
            permanent_exclusions_count=[
                SchoolTrendBenchmarkPointResponse(**point.__dict__)
                for point in result.benchmarks.permanent_exclusions_count
            ],
            permanent_exclusions_rate=[
                SchoolTrendBenchmarkPointResponse(**point.__dict__)
                for point in result.benchmarks.permanent_exclusions_rate
            ],
            pupil_teacher_ratio=[
                SchoolTrendBenchmarkPointResponse(**point.__dict__)
                for point in result.benchmarks.pupil_teacher_ratio
            ],
            supply_staff_pct=[
                SchoolTrendBenchmarkPointResponse(**point.__dict__)
                for point in result.benchmarks.supply_staff_pct
            ],
            teachers_3plus_years_pct=[
                SchoolTrendBenchmarkPointResponse(**point.__dict__)
                for point in result.benchmarks.teachers_3plus_years_pct
            ],
            teacher_turnover_pct=[
                SchoolTrendBenchmarkPointResponse(**point.__dict__)
                for point in result.benchmarks.teacher_turnover_pct
            ],
            qts_pct=[
                SchoolTrendBenchmarkPointResponse(**point.__dict__)
                for point in result.benchmarks.qts_pct
            ],
            qualifications_level6_plus_pct=[
                SchoolTrendBenchmarkPointResponse(**point.__dict__)
                for point in result.benchmarks.qualifications_level6_plus_pct
            ],
        ),
        completeness=SchoolTrendsCompletenessResponse(
            status=result.completeness.status,
            reason_code=result.completeness.reason_code,
            last_updated_at=result.completeness.last_updated_at,
            years_available=(
                list(result.completeness.years_available)
                if result.completeness.years_available is not None
                else None
            ),
        ),
        section_completeness=SchoolTrendsSectionCompletenessResponse(
            demographics=SchoolTrendsCompletenessResponse(
                status=result.section_completeness.demographics.status,
                reason_code=result.section_completeness.demographics.reason_code,
                last_updated_at=result.section_completeness.demographics.last_updated_at,
                years_available=(
                    list(result.section_completeness.demographics.years_available)
                    if result.section_completeness.demographics.years_available is not None
                    else None
                ),
            ),
            attendance=SchoolTrendsCompletenessResponse(
                status=result.section_completeness.attendance.status,
                reason_code=result.section_completeness.attendance.reason_code,
                last_updated_at=result.section_completeness.attendance.last_updated_at,
                years_available=(
                    list(result.section_completeness.attendance.years_available)
                    if result.section_completeness.attendance.years_available is not None
                    else None
                ),
            ),
            behaviour=SchoolTrendsCompletenessResponse(
                status=result.section_completeness.behaviour.status,
                reason_code=result.section_completeness.behaviour.reason_code,
                last_updated_at=result.section_completeness.behaviour.last_updated_at,
                years_available=(
                    list(result.section_completeness.behaviour.years_available)
                    if result.section_completeness.behaviour.years_available is not None
                    else None
                ),
            ),
            workforce=SchoolTrendsCompletenessResponse(
                status=result.section_completeness.workforce.status,
                reason_code=result.section_completeness.workforce.reason_code,
                last_updated_at=result.section_completeness.workforce.last_updated_at,
                years_available=(
                    list(result.section_completeness.workforce.years_available)
                    if result.section_completeness.workforce.years_available is not None
                    else None
                ),
            ),
        ),
    )


@router.get(
    "/schools/{urn}/trends/dashboard",
    response_model=SchoolTrendDashboardResponse,
    tags=["schools"],
    responses={
        404: {"description": "School URN not found."},
        503: {"description": "School trends datastore unavailable."},
    },
)
def get_school_trend_dashboard(
    urn: str,
    use_case: GetSchoolTrendDashboardUseCase = Depends(get_school_trend_dashboard_use_case),
) -> SchoolTrendDashboardResponse:
    try:
        result = use_case.execute(urn=urn)
    except SchoolTrendsNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SchoolTrendsDataUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return SchoolTrendDashboardResponse(
        urn=result.urn,
        years_available=list(result.years_available),
        sections=[
            SchoolTrendDashboardSectionResponse(
                key=section.key,
                metrics=[
                    SchoolTrendDashboardMetricResponse(
                        metric_key=metric.metric_key,
                        label=metric.label,
                        unit=metric.unit,
                        points=[
                            SchoolTrendBenchmarkPointResponse(**point.__dict__)
                            for point in metric.points
                        ],
                    )
                    for metric in section.metrics
                ],
            )
            for section in result.sections
        ],
        completeness=SchoolTrendsCompletenessResponse(
            status=result.completeness.status,
            reason_code=result.completeness.reason_code,
            last_updated_at=result.completeness.last_updated_at,
            years_available=(
                list(result.completeness.years_available)
                if result.completeness.years_available is not None
                else None
            ),
        ),
    )
