from collections.abc import Sequence

from fastapi import APIRouter, Depends

from bootstrap_app.api.dependencies import get_create_task_use_case, get_list_tasks_use_case
from bootstrap_app.application.tasks.use_cases import CreateTaskUseCase, ListTasksUseCase
from bootstrap_app.contracts.tasks import TaskCreateRequest, TaskResponse

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
