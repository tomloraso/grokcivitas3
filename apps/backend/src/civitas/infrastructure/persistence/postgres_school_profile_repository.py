from __future__ import annotations

from datetime import date

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from civitas.application.school_profiles.errors import SchoolProfileDataUnavailableError
from civitas.application.school_profiles.ports.school_profile_repository import (
    SchoolProfileRepository,
)
from civitas.domain.school_profiles.models import (
    SchoolAreaContext,
    SchoolAreaContextCoverage,
    SchoolAreaCrime,
    SchoolAreaCrimeCategory,
    SchoolAreaDeprivation,
    SchoolDemographicsCoverage,
    SchoolDemographicsLatest,
    SchoolOfstedLatest,
    SchoolOfstedTimeline,
    SchoolOfstedTimelineCoverage,
    SchoolOfstedTimelineEvent,
    SchoolProfile,
    SchoolProfileSchool,
)

HISTORICAL_TIMELINE_BASELINE_DATE = date(2015, 9, 14)
METERS_PER_MILE = 1609.344


class PostgresSchoolProfileRepository(SchoolProfileRepository):
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def get_school_profile(self, urn: str) -> SchoolProfile | None:
        try:
            with self._engine.connect() as connection:
                row = (
                    connection.execute(
                        text(
                            """
                        SELECT
                            schools.urn,
                            schools.name,
                            schools.phase,
                            schools.type,
                            schools.status,
                            schools.postcode,
                            ST_Y(schools.location::geometry) AS lat,
                            ST_X(schools.location::geometry) AS lng,
                            demographics.academic_year,
                            demographics.disadvantaged_pct,
                            demographics.fsm_pct,
                            demographics.sen_pct,
                            demographics.ehcp_pct,
                            demographics.eal_pct,
                            demographics.first_language_english_pct,
                            demographics.first_language_unclassified_pct,
                            demographics.has_ethnicity_data,
                            demographics.has_top_languages_data,
                            ofsted.urn AS ofsted_urn,
                            ofsted.overall_effectiveness_code,
                            ofsted.overall_effectiveness_label,
                            ofsted.inspection_start_date,
                            ofsted.publication_date,
                            ofsted.is_graded,
                            ofsted.ungraded_outcome
                        FROM schools
                        LEFT JOIN LATERAL (
                            SELECT
                                academic_year,
                                disadvantaged_pct,
                                fsm_pct,
                                sen_pct,
                                ehcp_pct,
                                eal_pct,
                                first_language_english_pct,
                                first_language_unclassified_pct,
                                has_ethnicity_data,
                                has_top_languages_data
                            FROM school_demographics_yearly
                            WHERE school_demographics_yearly.urn = schools.urn
                            ORDER BY
                                substring(academic_year from 1 for 4)::integer DESC,
                                academic_year DESC
                            LIMIT 1
                        ) AS demographics ON TRUE
                        LEFT JOIN school_ofsted_latest AS ofsted
                            ON ofsted.urn = schools.urn
                        WHERE schools.urn = :urn
                        """
                        ),
                        {"urn": urn},
                    )
                    .mappings()
                    .first()
                )
                timeline_rows = list(
                    connection.execute(
                        text(
                            """
                            SELECT
                                inspection_number,
                                inspection_start_date,
                                publication_date,
                                inspection_type,
                                overall_effectiveness_label,
                                headline_outcome_text,
                                category_of_concern
                            FROM ofsted_inspections
                            WHERE urn = :urn
                            ORDER BY
                                inspection_start_date DESC,
                                inspection_number DESC
                            """
                        ),
                        {"urn": urn},
                    ).mappings()
                )
                deprivation_row = None
                postcode = _to_optional_str(row["postcode"]) if row is not None else None
                if postcode is not None:
                    deprivation_row = (
                        connection.execute(
                            text(
                                """
                                SELECT
                                    deprivation.lsoa_code,
                                    deprivation.imd_decile,
                                    deprivation.idaci_score,
                                    deprivation.idaci_decile,
                                    deprivation.source_release
                                FROM postcode_cache AS cache
                                INNER JOIN area_deprivation AS deprivation
                                    ON lower(deprivation.lsoa_name) = lower(cache.lsoa)
                                WHERE replace(upper(cache.postcode), ' ', '') =
                                      replace(upper(:postcode), ' ', '')
                                ORDER BY cache.cached_at DESC
                                LIMIT 1
                                """
                            ),
                            {"postcode": postcode},
                        )
                        .mappings()
                        .first()
                    )

                crime_months_available = int(
                    connection.execute(
                        text(
                            """
                            SELECT COUNT(DISTINCT month)
                            FROM area_crime_context
                            WHERE urn = :urn
                            """
                        ),
                        {"urn": urn},
                    ).scalar_one()
                )
                latest_crime_row = (
                    connection.execute(
                        text(
                            """
                            SELECT
                                month,
                                radius_meters
                            FROM area_crime_context
                            WHERE urn = :urn
                            ORDER BY month DESC, radius_meters DESC
                            LIMIT 1
                            """
                        ),
                        {"urn": urn},
                    )
                    .mappings()
                    .first()
                )
                crime_category_rows = []
                if latest_crime_row is not None:
                    crime_category_rows = list(
                        connection.execute(
                            text(
                                """
                                SELECT
                                    crime_category,
                                    incident_count
                                FROM area_crime_context
                                WHERE
                                    urn = :urn
                                    AND month = :month
                                    AND radius_meters = :radius_meters
                                ORDER BY
                                    incident_count DESC,
                                    crime_category ASC
                                """
                            ),
                            {
                                "urn": urn,
                                "month": latest_crime_row["month"],
                                "radius_meters": latest_crime_row["radius_meters"],
                            },
                        ).mappings()
                    )
        except SQLAlchemyError as exc:
            raise SchoolProfileDataUnavailableError(
                "School profile datastore is unavailable."
            ) from exc

        if row is None:
            return None

        demographics_latest = None
        if row["academic_year"] is not None:
            demographics_latest = SchoolDemographicsLatest(
                academic_year=str(row["academic_year"]),
                disadvantaged_pct=_to_optional_float(row["disadvantaged_pct"]),
                fsm_pct=_to_optional_float(row["fsm_pct"]),
                sen_pct=_to_optional_float(row["sen_pct"]),
                ehcp_pct=_to_optional_float(row["ehcp_pct"]),
                eal_pct=_to_optional_float(row["eal_pct"]),
                first_language_english_pct=_to_optional_float(row["first_language_english_pct"]),
                first_language_unclassified_pct=_to_optional_float(
                    row["first_language_unclassified_pct"]
                ),
                coverage=SchoolDemographicsCoverage(
                    # Phase 1 source contract does not provide direct school-level FSM%.
                    fsm_supported=False,
                    ethnicity_supported=bool(row["has_ethnicity_data"]),
                    top_languages_supported=bool(row["has_top_languages_data"]),
                ),
            )

        ofsted_latest = None
        if row["ofsted_urn"] is not None:
            ofsted_latest = SchoolOfstedLatest(
                overall_effectiveness_code=_to_optional_str(row["overall_effectiveness_code"]),
                overall_effectiveness_label=_to_optional_str(row["overall_effectiveness_label"]),
                inspection_start_date=row["inspection_start_date"],
                publication_date=row["publication_date"],
                is_graded=bool(row["is_graded"]),
                ungraded_outcome=_to_optional_str(row["ungraded_outcome"]),
            )

        timeline_events = tuple(
            SchoolOfstedTimelineEvent(
                inspection_number=str(timeline_row["inspection_number"]),
                inspection_start_date=timeline_row["inspection_start_date"],
                publication_date=timeline_row["publication_date"],
                inspection_type=_to_optional_str(timeline_row["inspection_type"]),
                overall_effectiveness_label=_to_optional_str(
                    timeline_row["overall_effectiveness_label"]
                ),
                headline_outcome_text=_to_optional_str(timeline_row["headline_outcome_text"]),
                category_of_concern=_to_optional_str(timeline_row["category_of_concern"]),
            )
            for timeline_row in timeline_rows
        )
        timeline_coverage = SchoolOfstedTimelineCoverage(
            is_partial_history=not timeline_events
            or min(event.inspection_start_date for event in timeline_events)
            > HISTORICAL_TIMELINE_BASELINE_DATE,
            earliest_event_date=min(event.inspection_start_date for event in timeline_events)
            if timeline_events
            else None,
            latest_event_date=max(event.inspection_start_date for event in timeline_events)
            if timeline_events
            else None,
            events_count=len(timeline_events),
        )
        ofsted_timeline = SchoolOfstedTimeline(
            events=timeline_events,
            coverage=timeline_coverage,
        )

        deprivation = None
        if deprivation_row is not None:
            deprivation = SchoolAreaDeprivation(
                lsoa_code=str(deprivation_row["lsoa_code"]),
                imd_decile=int(deprivation_row["imd_decile"]),
                idaci_score=float(str(deprivation_row["idaci_score"])),
                idaci_decile=int(deprivation_row["idaci_decile"]),
                source_release=str(deprivation_row["source_release"]),
            )

        crime = None
        if latest_crime_row is not None:
            latest_month = latest_crime_row["month"]
            if latest_month is not None:
                crime = SchoolAreaCrime(
                    radius_miles=round(
                        float(str(latest_crime_row["radius_meters"])) / METERS_PER_MILE, 2
                    ),
                    latest_month=latest_month.strftime("%Y-%m"),
                    total_incidents=sum(
                        int(category_row["incident_count"]) for category_row in crime_category_rows
                    ),
                    categories=tuple(
                        SchoolAreaCrimeCategory(
                            category=str(category_row["crime_category"]),
                            incident_count=int(category_row["incident_count"]),
                        )
                        for category_row in crime_category_rows
                    ),
                )

        area_context = SchoolAreaContext(
            deprivation=deprivation,
            crime=crime,
            coverage=SchoolAreaContextCoverage(
                has_deprivation=deprivation is not None,
                has_crime=crime is not None,
                crime_months_available=crime_months_available,
            ),
        )

        return SchoolProfile(
            school=SchoolProfileSchool(
                urn=str(row["urn"]),
                name=str(row["name"]),
                phase=_to_optional_str(row["phase"]),
                school_type=_to_optional_str(row["type"]),
                status=_to_optional_str(row["status"]),
                postcode=_to_optional_str(row["postcode"]),
                lat=float(row["lat"]),
                lng=float(row["lng"]),
            ),
            demographics_latest=demographics_latest,
            ofsted_latest=ofsted_latest,
            ofsted_timeline=ofsted_timeline,
            area_context=area_context,
        )


def _to_optional_float(value: object) -> float | None:
    if value is None:
        return None
    return float(str(value))


def _to_optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)
