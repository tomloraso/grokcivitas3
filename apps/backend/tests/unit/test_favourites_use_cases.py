from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from civitas.application.access.dto import SectionAccessDto
from civitas.application.favourites.dto import (
    AccountFavouriteSchoolDto,
    PostcodeSchoolSearchAcademicMetricDto,
    PostcodeSchoolSearchLatestOfstedDto,
    SavedSchoolStateDto,
)
from civitas.application.favourites.use_cases import (
    GetSavedSchoolStatesUseCase,
    ListSavedSchoolsUseCase,
    RemoveSavedSchoolUseCase,
    SaveSchoolUseCase,
)
from civitas.domain.favourites.models import SavedSchool, SavedSchoolEvent


class FakeFavouriteRepository:
    def __init__(self) -> None:
        self.saved_by_key: dict[tuple[UUID, str], SavedSchool] = {}
        self.summary_rows: dict[UUID, tuple[AccountFavouriteSchoolDto, ...]] = {}

    def get_saved_school(self, *, user_id: UUID, school_urn: str) -> SavedSchool | None:
        return self.saved_by_key.get((user_id, school_urn))

    def create_saved_school(
        self,
        *,
        user_id: UUID,
        school_urn: str,
        created_at: datetime,
    ) -> SavedSchool:
        saved_school = SavedSchool.create(
            user_id=user_id,
            school_urn=school_urn,
            created_at=created_at,
        )
        self.saved_by_key[(user_id, school_urn)] = saved_school
        return saved_school

    def delete_saved_school(self, *, saved_school_id: UUID) -> None:
        for key, value in tuple(self.saved_by_key.items()):
            if value.id == saved_school_id:
                del self.saved_by_key[key]
                return

    def list_saved_schools(
        self,
        *,
        user_id: UUID,
        school_urns: tuple[str, ...] | None = None,
    ) -> tuple[SavedSchool, ...]:
        rows = tuple(
            saved_school
            for (saved_user_id, _), saved_school in self.saved_by_key.items()
            if saved_user_id == user_id
        )
        if school_urns is None:
            return tuple(sorted(rows, key=lambda row: row.created_at, reverse=True))
        allowed = set(school_urns)
        return tuple(
            sorted(
                (row for row in rows if row.school_urn in allowed),
                key=lambda row: row.created_at,
                reverse=True,
            )
        )

    def list_saved_school_summaries(
        self,
        *,
        user_id: UUID,
    ) -> tuple[AccountFavouriteSchoolDto, ...]:
        return self.summary_rows.get(user_id, ())


class FakeFavouriteEventRepository:
    def __init__(self) -> None:
        self.events: list[SavedSchoolEvent] = []

    def append_event(self, event: SavedSchoolEvent) -> SavedSchoolEvent:
        self.events.append(event)
        return event


class FakeFavouritesAccessResolver:
    def __init__(self, access: SectionAccessDto) -> None:
        self._access = access
        self.calls: list[UUID | None] = []

    def execute(self, *, user_id: UUID | None) -> SectionAccessDto:
        self.calls.append(user_id)
        return self._access


def _timestamp(hour: int) -> datetime:
    return datetime(2026, 3, 10, hour, 0, tzinfo=timezone.utc)


def _summary_row(*, urn: str, name: str, saved_at: datetime) -> AccountFavouriteSchoolDto:
    return AccountFavouriteSchoolDto(
        urn=urn,
        name=name,
        school_type="Community school",
        phase="Primary",
        postcode="SW1A 1AA",
        pupil_count=320,
        latest_ofsted=PostcodeSchoolSearchLatestOfstedDto(
            label="Good",
            sort_rank=2,
            availability="published",
        ),
        academic_metric=PostcodeSchoolSearchAcademicMetricDto(
            metric_key="ks2_combined_expected_pct",
            label="KS2 expected standard",
            display_value="68%",
            sort_value=68.0,
            availability="published",
        ),
        saved_at=saved_at,
    )


def test_save_school_is_idempotent_and_records_only_one_save_event() -> None:
    user_id = uuid4()
    repository = FakeFavouriteRepository()
    event_repository = FakeFavouriteEventRepository()
    access_resolver = FakeFavouritesAccessResolver(
        SectionAccessDto(
            state="available",
            capability_key=None,
            reason_code=None,
            product_codes=(),
            requires_auth=False,
            requires_purchase=False,
        )
    )
    use_case = SaveSchoolUseCase(
        favourite_repository=repository,
        favourite_event_repository=event_repository,
        favourites_access_resolver=access_resolver,
        clock=lambda: _timestamp(9),
    )

    first = use_case.execute(user_id=user_id, school_urn="123456")
    second = use_case.execute(user_id=user_id, school_urn="123456")

    assert first == SavedSchoolStateDto(
        status="saved",
        saved_at=_timestamp(9),
        capability_key=None,
        reason_code=None,
    )
    assert second == first
    assert access_resolver.calls == [user_id, user_id]
    assert len(event_repository.events) == 1
    assert event_repository.events[0].event_type == "saved"


def test_remove_saved_school_is_idempotent_and_records_only_one_remove_event() -> None:
    user_id = uuid4()
    repository = FakeFavouriteRepository()
    repository.create_saved_school(
        user_id=user_id,
        school_urn="123456",
        created_at=_timestamp(9),
    )
    event_repository = FakeFavouriteEventRepository()
    access_resolver = FakeFavouritesAccessResolver(
        SectionAccessDto(
            state="available",
            capability_key=None,
            reason_code=None,
            product_codes=(),
            requires_auth=False,
            requires_purchase=False,
        )
    )
    use_case = RemoveSavedSchoolUseCase(
        favourite_repository=repository,
        favourite_event_repository=event_repository,
        favourites_access_resolver=access_resolver,
        clock=lambda: _timestamp(10),
    )

    first = use_case.execute(user_id=user_id, school_urn="123456")
    second = use_case.execute(user_id=user_id, school_urn="123456")

    assert first == SavedSchoolStateDto(
        status="not_saved",
        saved_at=None,
        capability_key=None,
        reason_code=None,
    )
    assert second == first
    assert len(event_repository.events) == 1
    assert event_repository.events[0].event_type == "removed"


def test_get_saved_school_states_returns_requires_auth_for_anonymous_viewers() -> None:
    repository = FakeFavouriteRepository()
    access_resolver = FakeFavouritesAccessResolver(
        SectionAccessDto(
            state="locked",
            capability_key=None,
            reason_code="anonymous_user",
            product_codes=(),
            requires_auth=True,
            requires_purchase=False,
        )
    )
    use_case = GetSavedSchoolStatesUseCase(
        favourite_repository=repository,
        favourites_access_resolver=access_resolver,
    )

    result = use_case.execute(
        user_id=None,
        school_urns=("123456", "654321"),
    )

    assert result == {
        "123456": SavedSchoolStateDto(
            status="requires_auth",
            saved_at=None,
            capability_key=None,
            reason_code="anonymous_user",
        ),
        "654321": SavedSchoolStateDto(
            status="requires_auth",
            saved_at=None,
            capability_key=None,
            reason_code="anonymous_user",
        ),
    }


def test_get_saved_school_states_returns_locked_when_capability_is_missing() -> None:
    user_id = uuid4()
    repository = FakeFavouriteRepository()
    access_resolver = FakeFavouritesAccessResolver(
        SectionAccessDto(
            state="locked",
            capability_key="premium_favourites",
            reason_code="premium_capability_missing",
            product_codes=("premium_launch",),
            requires_auth=False,
            requires_purchase=True,
        )
    )
    use_case = GetSavedSchoolStatesUseCase(
        favourite_repository=repository,
        favourites_access_resolver=access_resolver,
    )

    result = use_case.execute(
        user_id=user_id,
        school_urns=("123456",),
    )

    assert result == {
        "123456": SavedSchoolStateDto(
            status="locked",
            saved_at=None,
            capability_key="premium_favourites",
            reason_code="premium_capability_missing",
        )
    }


def test_list_saved_schools_returns_latest_saved_first() -> None:
    user_id = uuid4()
    repository = FakeFavouriteRepository()
    repository.summary_rows[user_id] = (
        _summary_row(urn="654321", name="Second School", saved_at=_timestamp(11)),
        _summary_row(urn="123456", name="First School", saved_at=_timestamp(12)),
    )
    access_resolver = FakeFavouritesAccessResolver(
        SectionAccessDto(
            state="available",
            capability_key=None,
            reason_code=None,
            product_codes=(),
            requires_auth=False,
            requires_purchase=False,
        )
    )
    use_case = ListSavedSchoolsUseCase(
        favourite_repository=repository,
        favourites_access_resolver=access_resolver,
    )

    result = use_case.execute(user_id=user_id)

    assert result.access.state == "available"
    assert [school.urn for school in result.schools] == ["654321", "123456"]
    assert result.count == 2
