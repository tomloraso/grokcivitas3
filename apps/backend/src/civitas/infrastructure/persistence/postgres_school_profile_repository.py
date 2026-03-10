from __future__ import annotations

from datetime import date, datetime
from typing import Literal, Mapping, Sequence, cast

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
    SchoolAreaCrimeAnnualRate,
    SchoolAreaCrimeCategory,
    SchoolAreaDeprivation,
    SchoolAreaHousePricePoint,
    SchoolAreaHousePrices,
    SchoolAttendanceLatest,
    SchoolBehaviourLatest,
    SchoolDemographicsCoverage,
    SchoolDemographicsEthnicityGroup,
    SchoolDemographicsHomeLanguage,
    SchoolDemographicsLatest,
    SchoolDemographicsSendPrimaryNeed,
    SchoolFinanceLatest,
    SchoolLeadershipSnapshot,
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
    SchoolWorkforceLatest,
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
                            schools.website,
                            schools.telephone,
                            schools.head_title,
                            schools.head_first_name,
                            schools.head_last_name,
                            schools.head_job_title,
                            schools.address_street,
                            schools.address_locality,
                            schools.address_line3,
                            schools.address_town,
                            schools.address_county,
                            schools.statutory_low_age,
                            schools.statutory_high_age,
                            schools.gender,
                            schools.religious_character,
                            schools.diocese,
                            schools.admissions_policy,
                            schools.sixth_form,
                            schools.nursery_provision,
                            schools.boarders,
                            schools.fsm_pct_gias,
                            schools.trust_name,
                            schools.trust_flag,
                            schools.federation_name,
                            schools.federation_flag,
                            schools.la_name,
                            schools.la_code,
                            schools.urban_rural,
                            schools.number_of_boys,
                            schools.number_of_girls,
                            schools.lsoa_code,
                            schools.lsoa_name,
                            schools.last_changed_date,
                            schools.updated_at AS school_updated_at,
                            ST_Y(schools.location::geometry) AS lat,
                            ST_X(schools.location::geometry) AS lng,
                            demographics.academic_year,
                            demographics.disadvantaged_pct,
                            demographics.fsm_pct,
                            demographics.fsm6_pct,
                            demographics.sen_pct,
                            demographics.ehcp_pct,
                            demographics.eal_pct,
                            demographics.first_language_english_pct,
                            demographics.first_language_unclassified_pct,
                            demographics.male_pct,
                            demographics.female_pct,
                            demographics.pupil_mobility_pct,
                            demographics.has_fsm6_data,
                            demographics.has_gender_data,
                            demographics.has_mobility_data,
                            demographics.has_ethnicity_data,
                            demographics.has_top_languages_data,
                            demographics.has_send_primary_need_data,
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
                            ofsted.provider_page_url,
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
                                fsm6_pct,
                                sen_pct,
                                ehcp_pct,
                                eal_pct,
                                first_language_english_pct,
                                first_language_unclassified_pct,
                                male_pct,
                                female_pct,
                                pupil_mobility_pct,
                                has_fsm6_data,
                                has_gender_data,
                                has_mobility_data,
                                has_ethnicity_data,
                                has_top_languages_data,
                                has_send_primary_need_data,
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
                attendance_row = (
                    connection.execute(
                        text(
                            """
                            SELECT
                                academic_year,
                                overall_attendance_pct,
                                overall_absence_pct,
                                persistent_absence_pct,
                                updated_at
                            FROM school_attendance_yearly
                            WHERE urn = :urn
                            ORDER BY
                                substring(academic_year from 1 for 4)::integer DESC,
                                academic_year DESC
                            LIMIT 1
                            """
                        ),
                        {"urn": urn},
                    )
                    .mappings()
                    .first()
                )
                behaviour_row = (
                    connection.execute(
                        text(
                            """
                            SELECT
                                academic_year,
                                suspensions_count,
                                suspensions_rate,
                                permanent_exclusions_count,
                                permanent_exclusions_rate,
                                updated_at
                            FROM school_behaviour_yearly
                            WHERE urn = :urn
                            ORDER BY
                                substring(academic_year from 1 for 4)::integer DESC,
                                academic_year DESC
                            LIMIT 1
                            """
                        ),
                        {"urn": urn},
                    )
                    .mappings()
                    .first()
                )
                workforce_row = (
                    connection.execute(
                        text(
                            """
                            SELECT
                                academic_year,
                                pupil_teacher_ratio,
                                supply_staff_pct,
                                teachers_3plus_years_pct,
                                teacher_turnover_pct,
                                qts_pct,
                                qualifications_level6_plus_pct,
                                updated_at
                            FROM school_workforce_yearly
                            WHERE urn = :urn
                            ORDER BY
                                substring(academic_year from 1 for 4)::integer DESC,
                                academic_year DESC
                            LIMIT 1
                            """
                        ),
                        {"urn": urn},
                    )
                    .mappings()
                    .first()
                )
                finance_row = (
                    connection.execute(
                        text(
                            """
                            SELECT
                                academic_year,
                                total_income_gbp,
                                total_expenditure_gbp,
                                income_per_pupil_gbp,
                                expenditure_per_pupil_gbp,
                                total_staff_costs_gbp,
                                staff_costs_pct_of_expenditure,
                                revenue_reserve_gbp,
                                revenue_reserve_per_pupil_gbp,
                                updated_at
                            FROM school_financials_yearly
                            WHERE urn = :urn
                            ORDER BY
                                substring(academic_year from 1 for 4)::integer DESC,
                                academic_year DESC
                            LIMIT 1
                            """
                        ),
                        {"urn": urn},
                    )
                    .mappings()
                    .first()
                )
                leadership_row = (
                    connection.execute(
                        text(
                            """
                            SELECT
                                headteacher_name,
                                headteacher_start_date,
                                headteacher_tenure_years,
                                leadership_turnover_score,
                                updated_at
                            FROM school_leadership_snapshot
                            WHERE urn = :urn
                            """
                        ),
                        {"urn": urn},
                    )
                    .mappings()
                    .first()
                )
                send_primary_need_rows: list[dict[str, object]] = []
                home_language_rows: list[dict[str, object]] = []
                demographics_academic_year = (
                    _to_optional_str(row["academic_year"]) if row is not None else None
                )
                if demographics_academic_year is not None:
                    send_primary_need_rows = [
                        dict(raw_row)
                        for raw_row in connection.execute(
                            text(
                                """
                                SELECT
                                    need_key,
                                    need_label,
                                    pupil_count,
                                    percentage
                                FROM school_send_primary_need_yearly
                                WHERE
                                    urn = :urn
                                    AND academic_year = :academic_year
                                ORDER BY
                                    pupil_count DESC NULLS LAST,
                                    percentage DESC NULLS LAST,
                                    need_label ASC
                                """
                            ),
                            {
                                "urn": urn,
                                "academic_year": demographics_academic_year,
                            },
                        )
                        .mappings()
                        .all()
                    ]
                    home_language_rows = [
                        dict(raw_row)
                        for raw_row in connection.execute(
                            text(
                                """
                                SELECT
                                    language_key,
                                    language_label,
                                    rank,
                                    pupil_count,
                                    percentage
                                FROM school_home_language_yearly
                                WHERE
                                    urn = :urn
                                    AND academic_year = :academic_year
                                ORDER BY rank ASC, language_label ASC
                                """
                            ),
                            {
                                "urn": urn,
                                "academic_year": demographics_academic_year,
                            },
                        )
                        .mappings()
                        .all()
                    ]
                deprivation_row = None
                postcode = _to_optional_str(row["postcode"]) if row is not None else None
                if postcode is not None:
                    deprivation_row = (
                        connection.execute(
                            text(
                                """
                                SELECT
                                    deprivation.lsoa_code,
                                    deprivation.local_authority_district_code,
                                    deprivation.local_authority_district_name,
                                    deprivation.imd_score,
                                    deprivation.imd_rank,
                                    deprivation.imd_decile,
                                    deprivation.idaci_score,
                                    deprivation.idaci_decile,
                                    deprivation.income_score,
                                    deprivation.income_rank,
                                    deprivation.income_decile,
                                    deprivation.employment_score,
                                    deprivation.employment_rank,
                                    deprivation.employment_decile,
                                    deprivation.education_score,
                                    deprivation.education_rank,
                                    deprivation.education_decile,
                                    deprivation.health_score,
                                    deprivation.health_rank,
                                    deprivation.health_decile,
                                    deprivation.crime_score,
                                    deprivation.crime_rank,
                                    deprivation.crime_decile,
                                    deprivation.barriers_score,
                                    deprivation.barriers_rank,
                                    deprivation.barriers_decile,
                                    deprivation.living_environment_score,
                                    deprivation.living_environment_rank,
                                    deprivation.living_environment_decile,
                                    deprivation.population_total,
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
                crime_category_rows: list[dict[str, object]] = []
                crime_annual_rows: list[dict[str, object]] = []
                if latest_crime_row is not None:
                    crime_category_rows = [
                        dict(raw_row)
                        for raw_row in connection.execute(
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
                        )
                        .mappings()
                        .all()
                    ]
                    crime_annual_rows = [
                        dict(raw_row)
                        for raw_row in connection.execute(
                            text(
                                """
                                SELECT
                                    CAST(EXTRACT(YEAR FROM month) AS integer) AS year,
                                    CAST(SUM(incident_count) AS integer) AS total_incidents
                                FROM area_crime_context
                                WHERE
                                    urn = :urn
                                    AND radius_meters = :radius_meters
                                GROUP BY CAST(EXTRACT(YEAR FROM month) AS integer)
                                ORDER BY year DESC
                                LIMIT 3
                                """
                            ),
                            {
                                "urn": urn,
                                "radius_meters": latest_crime_row["radius_meters"],
                            },
                        )
                        .mappings()
                        .all()
                    ]

                house_price_rows: list[dict[str, object]] = []
                latest_house_price_row: Mapping[str, object] | None = None
                house_price_months_available = 0
                house_price_updated_at: object = None
                global_house_price_months_available = 0
                global_house_price_updated_at: object = None
                has_house_price_source = _table_exists(connection, "area_house_price_context")
                if has_house_price_source:
                    global_house_price_months_available = int(
                        connection.execute(
                            text("SELECT COUNT(DISTINCT month) FROM area_house_price_context")
                        ).scalar_one()
                    )
                    global_house_price_updated_at = connection.execute(
                        text("SELECT MAX(updated_at) FROM area_house_price_context")
                    ).scalar_one()

                    local_authority_district_code = _to_optional_str(
                        deprivation_row["local_authority_district_code"]
                        if deprivation_row is not None
                        else None
                    )
                    if local_authority_district_code is not None:
                        house_price_months_available = int(
                            connection.execute(
                                text(
                                    """
                                    SELECT COUNT(DISTINCT month)
                                    FROM area_house_price_context
                                    WHERE area_code = :area_code
                                    """
                                ),
                                {"area_code": local_authority_district_code},
                            ).scalar_one()
                        )
                        house_price_updated_at = connection.execute(
                            text(
                                """
                                SELECT MAX(updated_at)
                                FROM area_house_price_context
                                WHERE area_code = :area_code
                                """
                            ),
                            {"area_code": local_authority_district_code},
                        ).scalar_one()
                        house_price_rows = [
                            dict(raw_row)
                            for raw_row in connection.execute(
                                text(
                                    """
                                    SELECT
                                        month,
                                        area_name,
                                        average_price,
                                        annual_change_pct,
                                        monthly_change_pct
                                    FROM area_house_price_context
                                    WHERE area_code = :area_code
                                    ORDER BY month DESC
                                    LIMIT 36
                                    """
                                ),
                                {"area_code": local_authority_district_code},
                            )
                            .mappings()
                            .all()
                        ]
                        if house_price_rows:
                            latest_house_price_row = house_price_rows[0]
        except SQLAlchemyError as exc:
            raise SchoolProfileDataUnavailableError(
                "School profile datastore is unavailable."
            ) from exc

        if row is None:
            return None

        demographics_latest = None
        if row["academic_year"] is not None:
            ethnicity_breakdown = _build_ethnicity_breakdown(dict(row))
            send_primary_needs = tuple(
                SchoolDemographicsSendPrimaryNeed(
                    key=str(send_row["need_key"]),
                    label=str(send_row["need_label"]),
                    percentage=_to_optional_float(send_row["percentage"]),
                    count=_to_optional_int(send_row["pupil_count"]),
                )
                for send_row in send_primary_need_rows
            )
            top_home_languages_list: list[SchoolDemographicsHomeLanguage] = []
            for language_row in home_language_rows:
                rank = _to_optional_int(language_row.get("rank"))
                if rank is None:
                    continue
                top_home_languages_list.append(
                    SchoolDemographicsHomeLanguage(
                        key=str(language_row["language_key"]),
                        label=str(language_row["language_label"]),
                        rank=rank,
                        percentage=_to_optional_float(language_row["percentage"]),
                        count=_to_optional_int(language_row["pupil_count"]),
                    )
                )
            top_home_languages = tuple(top_home_languages_list)
            demographics_latest = SchoolDemographicsLatest(
                academic_year=str(row["academic_year"]),
                disadvantaged_pct=_to_optional_float(row["disadvantaged_pct"]),
                fsm_pct=_to_optional_float(row["fsm_pct"]),
                fsm6_pct=_to_optional_float(row["fsm6_pct"]),
                sen_pct=_to_optional_float(row["sen_pct"]),
                ehcp_pct=_to_optional_float(row["ehcp_pct"]),
                eal_pct=_to_optional_float(row["eal_pct"]),
                first_language_english_pct=_to_optional_float(row["first_language_english_pct"]),
                first_language_unclassified_pct=_to_optional_float(
                    row["first_language_unclassified_pct"]
                ),
                male_pct=_to_optional_float(row["male_pct"]),
                female_pct=_to_optional_float(row["female_pct"]),
                pupil_mobility_pct=_to_optional_float(row["pupil_mobility_pct"]),
                coverage=SchoolDemographicsCoverage(
                    fsm_supported=_supports_direct_fsm(
                        source_dataset_id=row["source_dataset_id"],
                        fsm_pct=row["fsm_pct"],
                    ),
                    fsm6_supported=bool(row["has_fsm6_data"]),
                    gender_supported=bool(row["has_gender_data"]),
                    mobility_supported=bool(row["has_mobility_data"]),
                    send_primary_need_supported=bool(row["has_send_primary_need_data"]),
                    ethnicity_supported=bool(ethnicity_breakdown),
                    top_languages_supported=bool(row["has_top_languages_data"]),
                ),
                ethnicity_breakdown=ethnicity_breakdown,
                send_primary_needs=send_primary_needs,
                top_home_languages=top_home_languages,
            )

        attendance_latest = None
        if attendance_row is not None and attendance_row["academic_year"] is not None:
            attendance_latest = SchoolAttendanceLatest(
                academic_year=str(attendance_row["academic_year"]),
                overall_attendance_pct=_to_optional_float(attendance_row["overall_attendance_pct"]),
                overall_absence_pct=_to_optional_float(attendance_row["overall_absence_pct"]),
                persistent_absence_pct=_to_optional_float(attendance_row["persistent_absence_pct"]),
            )

        behaviour_latest = None
        if behaviour_row is not None and behaviour_row["academic_year"] is not None:
            behaviour_latest = SchoolBehaviourLatest(
                academic_year=str(behaviour_row["academic_year"]),
                suspensions_count=_to_optional_int(behaviour_row["suspensions_count"]),
                suspensions_rate=_to_optional_float(behaviour_row["suspensions_rate"]),
                permanent_exclusions_count=_to_optional_int(
                    behaviour_row["permanent_exclusions_count"]
                ),
                permanent_exclusions_rate=_to_optional_float(
                    behaviour_row["permanent_exclusions_rate"]
                ),
            )

        workforce_latest = None
        if workforce_row is not None and workforce_row["academic_year"] is not None:
            workforce_latest = SchoolWorkforceLatest(
                academic_year=str(workforce_row["academic_year"]),
                pupil_teacher_ratio=_to_optional_float(workforce_row["pupil_teacher_ratio"]),
                supply_staff_pct=_to_optional_float(workforce_row["supply_staff_pct"]),
                teachers_3plus_years_pct=_to_optional_float(
                    workforce_row["teachers_3plus_years_pct"]
                ),
                teacher_turnover_pct=_to_optional_float(workforce_row["teacher_turnover_pct"]),
                qts_pct=_to_optional_float(workforce_row["qts_pct"]),
                qualifications_level6_plus_pct=_to_optional_float(
                    workforce_row["qualifications_level6_plus_pct"]
                ),
            )

        finance_latest = None
        if finance_row is not None and finance_row["academic_year"] is not None:
            finance_latest = SchoolFinanceLatest(
                academic_year=str(finance_row["academic_year"]),
                total_income_gbp=_to_optional_float(finance_row["total_income_gbp"]),
                total_expenditure_gbp=_to_optional_float(finance_row["total_expenditure_gbp"]),
                income_per_pupil_gbp=_to_optional_float(finance_row["income_per_pupil_gbp"]),
                expenditure_per_pupil_gbp=_to_optional_float(
                    finance_row["expenditure_per_pupil_gbp"]
                ),
                total_staff_costs_gbp=_to_optional_float(finance_row["total_staff_costs_gbp"]),
                staff_costs_pct_of_expenditure=_to_optional_float(
                    finance_row["staff_costs_pct_of_expenditure"]
                ),
                revenue_reserve_gbp=_to_optional_float(finance_row["revenue_reserve_gbp"]),
                revenue_reserve_per_pupil_gbp=_to_optional_float(
                    finance_row["revenue_reserve_per_pupil_gbp"]
                ),
            )

        leadership_snapshot = None
        if leadership_row is not None:
            leadership_snapshot = SchoolLeadershipSnapshot(
                headteacher_name=_to_optional_str(leadership_row["headteacher_name"]),
                headteacher_start_date=_to_optional_date(leadership_row["headteacher_start_date"]),
                headteacher_tenure_years=_to_optional_float(
                    leadership_row["headteacher_tenure_years"]
                ),
                leadership_turnover_score=_to_optional_float(
                    leadership_row["leadership_turnover_score"]
                ),
            )

        ofsted_latest = None
        if row["ofsted_urn"] is not None:
            most_recent_inspection_date = _max_optional_date(
                (
                    row["inspection_start_date"],
                    row["latest_oeif_inspection_start_date"],
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
                provider_page_url=_to_optional_str(row["provider_page_url"]),
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
                income_score=_to_optional_float(deprivation_row["income_score"]),
                income_rank=_to_optional_int(deprivation_row["income_rank"]),
                income_decile=_to_optional_int(deprivation_row["income_decile"]),
                employment_score=_to_optional_float(deprivation_row["employment_score"]),
                employment_rank=_to_optional_int(deprivation_row["employment_rank"]),
                employment_decile=_to_optional_int(deprivation_row["employment_decile"]),
                education_score=_to_optional_float(deprivation_row["education_score"]),
                education_rank=_to_optional_int(deprivation_row["education_rank"]),
                education_decile=_to_optional_int(deprivation_row["education_decile"]),
                health_score=_to_optional_float(deprivation_row["health_score"]),
                health_rank=_to_optional_int(deprivation_row["health_rank"]),
                health_decile=_to_optional_int(deprivation_row["health_decile"]),
                crime_score=_to_optional_float(deprivation_row["crime_score"]),
                crime_rank=_to_optional_int(deprivation_row["crime_rank"]),
                crime_decile=_to_optional_int(deprivation_row["crime_decile"]),
                barriers_score=_to_optional_float(deprivation_row["barriers_score"]),
                barriers_rank=_to_optional_int(deprivation_row["barriers_rank"]),
                barriers_decile=_to_optional_int(deprivation_row["barriers_decile"]),
                living_environment_score=_to_optional_float(
                    deprivation_row["living_environment_score"]
                ),
                living_environment_rank=_to_optional_int(
                    deprivation_row["living_environment_rank"]
                ),
                living_environment_decile=_to_optional_int(
                    deprivation_row["living_environment_decile"]
                ),
                population_total=_to_optional_int(deprivation_row["population_total"]),
                local_authority_district_code=_to_optional_str(
                    deprivation_row["local_authority_district_code"]
                ),
                local_authority_district_name=_to_optional_str(
                    deprivation_row["local_authority_district_name"]
                ),
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
        population_denominator = deprivation.population_total if deprivation is not None else None
        if latest_crime_row is not None:
            latest_month = latest_crime_row["month"]
            if latest_month is not None:
                total_incidents = sum(
                    (
                        incident_count
                        for incident_count in (
                            _to_optional_int(category_row.get("incident_count"))
                            for category_row in crime_category_rows
                        )
                        if incident_count is not None
                    )
                )
                annual_rates: list[SchoolAreaCrimeAnnualRate] = []
                for annual_row in crime_annual_rows:
                    year = _to_optional_int(annual_row.get("year"))
                    annual_total_incidents = _to_optional_int(annual_row.get("total_incidents"))
                    if year is None or annual_total_incidents is None:
                        continue
                    annual_rates.append(
                        SchoolAreaCrimeAnnualRate(
                            year=year,
                            total_incidents=annual_total_incidents,
                            incidents_per_1000=_incidents_per_1000(
                                incidents=annual_total_incidents,
                                population_total=population_denominator,
                            ),
                        )
                    )
                annual_incidents_per_1000 = tuple(
                    sorted(annual_rates, key=lambda annual_rate: annual_rate.year)
                )
                crime_categories = tuple(
                    SchoolAreaCrimeCategory(
                        category=str(category_row["crime_category"]),
                        incident_count=incident_count,
                    )
                    for category_row in crime_category_rows
                    for incident_count in [_to_optional_int(category_row.get("incident_count"))]
                    if incident_count is not None
                )
                crime = SchoolAreaCrime(
                    radius_miles=round(
                        float(str(latest_crime_row["radius_meters"])) / METERS_PER_MILE, 2
                    ),
                    latest_month=latest_month.strftime("%Y-%m"),
                    total_incidents=total_incidents,
                    population_denominator=population_denominator,
                    incidents_per_1000=_incidents_per_1000(
                        incidents=total_incidents,
                        population_total=population_denominator,
                    ),
                    annual_incidents_per_1000=annual_incidents_per_1000,
                    categories=crime_categories,
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
                population_denominator=population_denominator,
                incidents_per_1000=_incidents_per_1000(
                    incidents=0,
                    population_total=population_denominator,
                ),
                annual_incidents_per_1000=tuple(),
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
        attendance_updated_at = _to_optional_datetime(
            attendance_row["updated_at"] if attendance_row is not None else None
        )
        behaviour_updated_at = _to_optional_datetime(
            behaviour_row["updated_at"] if behaviour_row is not None else None
        )
        workforce_updated_at = _to_optional_datetime(
            workforce_row["updated_at"] if workforce_row is not None else None
        )
        leadership_updated_at = _to_optional_datetime(
            leadership_row["updated_at"] if leadership_row is not None else None
        )
        house_price_updated_at_dt = _to_optional_datetime(house_price_updated_at)
        global_house_price_updated_at_dt = _to_optional_datetime(global_house_price_updated_at)
        house_prices = None
        if latest_house_price_row is not None:
            latest_house_price_month = _to_optional_date(latest_house_price_row["month"])
            latest_average_price = _to_optional_float(latest_house_price_row["average_price"])
            if latest_house_price_month is not None and latest_average_price is not None:
                trend_points = tuple(
                    sorted(
                        (
                            SchoolAreaHousePricePoint(
                                month=month_value.strftime("%Y-%m"),
                                average_price=average_price,
                                annual_change_pct=_to_optional_float(
                                    trend_row["annual_change_pct"]
                                ),
                                monthly_change_pct=_to_optional_float(
                                    trend_row["monthly_change_pct"]
                                ),
                            )
                            for trend_row in house_price_rows
                            for month_value in (_to_optional_date(trend_row["month"]),)
                            for average_price in (_to_optional_float(trend_row["average_price"]),)
                            if month_value is not None and average_price is not None
                        ),
                        key=lambda point: point.month,
                    )
                )
                three_year_change_pct = _compute_three_year_change_pct(
                    latest_month=latest_house_price_month,
                    latest_average_price=latest_average_price,
                    house_price_rows=house_price_rows,
                )
                house_prices = SchoolAreaHousePrices(
                    area_code=_to_optional_str(
                        deprivation_row["local_authority_district_code"]
                        if deprivation_row is not None
                        else None
                    )
                    or "",
                    area_name=str(latest_house_price_row["area_name"]),
                    latest_month=latest_house_price_month.strftime("%Y-%m"),
                    average_price=latest_average_price,
                    annual_change_pct=_to_optional_float(
                        latest_house_price_row["annual_change_pct"]
                    ),
                    monthly_change_pct=_to_optional_float(
                        latest_house_price_row["monthly_change_pct"]
                    ),
                    three_year_change_pct=three_year_change_pct,
                    trend=trend_points,
                )

        area_context = SchoolAreaContext(
            deprivation=deprivation,
            crime=crime,
            house_prices=house_prices,
            coverage=SchoolAreaContextCoverage(
                has_deprivation=deprivation is not None,
                has_crime=crime is not None,
                crime_months_available=effective_crime_months_available,
                has_house_prices=house_prices is not None,
                house_price_months_available=house_price_months_available,
            ),
        )
        finance_applicable = finance_latest is not None or _finance_is_applicable(
            school_type=_to_optional_str(row["type"]),
            trust_name=_to_optional_str(row["trust_name"]),
            trust_flag=_to_optional_str(row["trust_flag"]),
        )

        completeness = SchoolProfileCompleteness(
            demographics=_build_demographics_completeness(
                demographics_latest=demographics_latest,
                demographics_updated_at=_to_optional_datetime(row["demographics_updated_at"]),
            ),
            attendance=_build_attendance_completeness(
                attendance_latest=attendance_latest,
                attendance_updated_at=attendance_updated_at,
            ),
            behaviour=_build_behaviour_completeness(
                behaviour_latest=behaviour_latest,
                behaviour_updated_at=behaviour_updated_at,
            ),
            workforce=_build_workforce_completeness(
                workforce_latest=workforce_latest,
                workforce_updated_at=workforce_updated_at,
            ),
            finance=_build_finance_completeness(
                finance_latest=finance_latest,
                finance_updated_at=_to_optional_datetime(
                    finance_row["updated_at"] if finance_row is not None else None
                ),
                finance_applicable=finance_applicable,
            ),
            leadership=_build_leadership_completeness(
                leadership_snapshot=leadership_snapshot,
                leadership_updated_at=leadership_updated_at,
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
            area_house_prices=_build_area_house_price_completeness(
                postcode=postcode,
                house_prices=house_prices,
                house_price_months_available=house_price_months_available,
                house_price_updated_at=house_price_updated_at_dt,
                school_updated_at=school_updated_at,
                global_house_price_updated_at=global_house_price_updated_at_dt,
                has_global_house_price_data=global_house_price_months_available > 0,
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
                website=_to_optional_str(row["website"]),
                telephone=_to_optional_str(row["telephone"]),
                head_title=_to_optional_str(row["head_title"]),
                head_first_name=_to_optional_str(row["head_first_name"]),
                head_last_name=_to_optional_str(row["head_last_name"]),
                head_job_title=_to_optional_str(row["head_job_title"]),
                address_street=_to_optional_str(row["address_street"]),
                address_locality=_to_optional_str(row["address_locality"]),
                address_line3=_to_optional_str(row["address_line3"]),
                address_town=_to_optional_str(row["address_town"]),
                address_county=_to_optional_str(row["address_county"]),
                statutory_low_age=_to_optional_int(row["statutory_low_age"]),
                statutory_high_age=_to_optional_int(row["statutory_high_age"]),
                gender=_to_optional_str(row["gender"]),
                religious_character=_to_optional_str(row["religious_character"]),
                diocese=_to_optional_str(row["diocese"]),
                admissions_policy=_to_optional_str(row["admissions_policy"]),
                sixth_form=_to_optional_str(row["sixth_form"]),
                nursery_provision=_to_optional_str(row["nursery_provision"]),
                boarders=_to_optional_str(row["boarders"]),
                fsm_pct_gias=_to_optional_float(row["fsm_pct_gias"]),
                trust_name=_to_optional_str(row["trust_name"]),
                trust_flag=_to_optional_str(row["trust_flag"]),
                federation_name=_to_optional_str(row["federation_name"]),
                federation_flag=_to_optional_str(row["federation_flag"]),
                la_name=_to_optional_str(row["la_name"]),
                la_code=_to_optional_str(row["la_code"]),
                urban_rural=_to_optional_str(row["urban_rural"]),
                number_of_boys=_to_optional_int(row["number_of_boys"]),
                number_of_girls=_to_optional_int(row["number_of_girls"]),
                lsoa_code=_to_optional_str(row["lsoa_code"]),
                lsoa_name=_to_optional_str(row["lsoa_name"]),
                last_changed_date=cast(date | None, row["last_changed_date"]),
                lat=float(row["lat"]),
                lng=float(row["lng"]),
            ),
            demographics_latest=demographics_latest,
            attendance_latest=attendance_latest,
            behaviour_latest=behaviour_latest,
            workforce_latest=workforce_latest,
            finance_latest=finance_latest,
            leadership_snapshot=leadership_snapshot,
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


def _to_optional_date(value: object) -> date | None:
    if isinstance(value, date):
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
    months_available = _to_optional_int(row["months_available"])
    if months_available is None:
        return None
    return (
        months_available,
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
        or not demographics_latest.coverage.fsm6_supported
        or not demographics_latest.coverage.gender_supported
        or not demographics_latest.coverage.mobility_supported
        or not demographics_latest.coverage.send_primary_need_supported
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


def _build_attendance_completeness(
    *,
    attendance_latest: SchoolAttendanceLatest | None,
    attendance_updated_at: datetime | None,
) -> SchoolProfileSectionCompleteness:
    if attendance_latest is None:
        return _section_completeness(
            status="unavailable",
            reason_code="source_missing",
            last_updated_at=None,
        )

    if any(
        value is None
        for value in (
            attendance_latest.overall_attendance_pct,
            attendance_latest.overall_absence_pct,
            attendance_latest.persistent_absence_pct,
        )
    ):
        return _section_completeness(
            status="partial",
            reason_code="partial_metric_coverage",
            last_updated_at=attendance_updated_at,
        )

    return _section_completeness(
        status="available",
        reason_code=None,
        last_updated_at=attendance_updated_at,
    )


def _build_behaviour_completeness(
    *,
    behaviour_latest: SchoolBehaviourLatest | None,
    behaviour_updated_at: datetime | None,
) -> SchoolProfileSectionCompleteness:
    if behaviour_latest is None:
        return _section_completeness(
            status="unavailable",
            reason_code="source_missing",
            last_updated_at=None,
        )

    if any(
        value is None
        for value in (
            behaviour_latest.suspensions_count,
            behaviour_latest.suspensions_rate,
            behaviour_latest.permanent_exclusions_count,
            behaviour_latest.permanent_exclusions_rate,
        )
    ):
        return _section_completeness(
            status="partial",
            reason_code="partial_metric_coverage",
            last_updated_at=behaviour_updated_at,
        )

    return _section_completeness(
        status="available",
        reason_code=None,
        last_updated_at=behaviour_updated_at,
    )


def _build_workforce_completeness(
    *,
    workforce_latest: SchoolWorkforceLatest | None,
    workforce_updated_at: datetime | None,
) -> SchoolProfileSectionCompleteness:
    if workforce_latest is None:
        return _section_completeness(
            status="unavailable",
            reason_code="source_missing",
            last_updated_at=None,
        )

    if any(
        value is None
        for value in (
            workforce_latest.pupil_teacher_ratio,
            workforce_latest.supply_staff_pct,
            workforce_latest.teachers_3plus_years_pct,
            workforce_latest.teacher_turnover_pct,
            workforce_latest.qts_pct,
            workforce_latest.qualifications_level6_plus_pct,
        )
    ):
        return _section_completeness(
            status="partial",
            reason_code="partial_metric_coverage",
            last_updated_at=workforce_updated_at,
        )

    return _section_completeness(
        status="available",
        reason_code=None,
        last_updated_at=workforce_updated_at,
    )


def _build_finance_completeness(
    *,
    finance_latest: SchoolFinanceLatest | None,
    finance_updated_at: datetime | None,
    finance_applicable: bool,
) -> SchoolProfileSectionCompleteness:
    if finance_latest is None:
        if not finance_applicable:
            return _section_completeness(
                status="unavailable",
                reason_code="not_applicable",
                last_updated_at=None,
            )
        return _section_completeness(
            status="unavailable",
            reason_code="source_missing",
            last_updated_at=None,
        )

    if any(
        value is None
        for value in (
            finance_latest.total_income_gbp,
            finance_latest.total_expenditure_gbp,
            finance_latest.income_per_pupil_gbp,
            finance_latest.expenditure_per_pupil_gbp,
            finance_latest.total_staff_costs_gbp,
            finance_latest.staff_costs_pct_of_expenditure,
            finance_latest.revenue_reserve_gbp,
            finance_latest.revenue_reserve_per_pupil_gbp,
        )
    ):
        return _section_completeness(
            status="partial",
            reason_code="partial_metric_coverage",
            last_updated_at=finance_updated_at,
        )

    return _section_completeness(
        status="available",
        reason_code=None,
        last_updated_at=finance_updated_at,
    )


def _build_leadership_completeness(
    *,
    leadership_snapshot: SchoolLeadershipSnapshot | None,
    leadership_updated_at: datetime | None,
) -> SchoolProfileSectionCompleteness:
    if leadership_snapshot is None:
        return _section_completeness(
            status="unavailable",
            reason_code="source_missing",
            last_updated_at=None,
        )

    if all(
        value is None
        for value in (
            leadership_snapshot.headteacher_name,
            leadership_snapshot.headteacher_start_date,
            leadership_snapshot.headteacher_tenure_years,
            leadership_snapshot.leadership_turnover_score,
        )
    ):
        return _section_completeness(
            status="partial",
            reason_code="source_not_provided",
            last_updated_at=leadership_updated_at,
        )

    if any(
        value is None
        for value in (
            leadership_snapshot.headteacher_name,
            leadership_snapshot.headteacher_start_date,
            leadership_snapshot.headteacher_tenure_years,
            leadership_snapshot.leadership_turnover_score,
        )
    ):
        return _section_completeness(
            status="partial",
            reason_code="partial_metric_coverage",
            last_updated_at=leadership_updated_at,
        )

    return _section_completeness(
        status="available",
        reason_code=None,
        last_updated_at=leadership_updated_at,
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


def _build_area_house_price_completeness(
    *,
    postcode: str | None,
    house_prices: SchoolAreaHousePrices | None,
    house_price_months_available: int,
    house_price_updated_at: datetime | None,
    school_updated_at: datetime | None,
    global_house_price_updated_at: datetime | None,
    has_global_house_price_data: bool,
) -> SchoolProfileSectionCompleteness:
    if postcode is None or not postcode.strip():
        return _section_completeness(
            status="unavailable",
            reason_code="not_applicable",
            last_updated_at=None,
        )
    if house_prices is None:
        if not has_global_house_price_data:
            return _section_completeness(
                status="unavailable",
                reason_code="source_missing",
                last_updated_at=None,
            )
        if (
            school_updated_at is not None
            and global_house_price_updated_at is not None
            and school_updated_at > global_house_price_updated_at
        ):
            return _section_completeness(
                status="unavailable",
                reason_code="stale_after_school_refresh",
                last_updated_at=global_house_price_updated_at,
            )
        return _section_completeness(
            status="unavailable",
            reason_code="source_coverage_gap",
            last_updated_at=global_house_price_updated_at,
        )
    if house_price_months_available < 36:
        return _section_completeness(
            status="partial",
            reason_code="insufficient_years_published",
            last_updated_at=house_price_updated_at,
        )
    return _section_completeness(
        status="available",
        reason_code=None,
        last_updated_at=house_price_updated_at,
    )


def _incidents_per_1000(*, incidents: int, population_total: int | None) -> float | None:
    if population_total is None or population_total <= 0:
        return None
    return round((float(incidents) / float(population_total)) * 1000.0, 2)


def _compute_three_year_change_pct(
    *,
    latest_month: date,
    latest_average_price: float,
    house_price_rows: Sequence[Mapping[str, object]],
) -> float | None:
    if latest_average_price <= 0:
        return None

    target_year = latest_month.year - 3
    target_month = latest_month.month
    target_price: float | None = None
    for row in house_price_rows:
        row_month = _to_optional_date(row["month"])
        if row_month is None:
            continue
        if row_month.year == target_year and row_month.month == target_month:
            target_price = _to_optional_float(row["average_price"])
            break

    if target_price is None and len(house_price_rows) >= 36:
        target_price = _to_optional_float(house_price_rows[-1]["average_price"])

    if target_price is None or target_price <= 0:
        return None
    return round(((latest_average_price - target_price) / target_price) * 100.0, 2)


def _finance_is_applicable(
    *,
    school_type: str | None,
    trust_name: str | None,
    trust_flag: str | None,
) -> bool:
    normalized_type = (school_type or "").strip().casefold()
    return (
        "academy" in normalized_type
        or bool((trust_name or "").strip())
        or bool((trust_flag or "").strip())
    )


def _supports_direct_fsm(*, source_dataset_id: object, fsm_pct: object) -> bool:
    source_token = _to_optional_str(source_dataset_id)
    if source_token is not None and "spc:" in source_token:
        return True

    # Legacy rows may not include family tokens in source_dataset_id.
    return _to_optional_float(fsm_pct) is not None
