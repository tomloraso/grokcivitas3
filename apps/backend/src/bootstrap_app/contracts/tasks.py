from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class TaskCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class TaskResponse(BaseModel):
    id: UUID
    title: str
    created_at: datetime
