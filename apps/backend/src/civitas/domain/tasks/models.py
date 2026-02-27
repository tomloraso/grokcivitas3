from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4


@dataclass(frozen=True)
class Task:
    id: UUID
    title: str
    created_at: datetime

    @classmethod
    def create(cls, title: str) -> "Task":
        cleaned = title.strip()
        if not cleaned:
            raise ValueError("Task title must not be empty")
        return cls(id=uuid4(), title=cleaned, created_at=datetime.now(timezone.utc))
