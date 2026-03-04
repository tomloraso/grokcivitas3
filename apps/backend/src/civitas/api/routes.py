from collections.abc import Sequence

from fastapi import APIRouter, Depends, HTTPException, Query

from civitas.api.dependencies import (
    get_create_task_use_case,
    get_list_tasks_use_case,
    get_school_profile_use_case,
    get_school_trends_use_case,
    get_search_schools_by_name_use_case,
    get_search_schools_by_postcode_use_case,
)
from civitas.api.schemas.school_profiles import (
    SchoolProfileAreaContextCoverageResponse,
    SchoolProfileAreaContextResponse,
    SchoolProfileAreaCrimeCategoryResponse,
    SchoolProfileAreaCrimeResponse,
    SchoolProfileAreaDeprivationResponse,
    SchoolProfileCompletenessResponse,
    SchoolProfileDemographicsCoverageResponse,
    SchoolProfileDemographicsLatestResponse,
    SchoolProfileOfstedLatestResponse,
    SchoolProfileOfstedTimelineCoverageResponse,
    SchoolProfileOfstedTimelineEventResponse,
    SchoolProfileOfstedTimelineResponse,
    SchoolProfileResponse,
    SchoolProfileSchoolResponse,
    SchoolProfileSectionCompletenessResponse,
)
from civitas.api.schemas.school_trends import (
    SchoolTrendPointResponse,
    SchoolTrendsCompletenessResponse,
    SchoolTrendsHistoryQualityResponse,
    SchoolTrendsResponse,
    SchoolTrendsSeriesResponse,
)
from civitas.api.schemas.schools import (
    SchoolNameSearchResponse,
    SchoolSearchItemResponse,
    SchoolsSearchCenterResponse,
    SchoolsSearchQueryResponse,
    SchoolsSearchResponse,
)
from civitas.api.schemas.tasks import TaskCreateRequest, TaskResponse
from civitas.application.school_profiles.errors import (
    SchoolProfileDataUnavailableError,
    SchoolProfileNotFoundError,
)
from civitas.application.school_profiles.use_cases import GetSchoolProfileUseCase
from civitas.application.school_trends.errors import (
    SchoolTrendsDataUnavailableError,
    SchoolTrendsNotFoundError,
)
from civitas.application.school_trends.use_cases import GetSchoolTrendsUseCase
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
    use_case: SearchSchoolsByPostcodeUseCase = Depends(get_search_schools_by_postcode_use_case),
) -> SchoolsSearchResponse:
    try:
        result = use_case.execute(postcode=postcode, radius_miles=radius)
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
        ),
        center=SchoolsSearchCenterResponse(
            lat=result.center.lat,
            lng=result.center.lng,
        ),
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
            sen_pct=result.demographics_latest.sen_pct,
            ehcp_pct=result.demographics_latest.ehcp_pct,
            eal_pct=result.demographics_latest.eal_pct,
            first_language_english_pct=result.demographics_latest.first_language_english_pct,
            first_language_unclassified_pct=result.demographics_latest.first_language_unclassified_pct,
            coverage=SchoolProfileDemographicsCoverageResponse(
                fsm_supported=result.demographics_latest.coverage.fsm_supported,
                ethnicity_supported=result.demographics_latest.coverage.ethnicity_supported,
                top_languages_supported=result.demographics_latest.coverage.top_languages_supported,
            ),
        )

    ofsted_latest = None
    if result.ofsted_latest is not None:
        ofsted_latest = SchoolProfileOfstedLatestResponse(
            overall_effectiveness_code=result.ofsted_latest.overall_effectiveness_code,
            overall_effectiveness_label=result.ofsted_latest.overall_effectiveness_label,
            inspection_start_date=result.ofsted_latest.inspection_start_date,
            publication_date=result.ofsted_latest.publication_date,
            is_graded=result.ofsted_latest.is_graded,
            ungraded_outcome=result.ofsted_latest.ungraded_outcome,
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

    deprivation = None
    if result.area_context is not None and result.area_context.deprivation is not None:
        deprivation = SchoolProfileAreaDeprivationResponse(
            lsoa_code=result.area_context.deprivation.lsoa_code,
            imd_decile=result.area_context.deprivation.imd_decile,
            idaci_score=result.area_context.deprivation.idaci_score,
            idaci_decile=result.area_context.deprivation.idaci_decile,
            source_release=result.area_context.deprivation.source_release,
        )

    crime = None
    if result.area_context is not None and result.area_context.crime is not None:
        crime = SchoolProfileAreaCrimeResponse(
            radius_miles=result.area_context.crime.radius_miles,
            latest_month=result.area_context.crime.latest_month,
            total_incidents=result.area_context.crime.total_incidents,
            categories=[
                SchoolProfileAreaCrimeCategoryResponse(
                    category=category.category,
                    incident_count=category.incident_count,
                )
                for category in result.area_context.crime.categories
            ],
        )

    area_context = SchoolProfileAreaContextResponse(
        deprivation=deprivation,
        crime=crime,
        coverage=SchoolProfileAreaContextCoverageResponse(
            has_deprivation=result.area_context.coverage.has_deprivation,
            has_crime=result.area_context.coverage.has_crime,
            crime_months_available=result.area_context.coverage.crime_months_available,
        )
        if result.area_context is not None
        else SchoolProfileAreaContextCoverageResponse(
            has_deprivation=False,
            has_crime=False,
            crime_months_available=0,
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
            lat=result.school.lat,
            lng=result.school.lng,
        ),
        demographics_latest=demographics_latest,
        ofsted_latest=ofsted_latest,
        ofsted_timeline=ofsted_timeline,
        area_context=area_context,
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
    )
