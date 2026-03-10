from collections.abc import Mapping
from typing import Protocol
from uuid import UUID

from civitas.application.favourites.dto import SavedSchoolStateDto


class SavedSchoolStateResolver(Protocol):
    def execute(
        self,
        *,
        user_id: UUID | None,
        school_urns: tuple[str, ...],
    ) -> Mapping[str, SavedSchoolStateDto]: ...
