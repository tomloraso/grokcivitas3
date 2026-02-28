from collections.abc import Sequence

from fastapi import APIRouter, Depends, HTTPException, Query

from civitas.api.dependencies import (
    get_create_task_use_case,
    get_list_tasks_use_case,
    get_search_schools_by_postcode_use_case,
)
from civitas.api.schemas.schools import (
    SchoolSearchItemResponse,
    SchoolsSearchCenterResponse,
    SchoolsSearchQueryResponse,
    SchoolsSearchResponse,
)
from civitas.api.schemas.tasks import TaskCreateRequest, TaskResponse
from civitas.application.schools.errors import (
    InvalidSchoolSearchParametersError,
    PostcodeNotFoundError,
    PostcodeResolverUnavailableError,
)
from civitas.application.schools.use_cases import SearchSchoolsByPostcodeUseCase
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
