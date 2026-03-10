from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Engine, RowMapping

from civitas.application.schools.dto import (
    PostcodeSchoolSearchAcademicMetricDto,
    PostcodeSchoolSearchItemDto,
    PostcodeSchoolSearchLatestOfstedDto,
    SchoolNameSearchItemDto,
)
from civitas.application.schools.ports.school_search_repository import SchoolSearchRepository
from civitas.application.schools.ports.school_search_summary_materializer import (
    SchoolSearchSummaryMaterializer,
)

METERS_PER_MILE = 1609.344
PRIMARY_FAMILY_PHASES = ("Primary", "Middle deemed primary")
SECONDARY_FAMILY_PHASES = ("Secondary", "Middle deemed secondary")
PRIMARY_METRIC_KEY = "ks2_combined_expected_pct"
PRIMARY_METRIC_LABEL = "KS2 expected standard"
SECONDARY_METRIC_KEY = "progress8_average"
SECONDARY_METRIC_LABEL = "Progress 8"


class PostgresSchoolSearchRepository(SchoolSearchRepository, SchoolSearchSummaryMaterializer):
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def materialize_all_search_summaries(self) -> int:
        with self._engine.begin() as connection:
            connection.execute(text("DELETE FROM school_search_summary"))
            connection.execute(
                text(
                    f"""
                    WITH latest_performance AS (
                        SELECT DISTINCT ON (urn)
                            urn,
                            academic_year,
                            progress8_average,
                            ks2_combined_expected_pct
                        FROM school_performance_yearly
                        ORDER BY urn, academic_year DESC
                    )
                    INSERT INTO school_search_summary (
                        urn,
                        name,
                        phase,
                        type,
                        postcode,
                        location,
                        pupil_count,
                        latest_ofsted_label,
                        latest_ofsted_sort_rank,
                        latest_ofsted_availability,
                        primary_academic_metric_key,
                        primary_academic_metric_label,
                        primary_academic_metric_value,
                        primary_academic_metric_availability,
                        secondary_academic_metric_key,
                        secondary_academic_metric_label,
                        secondary_academic_metric_value,
                        secondary_academic_metric_availability
                    )
                    SELECT
                        schools.urn,
                        schools.name,
                        schools.phase,
                        schools.type,
                        schools.postcode,
                        schools.location,
                        schools.pupil_count,
                        school_ofsted_latest.overall_effectiveness_label,
                        CASE school_ofsted_latest.overall_effectiveness_code
                            WHEN '1' THEN 1
                            WHEN '2' THEN 2
                            WHEN '3' THEN 3
                            WHEN '4' THEN 4
                            ELSE NULL
                        END,
                        CASE
                            WHEN school_ofsted_latest.overall_effectiveness_label IS NOT NULL
                                THEN 'published'
                            ELSE 'not_published'
                        END,
                        '{PRIMARY_METRIC_KEY}',
                        '{PRIMARY_METRIC_LABEL}',
                        latest_performance.ks2_combined_expected_pct,
                        CASE
                            WHEN schools.phase IN ('Primary', 'Middle deemed primary', 'All-through')
                                 AND latest_performance.ks2_combined_expected_pct IS NOT NULL
                                THEN 'published'
                            WHEN schools.phase IN ('Primary', 'Middle deemed primary', 'All-through')
                                THEN 'not_published'
                            ELSE 'unsupported'
                        END,
                        '{SECONDARY_METRIC_KEY}',
                        '{SECONDARY_METRIC_LABEL}',
                        latest_performance.progress8_average,
                        CASE
                            WHEN schools.phase IN ('Secondary', 'Middle deemed secondary', 'All-through')
                                 AND latest_performance.progress8_average IS NOT NULL
                                THEN 'published'
                            WHEN schools.phase IN ('Secondary', 'Middle deemed secondary', 'All-through')
                                THEN 'not_published'
                            ELSE 'unsupported'
                        END
                    FROM schools
                    LEFT JOIN school_ofsted_latest
                        ON school_ofsted_latest.urn = schools.urn
                    LEFT JOIN latest_performance
                        ON latest_performance.urn = schools.urn
                    WHERE LOWER(COALESCE(schools.status, '')) LIKE 'open%'
                    """
                )
            )

            return int(
                connection.execute(text("SELECT count(*) FROM school_search_summary")).scalar_one()
            )

    def search_within_radius(
        self,
        *,
        center_lat: float,
        center_lng: float,
        radius_miles: float,
        phase_filters: tuple[str, ...],
        sort: str,
    ) -> tuple[PostcodeSchoolSearchItemDto, ...]:
        radius_meters = radius_miles * METERS_PER_MILE
        effective_family = _effective_phase_family(phase_filters)
        phase_clause = _phase_filter_clause(phase_filters)
        metric_columns = _academic_metric_projection_columns(effective_family)
        order_by_clause = _order_by_clause(sort)

        with self._engine.connect() as connection:
            rows = connection.execute(
                text(
                    f"""
                    WITH candidates AS (
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
                            ) / :meters_per_mile AS distance_miles,
                            pupil_count,
                            latest_ofsted_label,
                            latest_ofsted_sort_rank,
                            latest_ofsted_availability,
                            {metric_columns}
                        FROM school_search_summary
                        WHERE ST_DWithin(
                            location,
                            ST_SetSRID(ST_MakePoint(:center_lng, :center_lat), 4326)::geography,
                            :radius_meters
                        )
                        {phase_clause}
                    )
                    SELECT *
                    FROM candidates
                    ORDER BY {order_by_clause}
                    """
                ),
                {
                    "center_lat": center_lat,
                    "center_lng": center_lng,
                    "radius_meters": radius_meters,
                    "meters_per_mile": METERS_PER_MILE,
                },
            ).mappings()

            return tuple(_map_postcode_search_row(row) for row in rows)

    def search_by_name(
        self,
        *,
        name: str,
        limit: int,
    ) -> tuple[SchoolNameSearchItemDto, ...]:
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
                SchoolNameSearchItemDto(
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


def _effective_phase_family(phase_filters: tuple[str, ...]) -> str | None:
    if len(phase_filters) != 1:
        return None
    return phase_filters[0]


def _phase_filter_clause(phase_filters: tuple[str, ...]) -> str:
    if len(phase_filters) == 0:
        return ""

    clauses: list[str] = []
    if "primary" in phase_filters:
        clauses.append(
            """
            (
                phase IN ('Primary', 'Middle deemed primary')
                OR (
                    phase = 'All-through'
                    AND primary_academic_metric_availability = 'published'
                )
            )
            """
        )
    if "secondary" in phase_filters:
        clauses.append(
            """
            (
                phase IN ('Secondary', 'Middle deemed secondary')
                OR (
                    phase = 'All-through'
                    AND secondary_academic_metric_availability = 'published'
                )
            )
            """
        )

    return "AND (" + " OR ".join(clause.strip() for clause in clauses) + ")"


def _academic_metric_projection_columns(effective_family: str | None) -> str:
    if effective_family == "primary":
        return """
            primary_academic_metric_key AS academic_metric_key,
            primary_academic_metric_label AS academic_metric_label,
            primary_academic_metric_value AS academic_metric_value,
            primary_academic_metric_availability AS academic_metric_availability
        """
    if effective_family == "secondary":
        return """
            secondary_academic_metric_key AS academic_metric_key,
            secondary_academic_metric_label AS academic_metric_label,
            secondary_academic_metric_value AS academic_metric_value,
            secondary_academic_metric_availability AS academic_metric_availability
        """

    return """
        CASE
            WHEN phase IN ('Primary', 'Middle deemed primary', 'All-through')
                THEN primary_academic_metric_key
            WHEN phase IN ('Secondary', 'Middle deemed secondary')
                THEN secondary_academic_metric_key
            WHEN secondary_academic_metric_availability <> 'unsupported'
                THEN secondary_academic_metric_key
            ELSE primary_academic_metric_key
        END AS academic_metric_key,
        CASE
            WHEN phase IN ('Primary', 'Middle deemed primary', 'All-through')
                THEN primary_academic_metric_label
            WHEN phase IN ('Secondary', 'Middle deemed secondary')
                THEN secondary_academic_metric_label
            WHEN secondary_academic_metric_availability <> 'unsupported'
                THEN secondary_academic_metric_label
            ELSE primary_academic_metric_label
        END AS academic_metric_label,
        CASE
            WHEN phase IN ('Primary', 'Middle deemed primary', 'All-through')
                THEN primary_academic_metric_value
            WHEN phase IN ('Secondary', 'Middle deemed secondary')
                THEN secondary_academic_metric_value
            WHEN secondary_academic_metric_availability <> 'unsupported'
                THEN secondary_academic_metric_value
            ELSE primary_academic_metric_value
        END AS academic_metric_value,
        CASE
            WHEN phase IN ('Primary', 'Middle deemed primary', 'All-through')
                THEN primary_academic_metric_availability
            WHEN phase IN ('Secondary', 'Middle deemed secondary')
                THEN secondary_academic_metric_availability
            WHEN secondary_academic_metric_availability <> 'unsupported'
                THEN secondary_academic_metric_availability
            ELSE primary_academic_metric_availability
        END AS academic_metric_availability
    """


def _order_by_clause(sort: str) -> str:
    if sort == "ofsted":
        return "COALESCE(latest_ofsted_sort_rank, 999) ASC, distance_miles ASC, urn ASC"
    if sort == "academic":
        return "academic_metric_value DESC NULLS LAST, distance_miles ASC, urn ASC"
    return "distance_miles ASC, urn ASC"


def _map_postcode_search_row(row: RowMapping) -> PostcodeSchoolSearchItemDto:
    mapping = dict(row)
    metric_key = _optional_text(mapping.get("academic_metric_key"))
    metric_value = _optional_float(mapping.get("academic_metric_value"))
    return PostcodeSchoolSearchItemDto(
        urn=str(mapping["urn"]),
        name=str(mapping["name"]),
        school_type=_optional_text(mapping.get("type")),
        phase=_optional_text(mapping.get("phase")),
        postcode=_optional_text(mapping.get("postcode")),
        lat=float(mapping["lat"]),
        lng=float(mapping["lng"]),
        distance_miles=float(mapping["distance_miles"]),
        pupil_count=_optional_int(mapping.get("pupil_count")),
        latest_ofsted=PostcodeSchoolSearchLatestOfstedDto(
            label=_optional_text(mapping.get("latest_ofsted_label")),
            sort_rank=_optional_int(mapping.get("latest_ofsted_sort_rank")),
            availability=str(mapping["latest_ofsted_availability"]),
        ),
        academic_metric=PostcodeSchoolSearchAcademicMetricDto(
            metric_key=metric_key,
            label=_optional_text(mapping.get("academic_metric_label")),
            display_value=_format_academic_metric(metric_key, metric_value),
            sort_value=metric_value,
            availability=str(mapping["academic_metric_availability"]),
        ),
    )


def _format_academic_metric(metric_key: str | None, value: float | None) -> str | None:
    if metric_key is None or value is None:
        return None
    if metric_key == PRIMARY_METRIC_KEY:
        return f"{_format_number(value)}%"
    return _format_number(value)


def _format_number(value: float) -> str:
    text_value = f"{value:.2f}".rstrip("0").rstrip(".")
    return text_value if text_value != "-0" else "0"


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return int(str(value))


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return float(int(value))
    if isinstance(value, (int, float)):
        return float(value)
    return float(str(value))
