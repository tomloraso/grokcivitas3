from collections.abc import Sequence
from typing import Protocol

from bootstrap_app.domain.tasks.models import Task


class TaskRepository(Protocol):
    def add(self, task: Task) -> Task: ...

    def list_all(self) -> Sequence[Task]: ...
