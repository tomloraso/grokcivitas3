from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Engine

from civitas.application.favourites.ports.favourite_event_repository import (
    FavouriteEventRepository,
)
from civitas.domain.favourites.models import SavedSchoolEvent


class PostgresFavouriteEventRepository(FavouriteEventRepository):
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def append_event(self, event: SavedSchoolEvent) -> SavedSchoolEvent:
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO saved_school_events (
                        id,
                        user_id,
                        school_urn,
                        event_type,
                        occurred_at
                    ) VALUES (
                        :id,
                        :user_id,
                        :school_urn,
                        :event_type,
                        :occurred_at
                    )
                    """
                ),
                {
                    "id": event.id,
                    "user_id": event.user_id,
                    "school_urn": event.school_urn,
                    "event_type": event.event_type,
                    "occurred_at": event.occurred_at,
                },
            )
        return event
