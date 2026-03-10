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
            income_per_pupil_gbp=[
                SchoolTrendPointResponse(
                    academic_year=point.academic_year,
                    value=point.value,
                    delta=point.delta,
                    direction=point.direction,
                )
                for point in result.series.income_per_pupil_gbp
            ],
            expenditure_per_pupil_gbp=[
                SchoolTrendPointResponse(
                    academic_year=point.academic_year,
                    value=point.value,
                    delta=point.delta,
                    direction=point.direction,
                )
                for point in result.series.expenditure_per_pupil_gbp
            ],
            staff_costs_pct_of_expenditure=[
                SchoolTrendPointResponse(
                    academic_year=point.academic_year,
                    value=point.value,
                    delta=point.delta,
                    direction=point.direction,
                )
                for point in result.series.staff_costs_pct_of_expenditure
            ],
            revenue_reserve_per_pupil_gbp=[
                SchoolTrendPointResponse(
                    academic_year=point.academic_year,
                    value=point.value,
                    delta=point.delta,
                    direction=point.direction,
                )
                for point in result.series.revenue_reserve_per_pupil_gbp
            ],
            teaching_staff_costs_per_pupil_gbp=[
                SchoolTrendPointResponse(
                    academic_year=point.academic_year,
                    value=point.value,
                    delta=point.delta,
                    direction=point.direction,
                )
                for point in result.series.teaching_staff_costs_per_pupil_gbp
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
            income_per_pupil_gbp=[
                SchoolTrendBenchmarkPointResponse(**point.__dict__)
                for point in result.benchmarks.income_per_pupil_gbp
            ],
            expenditure_per_pupil_gbp=[
                SchoolTrendBenchmarkPointResponse(**point.__dict__)
                for point in result.benchmarks.expenditure_per_pupil_gbp
            ],
            staff_costs_pct_of_expenditure=[
                SchoolTrendBenchmarkPointResponse(**point.__dict__)
                for point in result.benchmarks.staff_costs_pct_of_expenditure
            ],
            revenue_reserve_per_pupil_gbp=[
                SchoolTrendBenchmarkPointResponse(**point.__dict__)
                for point in result.benchmarks.revenue_reserve_per_pupil_gbp
            ],
            teaching_staff_costs_per_pupil_gbp=[
                SchoolTrendBenchmarkPointResponse(**point.__dict__)
                for point in result.benchmarks.teaching_staff_costs_per_pupil_gbp
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
            finance=SchoolTrendsCompletenessResponse(
                status=result.section_completeness.finance.status,
                reason_code=result.section_completeness.finance.reason_code,
                last_updated_at=result.section_completeness.finance.last_updated_at,
                years_available=(
                    list(result.section_completeness.finance.years_available)
                    if result.section_completeness.finance.years_available is not None
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
