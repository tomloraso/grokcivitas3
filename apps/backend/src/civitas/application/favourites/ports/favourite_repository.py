from datetime import datetime
from typing import Protocol
from uuid import UUID

from civitas.application.favourites.dto import AccountFavouriteSchoolDto
from civitas.domain.favourites.models import SavedSchool


class FavouriteRepository(Protocol):
    def get_saved_school(self, *, user_id: UUID, school_urn: str) -> SavedSchool | None: ...

    def create_saved_school(
        self,
        *,
        user_id: UUID,
        school_urn: str,
        created_at: datetime,
    ) -> SavedSchool: ...

    def delete_saved_school(self, *, saved_school_id: UUID) -> None: ...

    def list_saved_schools(
        self,
        *,
        user_id: UUID,
        school_urns: tuple[str, ...] | None = None,
    ) -> tuple[SavedSchool, ...]: ...

    def list_saved_school_summaries(
        self,
        *,
        user_id: UUID,
    ) -> tuple[AccountFavouriteSchoolDto, ...]: ...
