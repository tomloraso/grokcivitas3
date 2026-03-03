from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Engine

from civitas.application.schools.ports.school_search_repository import SchoolSearchRepository
from civitas.domain.schools.models import SchoolSearchResult

METERS_PER_MILE = 1609.344


class PostgresSchoolSearchRepository(SchoolSearchRepository):
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def search_within_radius(
        self,
        *,
        center_lat: float,
        center_lng: float,
        radius_miles: float,
    ) -> tuple[SchoolSearchResult, ...]:
        radius_meters = radius_miles * METERS_PER_MILE
        with self._engine.connect() as connection:
            rows = connection.execute(
                text(
                    """
                    SELECT
                        urn,
                        name,
                        type,
                        phase,
                        postcode,
                        ST_Y(location::geometry) AS lat,
                        ST_X(location::geometry) AS lng,
                        ST_Distance(
                            location,
                            ST_SetSRID(ST_MakePoint(:center_lng, :center_lat), 4326)::geography
                        ) / :meters_per_mile AS distance_miles
                    FROM schools
                    WHERE LOWER(COALESCE(status, '')) LIKE 'open%'
                      AND ST_DWithin(
                            location,
                            ST_SetSRID(ST_MakePoint(:center_lng, :center_lat), 4326)::geography,
                            :radius_meters
                        )
                    ORDER BY distance_miles ASC, urn ASC
                    """
                ),
                {
                    "center_lat": center_lat,
                    "center_lng": center_lng,
                    "radius_meters": radius_meters,
                    "meters_per_mile": METERS_PER_MILE,
                },
            ).mappings()

            return tuple(
                SchoolSearchResult(
                    urn=str(row["urn"]),
                    name=str(row["name"]),
                    school_type=str(row["type"]) if row["type"] is not None else None,
                    phase=str(row["phase"]) if row["phase"] is not None else None,
                    postcode=str(row["postcode"]) if row["postcode"] is not None else None,
                    lat=float(row["lat"]),
                    lng=float(row["lng"]),
                    distance_miles=float(row["distance_miles"]),
                )
                for row in rows
            )

    def search_by_name(
        self,
        *,
        name: str,
        limit: int,
    ) -> tuple[SchoolSearchResult, ...]:
        normalized_name = " ".join(name.split())
        tokens = [token.lower() for token in normalized_name.split(" ") if token]
        if not tokens:
            return ()

        token_conditions = " AND ".join(
            f"LOWER(name) LIKE :token_{index}" for index, _ in enumerate(tokens)
        )

        with self._engine.connect() as connection:
            rows = connection.execute(
                text(
                    """
                    SELECT
                        urn,
                        name,
                        type,
                        phase,
                        postcode,
                        ST_Y(location::geometry) AS lat,
                        ST_X(location::geometry) AS lng
                    FROM schools
                    WHERE LOWER(COALESCE(status, '')) LIKE 'open%'
                      AND """
                    + token_conditions
                    + """
                    ORDER BY
                        CASE
                            WHEN LOWER(name) = LOWER(:exact_name) THEN 0
                            WHEN LOWER(name) LIKE LOWER(:prefix_name) THEN 1
                            WHEN LOWER(name) LIKE LOWER(:word_prefix_name) THEN 2
                            ELSE 3
                        END ASC,
                        POSITION(LOWER(:needle_name) IN LOWER(name)) ASC,
                        LENGTH(name) ASC,
                        urn ASC
                    LIMIT :limit
                    """
                ),
                {
                    "exact_name": normalized_name,
                    "prefix_name": f"{normalized_name}%",
                    "word_prefix_name": f"% {normalized_name}%",
                    "needle_name": normalized_name,
                    "limit": limit,
                    **{f"token_{index}": f"%{token}%" for index, token in enumerate(tokens)},
                },
            ).mappings()

            return tuple(
                SchoolSearchResult(
                    urn=str(row["urn"]),
                    name=str(row["name"]),
                    school_type=str(row["type"]) if row["type"] is not None else None,
                    phase=str(row["phase"]) if row["phase"] is not None else None,
                    postcode=str(row["postcode"]) if row["postcode"] is not None else None,
                    lat=float(row["lat"]),
                    lng=float(row["lng"]),
                    distance_miles=0.0,
                )
                for row in rows
            )
