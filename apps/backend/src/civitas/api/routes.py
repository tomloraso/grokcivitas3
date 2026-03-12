from collections.abc import Sequence

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from civitas.api.dependencies import (
    get_create_task_use_case,
    get_list_tasks_use_case,
    get_optional_session_user,
    get_school_compare_use_case,
    get_school_profile_use_case,
    get_school_trend_dashboard_use_case,
    get_school_trends_use_case,
    get_search_schools_by_name_use_case,
    get_search_schools_by_postcode_use_case,
)
from civitas.api.favourites_presenter import to_saved_school_state_response
from civitas.api.schemas.school_compare import SchoolCompareResponse
from civitas.api.schemas.school_profiles import SchoolProfileResponse
from civitas.api.schemas.school_trends import (
    SchoolBenchmarkContextResponse,
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
from civitas.api.school_profile_presenter import to_school_profile_response
from civitas.api.subject_performance_presenter import (
    to_subject_performance_series_response,
)
from civitas.application.identity.dto import SessionUserDto
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
from civitas.application.school_trends.dto import (
    SchoolTrendBenchmarkPointDto,
    SchoolTrendPointDto,
    SchoolTrendsBenchmarksDto,
    SchoolTrendsCompletenessDto,
    SchoolTrendsSeriesDto,
)
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
    viewer: SessionUserDto | None = Depends(get_optional_session_user),
    use_case: SearchSchoolsByPostcodeUseCase = Depends(get_search_schools_by_postcode_use_case),
) -> SchoolsSearchResponse:
    try:
        result = use_case.execute(
            postcode=postcode,
            radius_miles=radius,
            phases=tuple(phase) if phase is not None else None,
            sort=sort,
            viewer_user_id=viewer.id if viewer is not None else None,
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
                saved_state=to_saved_school_state_response(school.saved_state),
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
    viewer: SessionUserDto | None = Depends(get_optional_session_user),
    use_case: SearchSchoolsByNameUseCase = Depends(get_search_schools_by_name_use_case),
) -> SchoolNameSearchResponse:
    try:
        result = use_case.execute(
            name=name,
            viewer_user_id=viewer.id if viewer is not None else None,
        )
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
                saved_state=to_saved_school_state_response(school.saved_state),
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
    response: Response,
    urns: str | None = Query(default=None),
    viewer: SessionUserDto | None = Depends(get_optional_session_user),
    use_case: GetSchoolCompareUseCase = Depends(get_school_compare_use_case),
) -> SchoolCompareResponse:
    try:
        result = use_case.execute(
            urns=urns or "",
            viewer_user_id=viewer.id if viewer is not None else None,
        )
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
    response: Response,
    urn: str,
    viewer: SessionUserDto | None = Depends(get_optional_session_user),
    use_case: GetSchoolProfileUseCase = Depends(get_school_profile_use_case),
) -> SchoolProfileResponse:
    try:
        result = use_case.execute(
            urn=urn,
            viewer_user_id=viewer.id if viewer is not None else None,
        )
    except SchoolProfileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SchoolProfileDataUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return to_school_profile_response(result)


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
        series=_to_school_trends_series_response(result.series),
        benchmarks=_to_school_trends_benchmarks_response(result.benchmarks),
        completeness=_to_school_trends_completeness_response(result.completeness),
        section_completeness=SchoolTrendsSectionCompletenessResponse(
            demographics=_to_school_trends_completeness_response(
                result.section_completeness.demographics
            ),
            attendance=_to_school_trends_completeness_response(
                result.section_completeness.attendance
            ),
            behaviour=_to_school_trends_completeness_response(
                result.section_completeness.behaviour
            ),
            workforce=_to_school_trends_completeness_response(
                result.section_completeness.workforce
            ),
            admissions=_to_school_trends_completeness_response(
                result.section_completeness.admissions
            ),
            destinations=_to_school_trends_completeness_response(
                result.section_completeness.destinations
            ),
            finance=_to_school_trends_completeness_response(result.section_completeness.finance),
        ),
        subject_performance=to_subject_performance_series_response(result.subject_performance),
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
                            _to_school_trend_benchmark_point_response(point)
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


def _to_school_trend_point_response(point: SchoolTrendPointDto) -> SchoolTrendPointResponse:
    return SchoolTrendPointResponse(
        academic_year=point.academic_year,
        value=point.value,
        delta=point.delta,
        direction=point.direction,
    )


def _to_school_trend_benchmark_point_response(
    point: SchoolTrendBenchmarkPointDto,
) -> SchoolTrendBenchmarkPointResponse:
    return SchoolTrendBenchmarkPointResponse(
        academic_year=point.academic_year,
        school_value=point.school_value,
        national_value=point.national_value,
        local_value=point.local_value,
        school_vs_national_delta=point.school_vs_national_delta,
        school_vs_local_delta=point.school_vs_local_delta,
        local_scope=point.local_scope,
        local_area_code=point.local_area_code,
        local_area_label=point.local_area_label,
        contexts=[
            SchoolBenchmarkContextResponse(
                scope=context.scope,
                label=context.label,
                value=context.value,
                percentile_rank=context.percentile_rank,
                school_count=context.school_count,
                area_code=context.area_code,
            )
            for context in point.contexts
        ],
    )


def _to_school_trends_series_response(series: SchoolTrendsSeriesDto) -> SchoolTrendsSeriesResponse:
    return SchoolTrendsSeriesResponse(
        **{
            field_name: [
                _to_school_trend_point_response(point) for point in getattr(series, field_name)
            ]
            for field_name in SchoolTrendsSeriesResponse.model_fields
        }
    )


def _to_school_trends_benchmarks_response(
    benchmarks: SchoolTrendsBenchmarksDto,
) -> SchoolTrendsBenchmarksResponse:
    return SchoolTrendsBenchmarksResponse(
        **{
            field_name: [
                _to_school_trend_benchmark_point_response(point)
                for point in getattr(benchmarks, field_name)
            ]
            for field_name in SchoolTrendsBenchmarksResponse.model_fields
        }
    )


def _to_school_trends_completeness_response(
    completeness: SchoolTrendsCompletenessDto,
) -> SchoolTrendsCompletenessResponse:
    years_available = completeness.years_available
    return SchoolTrendsCompletenessResponse(
        status=completeness.status,
        reason_code=completeness.reason_code,
        last_updated_at=completeness.last_updated_at,
        years_available=list(years_available) if years_available is not None else None,
    )
