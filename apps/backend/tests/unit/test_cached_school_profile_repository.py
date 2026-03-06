from __future__ import annotations

from dataclasses import dataclass

from civitas.domain.school_profiles.models import (
    SchoolAreaContext,
    SchoolAreaContextCoverage,
    SchoolProfile,
    SchoolProfileCompleteness,
    SchoolProfileSchool,
    SchoolProfileSectionCompleteness,
)
from civitas.infrastructure.persistence.cached_school_profile_repository import (
    CachedSchoolProfileRepository,
)


def _profile(urn: str, *, name: str = "Example School") -> SchoolProfile:
    unavailable = SchoolProfileSectionCompleteness(
        status="unavailable",
        reason_code="source_missing",
        last_updated_at=None,
        years_available=None,
    )
    return SchoolProfile(
        school=SchoolProfileSchool(
            urn=urn,
            name=name,
            phase="Primary",
            school_type="Academy",
            status="Open",
            postcode="SW1A 1AA",
            website=None,
            telephone=None,
            head_title=None,
            head_first_name=None,
            head_last_name=None,
            head_job_title=None,
            address_street=None,
            address_locality=None,
            address_line3=None,
            address_town=None,
            address_county=None,
            statutory_low_age=None,
            statutory_high_age=None,
            gender=None,
            religious_character=None,
            diocese=None,
            admissions_policy=None,
            sixth_form=None,
            nursery_provision=None,
            boarders=None,
            fsm_pct_gias=None,
            trust_name=None,
            trust_flag=None,
            federation_name=None,
            federation_flag=None,
            la_name=None,
            la_code=None,
            urban_rural=None,
            number_of_boys=None,
            number_of_girls=None,
            lsoa_code=None,
            lsoa_name=None,
            last_changed_date=None,
            lat=51.5,
            lng=-0.14,
        ),
        demographics_latest=None,
        attendance_latest=None,
        behaviour_latest=None,
        workforce_latest=None,
        leadership_snapshot=None,
        performance=None,
        ofsted_latest=None,
        ofsted_timeline=None,
        area_context=SchoolAreaContext(
            deprivation=None,
            crime=None,
            house_prices=None,
            coverage=SchoolAreaContextCoverage(
                has_deprivation=False,
                has_crime=False,
                crime_months_available=0,
                has_house_prices=False,
                house_price_months_available=0,
            ),
        ),
        completeness=SchoolProfileCompleteness(
            demographics=unavailable,
            attendance=unavailable,
            behaviour=unavailable,
            workforce=unavailable,
            leadership=unavailable,
            performance=unavailable,
            ofsted_latest=unavailable,
            ofsted_timeline=unavailable,
            area_deprivation=unavailable,
            area_crime=unavailable,
            area_house_prices=unavailable,
        ),
    )


class FakeSchoolProfileRepository:
    def __init__(self, responses: list[SchoolProfile | None]) -> None:
        self._responses = responses
        self.calls: list[str] = []

    def get_school_profile(self, urn: str) -> SchoolProfile | None:
        self.calls.append(urn)
        if len(self._responses) == 0:
            return None
        if len(self._responses) == 1:
            return self._responses[0]
        return self._responses.pop(0)


@dataclass
class FakeVersionProvider:
    tokens: list[str | None]

    def __post_init__(self) -> None:
        self.calls = 0

    def get_school_profile_cache_token(self) -> str | None:
        self.calls += 1
        if len(self.tokens) == 0:
            return None
        if len(self.tokens) == 1:
            return self.tokens[0]
        return self.tokens.pop(0)


@dataclass
class FakeClock:
    current: float = 0.0

    def now(self) -> float:
        return self.current

    def advance(self, seconds: float) -> None:
        self.current += seconds


def test_cached_repository_returns_cached_profile_when_ttl_is_active() -> None:
    delegate = FakeSchoolProfileRepository([_profile("123456")])
    version_provider = FakeVersionProvider(tokens=["v1"])
    clock = FakeClock()
    repository = CachedSchoolProfileRepository(
        delegate=delegate,
        ttl_seconds=300,
        version_provider=version_provider,
        clock=clock.now,
    )

    first = repository.get_school_profile("123456")
    second = repository.get_school_profile("123456")

    assert first is not None
    assert second is not None
    assert first.school.name == "Example School"
    assert second.school.name == "Example School"
    assert delegate.calls == ["123456"]
    assert version_provider.calls >= 2


def test_cached_repository_invalidates_when_version_token_changes() -> None:
    delegate = FakeSchoolProfileRepository(
        [_profile("123456", name="Before refresh"), _profile("123456", name="After refresh")]
    )
    version_provider = FakeVersionProvider(tokens=["v1", "v2"])
    repository = CachedSchoolProfileRepository(
        delegate=delegate,
        ttl_seconds=300,
        version_provider=version_provider,
    )

    first = repository.get_school_profile("123456")
    second = repository.get_school_profile("123456")

    assert first is not None
    assert second is not None
    assert first.school.name == "Before refresh"
    assert second.school.name == "After refresh"
    assert delegate.calls == ["123456", "123456"]


def test_cached_repository_refreshes_after_ttl_expiry() -> None:
    delegate = FakeSchoolProfileRepository(
        [_profile("123456", name="First value"), _profile("123456", name="Second value")]
    )
    clock = FakeClock()
    repository = CachedSchoolProfileRepository(
        delegate=delegate,
        ttl_seconds=60,
        version_provider=FakeVersionProvider(tokens=["v1"]),
        clock=clock.now,
    )

    first = repository.get_school_profile("123456")
    clock.advance(61)
    second = repository.get_school_profile("123456")

    assert first is not None
    assert second is not None
    assert first.school.name == "First value"
    assert second.school.name == "Second value"
    assert delegate.calls == ["123456", "123456"]


def test_cached_repository_can_be_disabled_with_zero_ttl() -> None:
    delegate = FakeSchoolProfileRepository(
        [_profile("123456", name="First value"), _profile("123456", name="Second value")]
    )
    repository = CachedSchoolProfileRepository(
        delegate=delegate,
        ttl_seconds=0,
        version_provider=FakeVersionProvider(tokens=["v1"]),
    )

    first = repository.get_school_profile("123456")
    second = repository.get_school_profile("123456")

    assert first is not None
    assert second is not None
    assert first.school.name == "First value"
    assert second.school.name == "Second value"
    assert delegate.calls == ["123456", "123456"]
