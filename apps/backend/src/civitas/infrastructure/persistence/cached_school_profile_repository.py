from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Protocol

from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine

from civitas.application.school_profiles.ports.school_profile_repository import (
    SchoolProfileRepository,
)
from civitas.domain.school_profiles.models import SchoolProfile

_SCHOOL_PROFILE_CACHE_KEY = "school_profile"


class SchoolProfileCacheVersionProvider(Protocol):
    def get_school_profile_cache_token(self) -> str | None: ...


@dataclass(frozen=True)
class _CacheEntry:
    profile: SchoolProfile | None
    expires_at: float


class PostgresSchoolProfileCacheVersionProvider(SchoolProfileCacheVersionProvider):
    def __init__(
        self,
        *,
        engine: Engine,
        poll_interval_seconds: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if poll_interval_seconds <= 0:
            raise ValueError("poll_interval_seconds must be greater than 0.")
        self._engine = engine
        self._poll_interval_seconds = poll_interval_seconds
        self._clock = clock
        self._lock = threading.Lock()
        self._cached_token: str | None = None
        self._next_refresh_at = 0.0

    def get_school_profile_cache_token(self) -> str | None:
        now = self._clock()
        with self._lock:
            if now < self._next_refresh_at:
                return self._cached_token
            self._cached_token = self._load_token()
            self._next_refresh_at = now + self._poll_interval_seconds
            return self._cached_token

    def _load_token(self) -> str | None:
        with self._engine.connect() as connection:
            if not _table_exists(connection, "app_cache_versions"):
                return None
            raw_token = connection.execute(
                text(
                    """
                    SELECT version_updated_at
                    FROM app_cache_versions
                    WHERE cache_key = :cache_key
                    LIMIT 1
                    """
                ),
                {"cache_key": _SCHOOL_PROFILE_CACHE_KEY},
            ).scalar_one_or_none()
        if raw_token is None:
            return None
        if isinstance(raw_token, datetime):
            return raw_token.isoformat()
        if isinstance(raw_token, str):
            return raw_token
        return str(raw_token)


class CachedSchoolProfileRepository(SchoolProfileRepository):
    def __init__(
        self,
        *,
        delegate: SchoolProfileRepository,
        ttl_seconds: int,
        version_provider: SchoolProfileCacheVersionProvider | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if ttl_seconds < 0:
            raise ValueError("ttl_seconds must be greater than or equal to 0.")
        self._delegate = delegate
        self._ttl_seconds = float(ttl_seconds)
        self._version_provider = version_provider
        self._clock = clock
        self._lock = threading.RLock()
        self._entries: dict[str, _CacheEntry] = {}
        self._last_seen_token: str | None = None

    def get_school_profile(self, urn: str) -> SchoolProfile | None:
        if self._ttl_seconds == 0:
            return self._delegate.get_school_profile(urn)

        version_token = (
            self._version_provider.get_school_profile_cache_token()
            if self._version_provider is not None
            else None
        )
        now = self._clock()

        with self._lock:
            if version_token != self._last_seen_token:
                self._entries.clear()
                self._last_seen_token = version_token

            cached = self._entries.get(urn)
            if cached is not None and cached.expires_at > now:
                return cached.profile
            if cached is not None:
                self._entries.pop(urn, None)

        profile = self._delegate.get_school_profile(urn)

        with self._lock:
            self._entries[urn] = _CacheEntry(
                profile=profile,
                expires_at=now + self._ttl_seconds,
            )
        return profile


def _table_exists(connection: Connection, table_name: str) -> bool:
    if connection.dialect.name == "postgresql":
        return bool(
            connection.execute(
                text("SELECT to_regclass(:table_name) IS NOT NULL"),
                {"table_name": table_name},
            ).scalar_one()
        )
    if connection.dialect.name == "sqlite":
        row = connection.execute(
            text(
                """
                SELECT 1
                FROM sqlite_master
                WHERE type = 'table' AND name = :table_name
                LIMIT 1
                """
            ),
            {"table_name": table_name},
        ).fetchone()
        return row is not None
    return False
