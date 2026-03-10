from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID, uuid4

SavedSchoolEventType = Literal["saved", "removed"]


def _normalize_school_urn(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError("school urn must not be blank")
    return normalized


@dataclass(frozen=True)
class SavedSchool:
    id: UUID
    user_id: UUID
    school_urn: str
    created_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "school_urn", _normalize_school_urn(self.school_urn))

    @classmethod
    def create(
        cls,
        *,
        user_id: UUID,
        school_urn: str,
        created_at: datetime,
    ) -> "SavedSchool":
        return cls(
            id=uuid4(),
            user_id=user_id,
            school_urn=school_urn,
            created_at=created_at,
        )


@dataclass(frozen=True)
class SavedSchoolEvent:
    id: UUID
    user_id: UUID
    school_urn: str
    event_type: SavedSchoolEventType
    occurred_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "school_urn", _normalize_school_urn(self.school_urn))

    @classmethod
    def saved(
        cls,
        *,
        user_id: UUID,
        school_urn: str,
        occurred_at: datetime,
    ) -> "SavedSchoolEvent":
        return cls(
            id=uuid4(),
            user_id=user_id,
            school_urn=school_urn,
            event_type="saved",
            occurred_at=occurred_at,
        )

    @classmethod
    def removed(
        cls,
        *,
        user_id: UUID,
        school_urn: str,
        occurred_at: datetime,
    ) -> "SavedSchoolEvent":
        return cls(
            id=uuid4(),
            user_id=user_id,
            school_urn=school_urn,
            event_type="removed",
            occurred_at=occurred_at,
        )
