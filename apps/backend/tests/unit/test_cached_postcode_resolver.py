from __future__ import annotations

from datetime import timedelta

from civitas.domain.schools.models import PostcodeCoordinates
from civitas.infrastructure.http.postcode_resolver import CachedPostcodeResolver


class FakePostcodeCacheRepository:
    def __init__(
        self,
        *,
        fresh: PostcodeCoordinates | None,
        stale: PostcodeCoordinates | None = None,
    ) -> None:
        self._fresh = fresh
        self._stale = stale
        self.upserted: list[PostcodeCoordinates] = []
        self.get_fresh_calls: list[tuple[str, timedelta]] = []
        self.get_any_calls: list[str] = []

    def get_fresh(self, *, postcode: str, ttl: timedelta) -> PostcodeCoordinates | None:
        self.get_fresh_calls.append((postcode, ttl))
        return self._fresh

    def get_any(self, *, postcode: str) -> PostcodeCoordinates | None:
        self.get_any_calls.append(postcode)
        return self._stale

    def upsert(self, *, coordinates: PostcodeCoordinates) -> None:
        self.upserted.append(coordinates)


class FakePostcodesIoClient:
    def __init__(self, response: PostcodeCoordinates) -> None:
        self._response = response
        self.lookup_calls: list[str] = []

    def lookup(self, postcode: str) -> PostcodeCoordinates:
        self.lookup_calls.append(postcode)
        return self._response


def test_cached_postcode_resolver_returns_fresh_cache_when_lsoa_code_present() -> None:
    cached = PostcodeCoordinates(
        postcode="SW1A 1AA",
        lat=51.501,
        lng=-0.1416,
        lsoa="Westminster 018C",
        admin_district="Westminster",
        lsoa_code="E01004736",
    )
    cache_repository = FakePostcodeCacheRepository(fresh=cached)
    client = FakePostcodesIoClient(response=cached)
    resolver = CachedPostcodeResolver(
        cache_repository=cache_repository,
        postcodes_io_client=client,
        cache_ttl_days=30,
    )

    result = resolver.resolve("SW1A 1AA")

    assert result == cached
    assert client.lookup_calls == []
    assert cache_repository.get_any_calls == []
    assert cache_repository.upserted == []


def test_cached_postcode_resolver_refreshes_cache_when_lsoa_code_missing() -> None:
    stale_shape = PostcodeCoordinates(
        postcode="SW1A 1AA",
        lat=51.501,
        lng=-0.1416,
        lsoa="Westminster 018C",
        admin_district="Westminster",
        lsoa_code=None,
    )
    refreshed = PostcodeCoordinates(
        postcode="SW1A 1AA",
        lat=51.501,
        lng=-0.1416,
        lsoa="Westminster 018C",
        admin_district="Westminster",
        lsoa_code="E01004736",
    )
    cache_repository = FakePostcodeCacheRepository(fresh=stale_shape)
    client = FakePostcodesIoClient(response=refreshed)
    resolver = CachedPostcodeResolver(
        cache_repository=cache_repository,
        postcodes_io_client=client,
        cache_ttl_days=30,
    )

    result = resolver.resolve("SW1A 1AA")

    assert result == refreshed
    assert client.lookup_calls == ["SW1A 1AA"]
    assert cache_repository.get_any_calls == ["SW1A 1AA"]
    assert cache_repository.upserted == [refreshed]


def test_cached_postcode_resolver_returns_stale_cache_when_lsoa_code_present() -> None:
    stale = PostcodeCoordinates(
        postcode="SW1A 1AA",
        lat=51.501,
        lng=-0.1416,
        lsoa="Westminster 018C",
        admin_district="Westminster",
        lsoa_code="E01004736",
    )
    cache_repository = FakePostcodeCacheRepository(fresh=None, stale=stale)
    client = FakePostcodesIoClient(response=stale)
    resolver = CachedPostcodeResolver(
        cache_repository=cache_repository,
        postcodes_io_client=client,
        cache_ttl_days=30,
    )

    result = resolver.resolve("SW1A 1AA")

    assert result == stale
    assert client.lookup_calls == []
    assert cache_repository.get_any_calls == ["SW1A 1AA"]
    assert cache_repository.upserted == []


def test_cached_postcode_resolver_populates_cache_on_miss() -> None:
    resolved = PostcodeCoordinates(
        postcode="SW1A 1AA",
        lat=51.501,
        lng=-0.1416,
        lsoa="Westminster 018C",
        admin_district="Westminster",
        lsoa_code="E01004736",
    )
    cache_repository = FakePostcodeCacheRepository(fresh=None, stale=None)
    client = FakePostcodesIoClient(response=resolved)
    resolver = CachedPostcodeResolver(
        cache_repository=cache_repository,
        postcodes_io_client=client,
        cache_ttl_days=30,
    )

    result = resolver.resolve("SW1A 1AA")

    assert result == resolved
    assert client.lookup_calls == ["SW1A 1AA"]
    assert cache_repository.get_any_calls == ["SW1A 1AA"]
    assert cache_repository.upserted == [resolved]
