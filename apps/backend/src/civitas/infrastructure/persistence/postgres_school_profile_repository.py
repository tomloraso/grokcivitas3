from __future__ import annotations

from datetime import date, datetime
from typing import Literal, Mapping

from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine
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
    SchoolDemographicsEthnicityGroup,
    SchoolDemographicsLatest,
    SchoolOfstedLatest,
    SchoolOfstedTimeline,
    SchoolOfstedTimelineCoverage,
    SchoolOfstedTimelineEvent,
    SchoolPerformance,
    SchoolPerformanceYear,
    SchoolProfile,
    SchoolProfileCompleteness,
    SchoolProfileSchool,
    SchoolProfileSectionCompleteness,
)

HISTORICAL_TIMELINE_BASELINE_DATE = date(2015, 9, 14)
METERS_PER_MILE = 1609.344
SECTION_COMPLETENESS_STATUS = Literal["available", "partial", "unavailable"]
SECTION_COMPLETENESS_REASON = Literal[
    "source_missing",
    "insufficient_years_published",
    "source_not_in_catalog",
    "source_file_missing_for_year",
    "source_schema_incompatible_for_year",
    "partial_metric_coverage",
    "source_not_provided",
    "rejected_by_validation",
    "not_joined_yet",
    "pipeline_failed_recently",
    "not_applicable",
    "source_coverage_gap",
    "stale_after_school_refresh",
    "no_incidents_in_radius",
]
ETHNICITY_GROUP_COLUMNS: tuple[tuple[str, str, str, str], ...] = (
    ("white_british", "White British", "white_british_pct", "white_british_count"),
    ("irish", "Irish", "irish_pct", "irish_count"),
    (
        "traveller_of_irish_heritage",
        "Traveller of Irish heritage",
        "traveller_of_irish_heritage_pct",
        "traveller_of_irish_heritage_count",
    ),
    (
        "any_other_white_background",
        "Any other white background",
        "any_other_white_background_pct",
        "any_other_white_background_count",
    ),
    ("gypsy_roma", "Gypsy/Roma", "gypsy_roma_pct", "gypsy_roma_count"),
    (
        "white_and_black_caribbean",
        "White and Black Caribbean",
        "white_and_black_caribbean_pct",
        "white_and_black_caribbean_count",
    ),
    (
        "white_and_black_african",
        "White and Black African",
        "white_and_black_african_pct",
        "white_and_black_african_count",
    ),
    ("white_and_asian", "White and Asian", "white_and_asian_pct", "white_and_asian_count"),
    (
        "any_other_mixed_background",
        "Any other mixed background",
        "any_other_mixed_background_pct",
        "any_other_mixed_background_count",
    ),
    ("indian", "Indian", "indian_pct", "indian_count"),
    ("pakistani", "Pakistani", "pakistani_pct", "pakistani_count"),
    ("bangladeshi", "Bangladeshi", "bangladeshi_pct", "bangladeshi_count"),
    (
        "any_other_asian_background",
        "Any other Asian background",
        "any_other_asian_background_pct",
        "any_other_asian_background_count",
    ),
    ("caribbean", "Caribbean", "caribbean_pct", "caribbean_count"),
    ("african", "African", "african_pct", "african_count"),
    (
        "any_other_black_background",
        "Any other black background",
        "any_other_black_background_pct",
        "any_other_black_background_count",
    ),
    ("chinese", "Chinese", "chinese_pct", "chinese_count"),
    (
        "any_other_ethnic_group",
        "Any other ethnic group",
        "any_other_ethnic_group_pct",
        "any_other_ethnic_group_count",
    ),
    ("unclassified", "Unclassified", "unclassified_pct", "unclassified_count"),
)


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
                            schools.updated_at AS school_updated_at,
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
                            demographics.source_dataset_id,
                            ethnicity.white_british_pct,
                            ethnicity.white_british_count,
                            ethnicity.irish_pct,
                            ethnicity.irish_count,
                            ethnicity.traveller_of_irish_heritage_pct,
                            ethnicity.traveller_of_irish_heritage_count,
                            ethnicity.any_other_white_background_pct,
                            ethnicity.any_other_white_background_count,
                            ethnicity.gypsy_roma_pct,
                            ethnicity.gypsy_roma_count,
                            ethnicity.white_and_black_caribbean_pct,
                            ethnicity.white_and_black_caribbean_count,
                            ethnicity.white_and_black_african_pct,
                            ethnicity.white_and_black_african_count,
                            ethnicity.white_and_asian_pct,
                            ethnicity.white_and_asian_count,
                            ethnicity.any_other_mixed_background_pct,
                            ethnicity.any_other_mixed_background_count,
                            ethnicity.indian_pct,
                            ethnicity.indian_count,
                            ethnicity.pakistani_pct,
                            ethnicity.pakistani_count,
                            ethnicity.bangladeshi_pct,
                            ethnicity.bangladeshi_count,
                            ethnicity.any_other_asian_background_pct,
                            ethnicity.any_other_asian_background_count,
                            ethnicity.caribbean_pct,
                            ethnicity.caribbean_count,
                            ethnicity.african_pct,
                            ethnicity.african_count,
                            ethnicity.any_other_black_background_pct,
                            ethnicity.any_other_black_background_count,
                            ethnicity.chinese_pct,
                            ethnicity.chinese_count,
                            ethnicity.any_other_ethnic_group_pct,
                            ethnicity.any_other_ethnic_group_count,
                            ethnicity.unclassified_pct,
                            ethnicity.unclassified_count,
                            demographics.updated_at AS demographics_updated_at,
                            ofsted.urn AS ofsted_urn,
                            ofsted.overall_effectiveness_code,
                            ofsted.overall_effectiveness_label,
                            ofsted.inspection_start_date,
                            ofsted.publication_date,
                            ofsted.latest_oeif_inspection_start_date,
                            ofsted.latest_oeif_publication_date,
                            ofsted.quality_of_education_code,
                            ofsted.quality_of_education_label,
                            ofsted.behaviour_and_attitudes_code,
                            ofsted.behaviour_and_attitudes_label,
                            ofsted.personal_development_code,
                            ofsted.personal_development_label,
                            ofsted.leadership_and_management_code,
                            ofsted.leadership_and_management_label,
                            ofsted.latest_ungraded_inspection_date,
                            ofsted.latest_ungraded_publication_date,
                            ofsted.is_graded,
                            ofsted.ungraded_outcome,
                            ofsted.updated_at AS ofsted_latest_updated_at
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
                                has_top_languages_data,
                                source_dataset_id,
                                updated_at
                            FROM school_demographics_yearly
                            WHERE school_demographics_yearly.urn = schools.urn
                            ORDER BY
                                substring(academic_year from 1 for 4)::integer DESC,
                                academic_year DESC
                            LIMIT 1
                        ) AS demographics ON TRUE
                        LEFT JOIN LATERAL (
                            SELECT
                                white_british_pct,
                                white_british_count,
                                irish_pct,
                                irish_count,
                                traveller_of_irish_heritage_pct,
                                traveller_of_irish_heritage_count,
                                any_other_white_background_pct,
                                any_other_white_background_count,
                                gypsy_roma_pct,
                                gypsy_roma_count,
                                white_and_black_caribbean_pct,
                                white_and_black_caribbean_count,
                                white_and_black_african_pct,
                                white_and_black_african_count,
                                white_and_asian_pct,
                                white_and_asian_count,
                                any_other_mixed_background_pct,
                                any_other_mixed_background_count,
                                indian_pct,
                                indian_count,
                                pakistani_pct,
                                pakistani_count,
                                bangladeshi_pct,
                                bangladeshi_count,
                                any_other_asian_background_pct,
                                any_other_asian_background_count,
                                caribbean_pct,
                                caribbean_count,
                                african_pct,
                                african_count,
                                any_other_black_background_pct,
                                any_other_black_background_count,
                                chinese_pct,
                                chinese_count,
                                any_other_ethnic_group_pct,
                                any_other_ethnic_group_count,
                                unclassified_pct,
                                unclassified_count
                            FROM school_ethnicity_yearly
                            WHERE
                                school_ethnicity_yearly.urn = schools.urn
                                AND school_ethnicity_yearly.academic_year = demographics.academic_year
                            LIMIT 1
                        ) AS ethnicity ON TRUE
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
                                category_of_concern,
                                updated_at
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
                performance_rows = list(
                    connection.execute(
                        text(
                            """
                            SELECT
                                academic_year,
                                attainment8_average,
                                progress8_average,
                                progress8_disadvantaged,
                                progress8_not_disadvantaged,
                                progress8_disadvantaged_gap,
                                engmath_5_plus_pct,
                                engmath_4_plus_pct,
                                ebacc_entry_pct,
                                ebacc_5_plus_pct,
                                ebacc_4_plus_pct,
                                ks2_reading_expected_pct,
                                ks2_writing_expected_pct,
                                ks2_maths_expected_pct,
                                ks2_combined_expected_pct,
                                ks2_reading_higher_pct,
                                ks2_writing_higher_pct,
                                ks2_maths_higher_pct,
                                ks2_combined_higher_pct,
                                updated_at
                            FROM school_performance_yearly
                            WHERE urn = :urn
                            ORDER BY
                                substring(academic_year from 1 for 4)::integer ASC,
                                academic_year ASC
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
                                    deprivation.imd_score,
                                    deprivation.imd_rank,
                                    deprivation.imd_decile,
                                    deprivation.idaci_score,
                                    deprivation.idaci_decile,
                                    deprivation.source_release,
                                    deprivation.updated_at
                                FROM postcode_cache AS cache
                                INNER JOIN area_deprivation AS deprivation
                                    ON deprivation.lsoa_code = cache.lsoa_code
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

                school_crime_months_available = int(
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
                crime_updated_at = connection.execute(
                    text(
                        """
                        SELECT MAX(updated_at)
                        FROM area_crime_context
                        WHERE urn = :urn
                        """
                    ),
                    {"urn": urn},
                ).scalar_one()
                global_crime_months_available: int
                global_crime_updated_at: object
                latest_global_crime_row: dict[str, object] | None
                global_crime_metadata = _load_global_crime_metadata(connection)
                if global_crime_metadata is None:
                    global_crime_months_available = int(
                        connection.execute(
                            text(
                                """
                                SELECT COUNT(DISTINCT month)
                                FROM area_crime_context
                                """
                            )
                        ).scalar_one()
                    )
                    global_crime_updated_at = connection.execute(
                        text(
                            """
                            SELECT MAX(updated_at)
                            FROM area_crime_context
                            """
                        )
                    ).scalar_one()
                    latest_global_crime_row_mapping = (
                        connection.execute(
                            text(
                                """
                                SELECT
                                    month,
                                    radius_meters
                                FROM area_crime_context
                                ORDER BY month DESC, updated_at DESC, radius_meters DESC
                                LIMIT 1
                                """
                            )
                        )
                        .mappings()
                        .first()
                    )
                    latest_global_crime_row = (
                        dict(latest_global_crime_row_mapping)
                        if latest_global_crime_row_mapping is not None
                        else None
                    )
                else:
                    (
                        global_crime_months_available,
                        global_crime_updated_at,
                        metadata_latest_month,
                        metadata_latest_radius_meters,
                    ) = global_crime_metadata
                    latest_global_crime_row = (
                        {
                            "month": metadata_latest_month,
                            "radius_meters": metadata_latest_radius_meters,
                        }
                        if metadata_latest_month is not None
                        and metadata_latest_radius_meters is not None
                        else None
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
            ethnicity_breakdown = _build_ethnicity_breakdown(dict(row))
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
                    fsm_supported=_supports_direct_fsm(
                        source_dataset_id=row["source_dataset_id"],
                        fsm_pct=row["fsm_pct"],
                    ),
                    ethnicity_supported=bool(ethnicity_breakdown),
                    top_languages_supported=bool(row["has_top_languages_data"]),
                ),
                ethnicity_breakdown=ethnicity_breakdown,
            )

        ofsted_latest = None
        if row["ofsted_urn"] is not None:
            most_recent_inspection_date = _max_optional_date(
                (
                    row["inspection_start_date"],
                    row["latest_ungraded_inspection_date"],
                )
            )
            days_since_most_recent_inspection = (
                max((date.today() - most_recent_inspection_date).days, 0)
                if most_recent_inspection_date is not None
                else None
            )
            ofsted_latest = SchoolOfstedLatest(
                overall_effectiveness_code=_to_optional_str(row["overall_effectiveness_code"]),
                overall_effectiveness_label=_to_optional_str(row["overall_effectiveness_label"]),
                inspection_start_date=row["inspection_start_date"],
                publication_date=row["publication_date"],
                latest_oeif_inspection_start_date=row["latest_oeif_inspection_start_date"],
                latest_oeif_publication_date=row["latest_oeif_publication_date"],
                quality_of_education_code=_to_optional_str(row["quality_of_education_code"]),
                quality_of_education_label=_to_optional_str(row["quality_of_education_label"]),
                behaviour_and_attitudes_code=_to_optional_str(row["behaviour_and_attitudes_code"]),
                behaviour_and_attitudes_label=_to_optional_str(
                    row["behaviour_and_attitudes_label"]
                ),
                personal_development_code=_to_optional_str(row["personal_development_code"]),
                personal_development_label=_to_optional_str(row["personal_development_label"]),
                leadership_and_management_code=_to_optional_str(
                    row["leadership_and_management_code"]
                ),
                leadership_and_management_label=_to_optional_str(
                    row["leadership_and_management_label"]
                ),
                latest_ungraded_inspection_date=row["latest_ungraded_inspection_date"],
                latest_ungraded_publication_date=row["latest_ungraded_publication_date"],
                most_recent_inspection_date=most_recent_inspection_date,
                days_since_most_recent_inspection=days_since_most_recent_inspection,
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

        performance_history = tuple(
            SchoolPerformanceYear(
                academic_year=str(performance_row["academic_year"]),
                attainment8_average=_to_optional_float(performance_row["attainment8_average"]),
                progress8_average=_to_optional_float(performance_row["progress8_average"]),
                progress8_disadvantaged=_to_optional_float(
                    performance_row["progress8_disadvantaged"]
                ),
                progress8_not_disadvantaged=_to_optional_float(
                    performance_row["progress8_not_disadvantaged"]
                ),
                progress8_disadvantaged_gap=_to_optional_float(
                    performance_row["progress8_disadvantaged_gap"]
                ),
                engmath_5_plus_pct=_to_optional_float(performance_row["engmath_5_plus_pct"]),
                engmath_4_plus_pct=_to_optional_float(performance_row["engmath_4_plus_pct"]),
                ebacc_entry_pct=_to_optional_float(performance_row["ebacc_entry_pct"]),
                ebacc_5_plus_pct=_to_optional_float(performance_row["ebacc_5_plus_pct"]),
                ebacc_4_plus_pct=_to_optional_float(performance_row["ebacc_4_plus_pct"]),
                ks2_reading_expected_pct=_to_optional_float(
                    performance_row["ks2_reading_expected_pct"]
                ),
                ks2_writing_expected_pct=_to_optional_float(
                    performance_row["ks2_writing_expected_pct"]
                ),
                ks2_maths_expected_pct=_to_optional_float(
                    performance_row["ks2_maths_expected_pct"]
                ),
                ks2_combined_expected_pct=_to_optional_float(
                    performance_row["ks2_combined_expected_pct"]
                ),
                ks2_reading_higher_pct=_to_optional_float(
                    performance_row["ks2_reading_higher_pct"]
                ),
                ks2_writing_higher_pct=_to_optional_float(
                    performance_row["ks2_writing_higher_pct"]
                ),
                ks2_maths_higher_pct=_to_optional_float(performance_row["ks2_maths_higher_pct"]),
                ks2_combined_higher_pct=_to_optional_float(
                    performance_row["ks2_combined_higher_pct"]
                ),
            )
            for performance_row in performance_rows
        )
        performance = (
            SchoolPerformance(
                latest=performance_history[-1] if performance_history else None,
                history=performance_history,
            )
            if performance_history
            else None
        )

        deprivation = None
        if deprivation_row is not None:
            deprivation = SchoolAreaDeprivation(
                lsoa_code=str(deprivation_row["lsoa_code"]),
                imd_score=float(str(deprivation_row["imd_score"])),
                imd_rank=int(deprivation_row["imd_rank"]),
                imd_decile=int(deprivation_row["imd_decile"]),
                idaci_score=float(str(deprivation_row["idaci_score"])),
                idaci_decile=int(deprivation_row["idaci_decile"]),
                source_release=str(deprivation_row["source_release"]),
            )

        school_updated_at = _to_optional_datetime(row["school_updated_at"])
        global_latest_crime_month: date | None = None
        global_latest_radius_meters: float | None = None
        if latest_global_crime_row is not None:
            raw_global_latest_month = latest_global_crime_row["month"]
            if isinstance(raw_global_latest_month, date):
                global_latest_crime_month = raw_global_latest_month
            global_latest_radius_meters = _to_optional_float(
                latest_global_crime_row["radius_meters"]
            )
        global_crime_updated_at_dt = _to_optional_datetime(global_crime_updated_at)

        inferred_no_incidents = False
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
        elif (
            global_latest_crime_month is not None
            and global_latest_radius_meters is not None
            and (
                school_updated_at is None
                or global_crime_updated_at_dt is None
                or school_updated_at <= global_crime_updated_at_dt
            )
        ):
            inferred_no_incidents = True
            crime = SchoolAreaCrime(
                radius_miles=round(float(str(global_latest_radius_meters)) / METERS_PER_MILE, 2),
                latest_month=global_latest_crime_month.strftime("%Y-%m"),
                total_incidents=0,
                categories=tuple(),
            )

        effective_crime_months_available = (
            school_crime_months_available
            if school_crime_months_available > 0
            else (
                global_crime_months_available
                if inferred_no_incidents
                else school_crime_months_available
            )
        )
        effective_crime_updated_at = (
            _to_optional_datetime(crime_updated_at)
            if school_crime_months_available > 0
            else global_crime_updated_at_dt
        )
        performance_updated_at = _max_optional_datetime(
            tuple(
                _to_optional_datetime(performance_row["updated_at"])
                for performance_row in performance_rows
            )
        )

        area_context = SchoolAreaContext(
            deprivation=deprivation,
            crime=crime,
            coverage=SchoolAreaContextCoverage(
                has_deprivation=deprivation is not None,
                has_crime=crime is not None,
                crime_months_available=effective_crime_months_available,
            ),
        )

        completeness = SchoolProfileCompleteness(
            demographics=_build_demographics_completeness(
                demographics_latest=demographics_latest,
                demographics_updated_at=_to_optional_datetime(row["demographics_updated_at"]),
            ),
            performance=_build_performance_completeness(
                performance=performance,
                performance_updated_at=performance_updated_at,
            ),
            ofsted_latest=_build_ofsted_latest_completeness(
                ofsted_latest=ofsted_latest,
                ofsted_latest_updated_at=_to_optional_datetime(row["ofsted_latest_updated_at"]),
            ),
            ofsted_timeline=_build_ofsted_timeline_completeness(
                events_count=timeline_coverage.events_count,
                is_partial_history=timeline_coverage.is_partial_history,
                timeline_updated_at=_max_optional_datetime(
                    tuple(
                        _to_optional_datetime(timeline_row["updated_at"])
                        for timeline_row in timeline_rows
                    )
                ),
            ),
            area_deprivation=_build_area_deprivation_completeness(
                postcode=postcode,
                deprivation=deprivation,
                deprivation_updated_at=_to_optional_datetime(
                    deprivation_row["updated_at"] if deprivation_row is not None else None
                ),
            ),
            area_crime=_build_area_crime_completeness(
                crime=crime,
                crime_months_available=effective_crime_months_available,
                crime_updated_at=effective_crime_updated_at,
                school_updated_at=school_updated_at,
                global_crime_updated_at=global_crime_updated_at_dt,
                has_global_crime_data=global_crime_months_available > 0,
                inferred_no_incidents=inferred_no_incidents,
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
            performance=performance,
            ofsted_latest=ofsted_latest,
            ofsted_timeline=ofsted_timeline,
            area_context=area_context,
            completeness=completeness,
        )


def _to_optional_float(value: object) -> float | None:
    if value is None:
        return None
    return float(str(value))


def _to_optional_int(value: object) -> int | None:
    if value is None:
        return None
    return int(float(str(value)))


def _to_optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _to_optional_datetime(value: object) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    return None


def _load_global_crime_metadata(
    connection: Connection,
) -> tuple[int, datetime | None, date | None, float | None] | None:
    if not _table_exists(connection, "area_crime_global_metadata"):
        return None

    row = (
        connection.execute(
            text(
                """
                SELECT
                    months_available,
                    latest_updated_at,
                    latest_month,
                    latest_radius_meters
                FROM area_crime_global_metadata
                WHERE id = 1
                """
            )
        )
        .mappings()
        .first()
    )
    if row is None:
        return None

    raw_month = row["latest_month"]
    latest_month = raw_month if isinstance(raw_month, date) else None
    return (
        int(row["months_available"]),
        _to_optional_datetime(row["latest_updated_at"]),
        latest_month,
        _to_optional_float(row["latest_radius_meters"]),
    )


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


def _max_optional_datetime(values: tuple[datetime | None, ...]) -> datetime | None:
    non_null_values = [value for value in values if value is not None]
    if not non_null_values:
        return None
    return max(non_null_values)


def _max_optional_date(values: tuple[date | None, ...]) -> date | None:
    non_null_values = [value for value in values if value is not None]
    if not non_null_values:
        return None
    return max(non_null_values)


def _build_ethnicity_breakdown(
    row: Mapping[str, object],
) -> tuple[SchoolDemographicsEthnicityGroup, ...]:
    groups: list[SchoolDemographicsEthnicityGroup] = []
    for key, label, pct_column, count_column in ETHNICITY_GROUP_COLUMNS:
        percentage = _to_optional_float(row.get(pct_column))
        count = _to_optional_int(row.get(count_column))
        if percentage is None and count is None:
            continue
        groups.append(
            SchoolDemographicsEthnicityGroup(
                key=key,
                label=label,
                percentage=percentage,
                count=count,
            )
        )
    return tuple(groups)


def _section_completeness(
    *,
    status: SECTION_COMPLETENESS_STATUS,
    reason_code: SECTION_COMPLETENESS_REASON | None,
    last_updated_at: datetime | None,
) -> SchoolProfileSectionCompleteness:
    return SchoolProfileSectionCompleteness(
        status=status,
        reason_code=reason_code,
        last_updated_at=last_updated_at,
        years_available=None,
    )


def _build_demographics_completeness(
    *,
    demographics_latest: SchoolDemographicsLatest | None,
    demographics_updated_at: datetime | None,
) -> SchoolProfileSectionCompleteness:
    if demographics_latest is None:
        return _section_completeness(
            status="unavailable",
            reason_code="source_file_missing_for_year",
            last_updated_at=None,
        )

    has_sparse_metrics = any(
        value is None
        for value in (
            demographics_latest.disadvantaged_pct,
            demographics_latest.sen_pct,
            demographics_latest.ehcp_pct,
            demographics_latest.eal_pct,
            demographics_latest.first_language_english_pct,
            demographics_latest.first_language_unclassified_pct,
        )
    )
    has_unsupported_metrics = (
        not demographics_latest.coverage.fsm_supported
        or not demographics_latest.coverage.ethnicity_supported
        or not demographics_latest.coverage.top_languages_supported
    )
    if has_sparse_metrics or has_unsupported_metrics:
        return _section_completeness(
            status="partial",
            reason_code="partial_metric_coverage",
            last_updated_at=demographics_updated_at,
        )
    return _section_completeness(
        status="available",
        reason_code=None,
        last_updated_at=demographics_updated_at,
    )


def _build_performance_completeness(
    *,
    performance: SchoolPerformance | None,
    performance_updated_at: datetime | None,
) -> SchoolProfileSectionCompleteness:
    if performance is None or len(performance.history) == 0:
        return _section_completeness(
            status="unavailable",
            reason_code="source_missing",
            last_updated_at=None,
        )

    if len(performance.history) < 3:
        return _section_completeness(
            status="partial",
            reason_code="insufficient_years_published",
            last_updated_at=performance_updated_at,
        )

    if any(not _performance_year_has_any_metrics(year) for year in performance.history):
        return _section_completeness(
            status="partial",
            reason_code="partial_metric_coverage",
            last_updated_at=performance_updated_at,
        )

    return _section_completeness(
        status="available",
        reason_code=None,
        last_updated_at=performance_updated_at,
    )


def _performance_year_has_any_metrics(year: SchoolPerformanceYear) -> bool:
    return any(
        value is not None
        for value in (
            year.attainment8_average,
            year.progress8_average,
            year.progress8_disadvantaged,
            year.progress8_not_disadvantaged,
            year.progress8_disadvantaged_gap,
            year.engmath_5_plus_pct,
            year.engmath_4_plus_pct,
            year.ebacc_entry_pct,
            year.ebacc_5_plus_pct,
            year.ebacc_4_plus_pct,
            year.ks2_reading_expected_pct,
            year.ks2_writing_expected_pct,
            year.ks2_maths_expected_pct,
            year.ks2_combined_expected_pct,
            year.ks2_reading_higher_pct,
            year.ks2_writing_higher_pct,
            year.ks2_maths_higher_pct,
            year.ks2_combined_higher_pct,
        )
    )


def _build_ofsted_latest_completeness(
    *,
    ofsted_latest: SchoolOfstedLatest | None,
    ofsted_latest_updated_at: datetime | None,
) -> SchoolProfileSectionCompleteness:
    if ofsted_latest is None:
        return _section_completeness(
            status="unavailable",
            reason_code="source_missing",
            last_updated_at=None,
        )

    if ofsted_latest.overall_effectiveness_label is None and ofsted_latest.ungraded_outcome is None:
        return _section_completeness(
            status="partial",
            reason_code="source_not_provided",
            last_updated_at=ofsted_latest_updated_at,
        )
    return _section_completeness(
        status="available",
        reason_code=None,
        last_updated_at=ofsted_latest_updated_at,
    )


def _build_ofsted_timeline_completeness(
    *,
    events_count: int,
    is_partial_history: bool,
    timeline_updated_at: datetime | None,
) -> SchoolProfileSectionCompleteness:
    if events_count == 0:
        return _section_completeness(
            status="unavailable",
            reason_code="source_missing",
            last_updated_at=None,
        )
    if is_partial_history:
        return _section_completeness(
            status="partial",
            reason_code="source_missing",
            last_updated_at=timeline_updated_at,
        )
    return _section_completeness(
        status="available",
        reason_code=None,
        last_updated_at=timeline_updated_at,
    )


def _build_area_deprivation_completeness(
    *,
    postcode: str | None,
    deprivation: SchoolAreaDeprivation | None,
    deprivation_updated_at: datetime | None,
) -> SchoolProfileSectionCompleteness:
    if postcode is None or not postcode.strip():
        return _section_completeness(
            status="unavailable",
            reason_code="not_applicable",
            last_updated_at=None,
        )
    if deprivation is None:
        return _section_completeness(
            status="unavailable",
            reason_code="not_joined_yet",
            last_updated_at=None,
        )
    return _section_completeness(
        status="available",
        reason_code=None,
        last_updated_at=deprivation_updated_at,
    )


def _build_area_crime_completeness(
    *,
    crime: SchoolAreaCrime | None,
    crime_months_available: int,
    crime_updated_at: datetime | None,
    school_updated_at: datetime | None,
    global_crime_updated_at: datetime | None,
    has_global_crime_data: bool,
    inferred_no_incidents: bool,
) -> SchoolProfileSectionCompleteness:
    if crime is None:
        if not has_global_crime_data:
            return _section_completeness(
                status="unavailable",
                reason_code="source_missing",
                last_updated_at=None,
            )
        if (
            school_updated_at is not None
            and global_crime_updated_at is not None
            and school_updated_at > global_crime_updated_at
        ):
            return _section_completeness(
                status="unavailable",
                reason_code="stale_after_school_refresh",
                last_updated_at=global_crime_updated_at,
            )
        return _section_completeness(
            status="unavailable",
            reason_code="source_coverage_gap",
            last_updated_at=global_crime_updated_at,
        )
    if crime_months_available < 12:
        return _section_completeness(
            status="partial",
            reason_code="source_coverage_gap",
            last_updated_at=crime_updated_at,
        )
    if inferred_no_incidents and crime.total_incidents == 0:
        return _section_completeness(
            status="available",
            reason_code="no_incidents_in_radius",
            last_updated_at=crime_updated_at,
        )
    return _section_completeness(
        status="available",
        reason_code=None,
        last_updated_at=crime_updated_at,
    )


def _supports_direct_fsm(*, source_dataset_id: object, fsm_pct: object) -> bool:
    source_token = _to_optional_str(source_dataset_id)
    if source_token is not None and "spc:" in source_token:
        return True

    # Legacy rows may not include family tokens in source_dataset_id.
    return _to_optional_float(fsm_pct) is not None
