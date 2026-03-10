from typing import Protocol
from uuid import UUID

from civitas.application.access.dto import SectionAccessDto


class FavouritesAccessResolver(Protocol):
    def execute(self, *, user_id: UUID | None) -> SectionAccessDto: ...
