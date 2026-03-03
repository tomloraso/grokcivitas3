from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError

from civitas.domain.schools.models import PostcodeCoordinates


class PostgresPostcodeCacheRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def get_fresh(
        self,
        *,
        postcode: str,
        ttl: timedelta,
        now: datetime | None = None,
    ) -> PostcodeCoordinates | None:
        reference_time = now or datetime.now(timezone.utc)
        fresh_after = reference_time - ttl

        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    text(
                        """
                    SELECT
                        postcode,
                        lat,
                        lng,
                        lsoa_code,
                        lsoa,
                        admin_district
                    FROM postcode_cache
                    WHERE postcode = :postcode
                      AND cached_at >= :fresh_after
                    """
                    ),
                    {
                        "postcode": postcode,
                        "fresh_after": fresh_after,
                    },
                )
                .mappings()
                .first()
            )

        if row is None:
            return None

        return PostcodeCoordinates(
            postcode=str(row["postcode"]),
            lat=float(row["lat"]),
            lng=float(row["lng"]),
            lsoa=str(row["lsoa"]) if row["lsoa"] is not None else None,
            admin_district=(
                str(row["admin_district"]) if row["admin_district"] is not None else None
            ),
            lsoa_code=str(row["lsoa_code"]) if row["lsoa_code"] is not None else None,
        )

    def upsert(
        self, *, coordinates: PostcodeCoordinates, cached_at: datetime | None = None
    ) -> None:
        cached_timestamp = cached_at or datetime.now(timezone.utc)
        params = {
            "postcode": coordinates.postcode,
            "lat": coordinates.lat,
            "lng": coordinates.lng,
            "lsoa_code": coordinates.lsoa_code,
            "lsoa": coordinates.lsoa,
            "admin_district": coordinates.admin_district,
            "cached_at": cached_timestamp,
        }

        with self._engine.begin() as connection:
            updated = connection.execute(
                text(
                    """
                    UPDATE postcode_cache
                    SET
                        lat = :lat,
                        lng = :lng,
                        lsoa_code = :lsoa_code,
                        lsoa = :lsoa,
                        admin_district = :admin_district,
                        cached_at = :cached_at
                    WHERE postcode = :postcode
                    """
                ),
                params,
            )
            if updated.rowcount and updated.rowcount > 0:
                return

            try:
                connection.execute(
                    text(
                        """
                        INSERT INTO postcode_cache (
                            postcode,
                            lat,
                            lng,
                            lsoa_code,
                            lsoa,
                            admin_district,
                            cached_at
                        ) VALUES (
                            :postcode,
                            :lat,
                            :lng,
                            :lsoa_code,
                            :lsoa,
                            :admin_district,
                            :cached_at
                        )
                        """
                    ),
                    params,
                )
            except IntegrityError:
                connection.execute(
                    text(
                        """
                        UPDATE postcode_cache
                        SET
                            lat = :lat,
                            lng = :lng,
                            lsoa_code = :lsoa_code,
                            lsoa = :lsoa,
                            admin_district = :admin_district,
                            cached_at = :cached_at
                        WHERE postcode = :postcode
                        """
                    ),
                    params,
                )
