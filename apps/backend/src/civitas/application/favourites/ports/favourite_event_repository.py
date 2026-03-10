from typing import Protocol

from civitas.domain.favourites.models import SavedSchoolEvent


class FavouriteEventRepository(Protocol):
    def append_event(self, event: SavedSchoolEvent) -> SavedSchoolEvent: ...
