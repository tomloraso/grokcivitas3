from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from uuid import UUID

from civitas.application.access.dto import SectionAccessDto
from civitas.application.favourites.dto import (
    AccountFavouritesResponseDto,
    SavedSchoolStateDto,
)
from civitas.application.favourites.ports.favourite_event_repository import (
    FavouriteEventRepository,
)
from civitas.application.favourites.ports.favourite_repository import FavouriteRepository
from civitas.application.favourites.ports.favourites_access_resolver import (
    FavouritesAccessResolver,
)
from civitas.domain.favourites.models import SavedSchoolEvent


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


Clock = Callable[[], datetime]


class GetFavouritesAccessUseCase:
    def execute(self, *, user_id: UUID | None) -> SectionAccessDto:
        if user_id is None:
            return SectionAccessDto(
                state="locked",
                capability_key=None,
                reason_code="anonymous_user",
                product_codes=(),
                requires_auth=True,
                requires_purchase=False,
            )
        return SectionAccessDto(
            state="available",
            capability_key=None,
            reason_code=None,
            product_codes=(),
            requires_auth=False,
            requires_purchase=False,
        )


class SaveSchoolUseCase:
    def __init__(
        self,
        *,
        favourite_repository: FavouriteRepository,
        favourite_event_repository: FavouriteEventRepository,
        favourites_access_resolver: FavouritesAccessResolver,
        clock: Clock = _utc_now,
    ) -> None:
        self._favourite_repository = favourite_repository
        self._favourite_event_repository = favourite_event_repository
        self._favourites_access_resolver = favourites_access_resolver
        self._clock = clock

    def execute(self, *, user_id: UUID | None, school_urn: str) -> SavedSchoolStateDto:
        normalized_urn = _normalize_school_urn(school_urn)
        access = self._favourites_access_resolver.execute(user_id=user_id)
        if user_id is None or access.state != "available":
            return _saved_state_from_access(access)

        existing = self._favourite_repository.get_saved_school(
            user_id=user_id,
            school_urn=normalized_urn,
        )
        if existing is not None:
            return SavedSchoolStateDto(
                status="saved",
                saved_at=existing.created_at,
                capability_key=None,
                reason_code=None,
            )

        now = self._clock()
        saved_school = self._favourite_repository.create_saved_school(
            user_id=user_id,
            school_urn=normalized_urn,
            created_at=now,
        )
        self._favourite_event_repository.append_event(
            SavedSchoolEvent.saved(
                user_id=user_id,
                school_urn=normalized_urn,
                occurred_at=now,
            )
        )
        return SavedSchoolStateDto(
            status="saved",
            saved_at=saved_school.created_at,
            capability_key=None,
            reason_code=None,
        )


class RemoveSavedSchoolUseCase:
    def __init__(
        self,
        *,
        favourite_repository: FavouriteRepository,
        favourite_event_repository: FavouriteEventRepository,
        favourites_access_resolver: FavouritesAccessResolver,
        clock: Clock = _utc_now,
    ) -> None:
        self._favourite_repository = favourite_repository
        self._favourite_event_repository = favourite_event_repository
        self._favourites_access_resolver = favourites_access_resolver
        self._clock = clock

    def execute(self, *, user_id: UUID | None, school_urn: str) -> SavedSchoolStateDto:
        normalized_urn = _normalize_school_urn(school_urn)
        access = self._favourites_access_resolver.execute(user_id=user_id)
        if user_id is None or access.state != "available":
            return _saved_state_from_access(access)

        existing = self._favourite_repository.get_saved_school(
            user_id=user_id,
            school_urn=normalized_urn,
        )
        if existing is None:
            return SavedSchoolStateDto(
                status="not_saved",
                saved_at=None,
                capability_key=None,
                reason_code=None,
            )

        self._favourite_repository.delete_saved_school(saved_school_id=existing.id)
        self._favourite_event_repository.append_event(
            SavedSchoolEvent.removed(
                user_id=user_id,
                school_urn=normalized_urn,
                occurred_at=self._clock(),
            )
        )
        return SavedSchoolStateDto(
            status="not_saved",
            saved_at=None,
            capability_key=None,
            reason_code=None,
        )


class ListSavedSchoolsUseCase:
    def __init__(
        self,
        *,
        favourite_repository: FavouriteRepository,
        favourites_access_resolver: FavouritesAccessResolver,
    ) -> None:
        self._favourite_repository = favourite_repository
        self._favourites_access_resolver = favourites_access_resolver

    def execute(self, *, user_id: UUID | None) -> AccountFavouritesResponseDto:
        access = self._favourites_access_resolver.execute(user_id=user_id)
        if user_id is None or access.state != "available":
            return AccountFavouritesResponseDto(access=access, schools=())

        return AccountFavouritesResponseDto(
            access=access,
            schools=self._favourite_repository.list_saved_school_summaries(user_id=user_id),
        )


class GetSavedSchoolStatesUseCase:
    def __init__(
        self,
        *,
        favourite_repository: FavouriteRepository,
        favourites_access_resolver: FavouritesAccessResolver,
    ) -> None:
        self._favourite_repository = favourite_repository
        self._favourites_access_resolver = favourites_access_resolver

    def execute(
        self,
        *,
        user_id: UUID | None,
        school_urns: tuple[str, ...],
    ) -> dict[str, SavedSchoolStateDto]:
        normalized_urns = tuple(dict.fromkeys(_normalize_school_urn(urn) for urn in school_urns))
        if not normalized_urns:
            return {}

        access = self._favourites_access_resolver.execute(user_id=user_id)
        if user_id is None or access.state != "available":
            locked_state = _saved_state_from_access(access)
            return {urn: locked_state for urn in normalized_urns}

        saved_schools = self._favourite_repository.list_saved_schools(
            user_id=user_id,
            school_urns=normalized_urns,
        )
        states = {
            urn: SavedSchoolStateDto(
                status="not_saved",
                saved_at=None,
                capability_key=None,
                reason_code=None,
            )
            for urn in normalized_urns
        }
        for saved_school in saved_schools:
            states[saved_school.school_urn] = SavedSchoolStateDto(
                status="saved",
                saved_at=saved_school.created_at,
                capability_key=None,
                reason_code=None,
            )
        return states


def _normalize_school_urn(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError("school urn must not be blank")
    return normalized


def _saved_state_from_access(access: SectionAccessDto) -> SavedSchoolStateDto:
    if access.requires_auth:
        return SavedSchoolStateDto(
            status="requires_auth",
            saved_at=None,
            capability_key=access.capability_key,
            reason_code=access.reason_code,
        )
    return SavedSchoolStateDto(
        status="locked",
        saved_at=None,
        capability_key=access.capability_key,
        reason_code=access.reason_code,
    )
