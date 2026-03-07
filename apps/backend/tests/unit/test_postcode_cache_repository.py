from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from civitas.domain.schools.models import PostcodeCoordinates
from civitas.infrastructure.persistence.postgres_postcode_cache_repository import (
    PostgresPostcodeCacheRepository,
)


def _create_engine_with_cache_table() -> Engine:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE postcode_cache (
                    postcode text PRIMARY KEY,
                    lat double precision NOT NULL,
                    lng double precision NOT NULL,
                    lsoa_code text NULL,
                    lsoa text NULL,
                    admin_district text NULL,
                    cached_at timestamp NOT NULL
                )
                """
            )
        )
    return engine


def test_postcode_cache_repository_returns_hit_only_when_fresh() -> None:
    engine = _create_engine_with_cache_table()
    repository = PostgresPostcodeCacheRepository(engine=engine)
    now = datetime(2026, 2, 28, 12, 0, tzinfo=timezone.utc)
    coordinates = PostcodeCoordinates(
        postcode="SW1A 1AA",
        lat=51.501009,
        lng=-0.141588,
        lsoa_code="E01004736",
        lsoa="Westminster 018B",
        admin_district="Westminster",
    )

    repository.upsert(coordinates=coordinates, cached_at=now - timedelta(days=1))

    hit = repository.get_fresh(
        postcode="SW1A 1AA",
        ttl=timedelta(days=30),
        now=now,
    )
    assert hit is not None
    assert hit.postcode == "SW1A 1AA"
    assert hit.lat == 51.501009
    assert hit.lsoa_code == "E01004736"

    stale_miss = repository.get_fresh(
        postcode="SW1A 1AA",
        ttl=timedelta(hours=6),
        now=now,
    )
    assert stale_miss is None

    stale_hit = repository.get_any(postcode="SW1A 1AA")
    assert stale_hit is not None
    assert stale_hit.postcode == "SW1A 1AA"
    assert stale_hit.lsoa_code == "E01004736"

    engine.dispose()


def test_postcode_cache_repository_upsert_replaces_existing_value() -> None:
    engine = _create_engine_with_cache_table()
    repository = PostgresPostcodeCacheRepository(engine=engine)
    now = datetime(2026, 2, 28, 12, 0, tzinfo=timezone.utc)

    repository.upsert(
        coordinates=PostcodeCoordinates(
            postcode="SW1A 1AA",
            lat=51.501009,
            lng=-0.141588,
            lsoa_code=None,
            lsoa=None,
            admin_district=None,
        ),
        cached_at=now - timedelta(days=2),
    )
    repository.upsert(
        coordinates=PostcodeCoordinates(
            postcode="SW1A 1AA",
            lat=51.501999,
            lng=-0.140000,
            lsoa_code="E01004736",
            lsoa="Westminster 018B",
            admin_district="Westminster",
        ),
        cached_at=now,
    )

    result = repository.get_fresh(
        postcode="SW1A 1AA",
        ttl=timedelta(days=30),
        now=now,
    )
    assert result is not None
    assert result.lat == 51.501999
    assert result.lng == -0.14
    assert result.lsoa_code == "E01004736"
    assert result.admin_district == "Westminster"

    engine.dispose()
