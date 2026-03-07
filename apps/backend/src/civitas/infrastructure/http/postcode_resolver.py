from __future__ import annotations

from datetime import timedelta

from civitas.application.schools.ports.postcode_resolver import PostcodeResolver
from civitas.domain.schools.models import PostcodeCoordinates
from civitas.infrastructure.http.postcodes_io_client import PostcodesIoClient
from civitas.infrastructure.persistence.postgres_postcode_cache_repository import (
    PostgresPostcodeCacheRepository,
)


class CachedPostcodeResolver(PostcodeResolver):
    def __init__(
        self,
        *,
        cache_repository: PostgresPostcodeCacheRepository,
        postcodes_io_client: PostcodesIoClient,
        cache_ttl_days: int,
    ) -> None:
        self._cache_repository = cache_repository
        self._postcodes_io_client = postcodes_io_client
        self._cache_ttl = timedelta(days=cache_ttl_days)

    def resolve(self, postcode: str) -> PostcodeCoordinates:
        cached = self._cache_repository.get_fresh(postcode=postcode, ttl=self._cache_ttl)
        if cached is not None and cached.lsoa_code is not None:
            return cached

        stale = self._cache_repository.get_any(postcode=postcode)
        if stale is not None and stale.lsoa_code is not None:
            return stale

        resolved = self._postcodes_io_client.lookup(postcode)
        self._cache_repository.upsert(coordinates=resolved)
        return resolved
