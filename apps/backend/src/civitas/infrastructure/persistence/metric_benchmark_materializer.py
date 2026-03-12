from __future__ import annotations

from collections.abc import Mapping

from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection

SIMILAR_SCHOOL_MIN_COHORT_SIZE = 30

_TABLE_METRIC_COLUMNS: tuple[tuple[str, str, tuple[tuple[str, str], ...]], ...] = (
    (
        "school_demographics_yearly",
        "demographics",
        (
            ("disadvantaged_pct", "disadvantaged_pct"),
            ("fsm_pct", "fsm_pct"),
            ("fsm6_pct", "fsm6_pct"),
            ("sen_pct", "sen_pct"),
            ("ehcp_pct", "ehcp_pct"),
            ("eal_pct", "eal_pct"),
            ("first_language_english_pct", "first_language_english_pct"),
            ("first_language_unclassified_pct", "first_language_unclassified_pct"),
            ("male_pct", "male_pct"),
            ("female_pct", "female_pct"),
            ("pupil_mobility_pct", "pupil_mobility_pct"),
        ),
    ),
    (
        "school_attendance_yearly",
        "attendance",
        (
            ("overall_attendance_pct", "overall_attendance_pct"),
            ("overall_absence_pct", "overall_absence_pct"),
            ("persistent_absence_pct", "persistent_absence_pct"),
        ),
    ),
    (
        "school_behaviour_yearly",
        "behaviour",
        (
            ("suspensions_count", "suspensions_count"),
            ("suspensions_rate", "suspensions_rate"),
            ("permanent_exclusions_count", "permanent_exclusions_count"),
            ("permanent_exclusions_rate", "permanent_exclusions_rate"),
        ),
    ),
    (
        "school_workforce_yearly",
        "workforce",
        (
            ("pupil_teacher_ratio", "pupil_teacher_ratio"),
            ("supply_staff_pct", "supply_staff_pct"),
            ("teachers_3plus_years_pct", "teachers_3plus_years_pct"),
            ("teacher_turnover_pct", "teacher_turnover_pct"),
            ("qts_pct", "qts_pct"),
            ("qualifications_level6_plus_pct", "qualifications_level6_plus_pct"),
            ("teacher_headcount_total", "teacher_headcount_total"),
            ("teacher_fte_total", "teacher_fte_total"),
            ("support_staff_headcount_total", "support_staff_headcount_total"),
            ("support_staff_fte_total", "support_staff_fte_total"),
            ("leadership_share_of_teachers", "leadership_share_of_teachers"),
            ("teacher_average_mean_salary_gbp", "teacher_average_mean_salary_gbp"),
            ("teacher_average_median_salary_gbp", "teacher_average_median_salary_gbp"),
            ("teachers_on_leadership_pay_range_pct", "teachers_on_leadership_pay_range_pct"),
            ("teacher_absence_pct", "teacher_absence_pct"),
            ("teacher_absence_days_total", "teacher_absence_days_total"),
            ("teacher_absence_days_average", "teacher_absence_days_average"),
            (
                "teacher_absence_days_average_all_teachers",
                "teacher_absence_days_average_all_teachers",
            ),
            ("teacher_vacancy_count", "teacher_vacancy_count"),
            ("teacher_vacancy_rate", "teacher_vacancy_rate"),
            ("teaching_assistants_per_100_pupils", "teaching_assistants_per_100_pupils"),
            (
                "non_classroom_support_staff_per_100_pupils",
                "non_classroom_support_staff_per_100_pupils",
            ),
            ("admin_clerical_staff_per_100_pupils", "admin_clerical_staff_per_100_pupils"),
            ("all_support_staff_per_100_pupils", "all_support_staff_per_100_pupils"),
            ("third_party_support_staff_headcount", "third_party_support_staff_headcount"),
            ("agency_teachers_headcount", "agency_teachers_headcount"),
        ),
    ),
    (
        "school_financials_yearly",
        "finance",
        (
            ("finance_income_per_pupil_gbp", "income_per_pupil_gbp"),
            ("finance_expenditure_per_pupil_gbp", "expenditure_per_pupil_gbp"),
            (
                "finance_staff_costs_pct_of_expenditure",
                "staff_costs_pct_of_expenditure",
            ),
            (
                "finance_revenue_reserve_per_pupil_gbp",
                "revenue_reserve_per_pupil_gbp",
            ),
            (
                "finance_teaching_staff_costs_per_pupil_gbp",
                "teaching_staff_costs_per_pupil_gbp",
            ),
            (
                "finance_supply_staff_costs_pct_of_staff_costs",
                "supply_staff_costs_pct_of_staff_costs",
            ),
        ),
    ),
    (
        "school_admissions_yearly",
        "admissions",
        (
            ("admissions_oversubscription_ratio", "oversubscription_ratio"),
            (
                "admissions_first_preference_offer_rate",
                "first_preference_offer_rate",
            ),
            ("admissions_any_preference_offer_rate", "any_preference_offer_rate"),
            ("admissions_cross_la_applications", "cross_la_applications"),
            ("admissions_cross_la_offers", "cross_la_offers"),
        ),
    ),
    (
        "school_destinations_benchmark_yearly",
        "destinations",
        (
            ("ks4_overall_pct", "ks4_overall_pct"),
            ("ks4_education_pct", "ks4_education_pct"),
            ("ks4_apprenticeship_pct", "ks4_apprenticeship_pct"),
            ("ks4_employment_pct", "ks4_employment_pct"),
            ("ks4_not_sustained_pct", "ks4_not_sustained_pct"),
            ("ks4_activity_unknown_pct", "ks4_activity_unknown_pct"),
            ("study_16_18_overall_pct", "study_16_18_overall_pct"),
            ("study_16_18_education_pct", "study_16_18_education_pct"),
            (
                "study_16_18_apprenticeship_pct",
                "study_16_18_apprenticeship_pct",
            ),
            ("study_16_18_employment_pct", "study_16_18_employment_pct"),
            ("study_16_18_not_sustained_pct", "study_16_18_not_sustained_pct"),
            (
                "study_16_18_activity_unknown_pct",
                "study_16_18_activity_unknown_pct",
            ),
        ),
    ),
    (
        "school_performance_yearly",
        "performance",
        (
            ("attainment8_average", "attainment8_average"),
            ("progress8_average", "progress8_average"),
            ("progress8_disadvantaged_gap", "progress8_disadvantaged_gap"),
            ("engmath_5_plus_pct", "engmath_5_plus_pct"),
            ("ebacc_entry_pct", "ebacc_entry_pct"),
            ("ks2_reading_expected_pct", "ks2_reading_expected_pct"),
            ("ks2_writing_expected_pct", "ks2_writing_expected_pct"),
            ("ks2_maths_expected_pct", "ks2_maths_expected_pct"),
            ("ks2_combined_expected_pct", "ks2_combined_expected_pct"),
            ("ks2_combined_higher_pct", "ks2_combined_higher_pct"),
        ),
    ),
)


def load_metric_benchmark_scope_rows(
    connection: Connection,
    urn: str,
) -> tuple[Mapping[str, object], ...]:
    if not _has_percentile_tables(connection):
        return ()

    rows = (
        connection.execute(
            text(
                """
                SELECT
                    percentiles.metric_key,
                    percentiles.academic_year,
                    percentiles.metric_value AS school_value,
                    percentiles.benchmark_scope,
                    distributions.mean_value AS benchmark_value,
                    percentiles.percentile_rank,
                    cohorts.school_count,
                    cohorts.cohort_label,
                    NULLIF(cohorts.definition_json ->> 'benchmark_area', '') AS benchmark_area
                FROM school_metric_percentiles_yearly AS percentiles
                INNER JOIN metric_benchmark_cohorts_yearly AS cohorts
                    ON cohorts.cohort_id = percentiles.cohort_id
                LEFT JOIN metric_benchmark_distributions_yearly AS distributions
                    ON distributions.cohort_id = percentiles.cohort_id
                WHERE percentiles.urn = :urn
                ORDER BY
                    percentiles.metric_key,
                    percentiles.academic_year,
                    CASE percentiles.benchmark_scope
                        WHEN 'national' THEN 1
                        WHEN 'local_authority_district' THEN 2
                        WHEN 'phase' THEN 3
                        WHEN 'similar_school' THEN 4
                        ELSE 9
                    END
                """
            ),
            {"urn": urn},
        )
        .mappings()
        .all()
    )
    return tuple(dict(row) for row in rows)


def rebuild_metric_benchmark_cache(connection: Connection) -> int:
    if not _has_percentile_tables(connection):
        return 0

    updated_at_expression = (
        "timezone('utc', now())" if connection.dialect.name == "postgresql" else "CURRENT_TIMESTAMP"
    )
    definition_json_expression = (
        "definition_json::jsonb" if connection.dialect.name == "postgresql" else "definition_json"
    )

    connection.execute(text("DELETE FROM school_metric_percentiles_yearly"))
    connection.execute(text("DELETE FROM metric_benchmark_distributions_yearly"))
    connection.execute(text("DELETE FROM metric_benchmark_cohorts_yearly"))
    if _table_exists(connection, "metric_benchmarks_yearly"):
        connection.execute(text("DELETE FROM metric_benchmarks_yearly"))

    _build_source_rows(connection)
    _build_similar_school_stage_rows(connection)
    _build_cohort_memberships(connection)
    _insert_benchmark_tables(
        connection=connection,
        updated_at_expression=updated_at_expression,
        definition_json_expression=definition_json_expression,
    )

    if _table_exists(connection, "metric_benchmarks_yearly"):
        return int(
            connection.execute(text("SELECT count(*) FROM metric_benchmarks_yearly")).scalar_one()
        )

    return int(
        connection.execute(
            text("SELECT count(*) FROM school_metric_percentiles_yearly")
        ).scalar_one()
    )


def _build_source_rows(connection: Connection) -> None:
    metric_row_selects = list(_build_metric_row_selects(connection))
    metric_row_selects.extend(
        (
            """
                SELECT yearly_crime.urn, yearly_crime.academic_year, 'area_crime_incidents_per_1000', yearly_crime.area_crime_incidents_per_1000
                FROM area_crime_yearly AS yearly_crime
            """.strip(),
            """
                SELECT yearly_prices.urn, yearly_prices.academic_year, metric.metric_key, metric.metric_value
                FROM area_house_price_yearly AS yearly_prices
                CROSS JOIN LATERAL (
                    VALUES
                        ('area_house_price_average', yearly_prices.area_house_price_average::double precision),
                        ('area_house_price_annual_change_pct', yearly_prices.area_house_price_annual_change_pct::double precision)
                ) AS metric(metric_key, metric_value)
            """.strip(),
        )
    )
    metric_rows_sql = "\n\n                UNION ALL\n\n".join(metric_row_selects)
    connection.execute(
        text(
            f"""
            CREATE TEMP TABLE tmp_metric_benchmark_source_rows ON COMMIT DROP AS
            WITH school_geo AS (
                SELECT
                    schools.urn,
                    schools.phase,
                    coalesce(deprivation.local_authority_district_code, schools.la_code) AS lad_code,
                    coalesce(deprivation.local_authority_district_name, schools.la_name) AS lad_name,
                    deprivation.population_total AS population_total,
                    schools.type AS establishment_type,
                    schools.admissions_policy,
                    schools.religious_character,
                    schools.urban_rural,
                    schools.pupil_count
                FROM schools
                LEFT JOIN LATERAL (
                    SELECT cache.lsoa_code
                    FROM postcode_cache AS cache
                    WHERE replace(upper(cache.postcode), ' ', '') =
                          replace(upper(schools.postcode), ' ', '')
                    ORDER BY cache.cached_at DESC
                    LIMIT 1
                ) AS cache ON TRUE
                LEFT JOIN area_deprivation AS deprivation
                    ON deprivation.lsoa_code = cache.lsoa_code
            ),
            school_band_dimensions AS (
                SELECT
                    demographics.urn,
                    demographics.academic_year,
                    geo.phase,
                    geo.lad_code,
                    geo.lad_name,
                    CASE
                        WHEN geo.establishment_type IS NULL OR btrim(geo.establishment_type) = '' THEN 'unknown'
                        WHEN lower(geo.establishment_type) LIKE '%grammar%' THEN 'grammar'
                        WHEN lower(geo.establishment_type) LIKE '%special%' THEN 'special'
                        WHEN lower(geo.establishment_type) LIKE '%academy%' THEN 'academy'
                        WHEN lower(geo.establishment_type) LIKE '%community%'
                            OR lower(geo.establishment_type) LIKE '%voluntary%'
                            OR lower(geo.establishment_type) LIKE '%foundation%'
                            OR lower(geo.establishment_type) LIKE '%maintained%'
                            THEN 'maintained'
                        ELSE lower(regexp_replace(geo.establishment_type, '[^a-z0-9]+', '_', 'g'))
                    END AS establishment_type_group,
                    CASE
                        WHEN geo.admissions_policy IS NULL OR btrim(geo.admissions_policy) = '' THEN 'missing'
                        ELSE lower(regexp_replace(geo.admissions_policy, '[^a-z0-9]+', '_', 'g'))
                    END AS admissions_policy_group,
                    CASE
                        WHEN geo.religious_character IS NULL OR btrim(geo.religious_character) = '' THEN 'missing'
                        ELSE lower(regexp_replace(geo.religious_character, '[^a-z0-9]+', '_', 'g'))
                    END AS religious_character_group,
                    CASE
                        WHEN geo.urban_rural IS NULL OR btrim(geo.urban_rural) = '' THEN 'unknown'
                        WHEN lower(geo.urban_rural) LIKE '%rural%' THEN 'rural'
                        WHEN lower(geo.urban_rural) LIKE '%urban%' THEN 'urban'
                        ELSE lower(regexp_replace(geo.urban_rural, '[^a-z0-9]+', '_', 'g'))
                    END AS urban_rural_group,
                    coalesce(
                        demographics.total_pupils::double precision,
                        geo.pupil_count::double precision
                    ) AS pupil_roll_value,
                    demographics.fsm_pct::double precision AS fsm_pct_value,
                    coalesce(
                        demographics.ehcp_pct::double precision,
                        demographics.sen_pct::double precision
                    ) AS need_pct_value
                FROM school_demographics_yearly AS demographics
                INNER JOIN school_geo AS geo
                    ON geo.urn = demographics.urn
            ),
            dimension_rows AS (
                SELECT
                    dims.urn,
                    dims.academic_year,
                    dims.phase,
                    dims.lad_code,
                    dims.lad_name,
                    dims.establishment_type_group,
                    dims.admissions_policy_group,
                    dims.religious_character_group,
                    dims.urban_rural_group,
                    CASE
                        WHEN dims.pupil_roll_value IS NULL THEN NULL
                        WHEN dims.pupil_roll_value < 200 THEN 1
                        WHEN dims.pupil_roll_value < 400 THEN 2
                        WHEN dims.pupil_roll_value < 700 THEN 3
                        WHEN dims.pupil_roll_value < 1000 THEN 4
                        ELSE 5
                    END AS pupil_roll_band_narrow,
                    CASE
                        WHEN dims.pupil_roll_value IS NULL THEN NULL
                        WHEN dims.pupil_roll_value < 400 THEN 1
                        WHEN dims.pupil_roll_value < 1000 THEN 2
                        ELSE 3
                    END AS pupil_roll_band_wide,
                    CASE
                        WHEN dims.fsm_pct_value IS NULL THEN NULL
                        WHEN dims.fsm_pct_value < 10 THEN 1
                        WHEN dims.fsm_pct_value < 20 THEN 2
                        WHEN dims.fsm_pct_value < 30 THEN 3
                        WHEN dims.fsm_pct_value < 40 THEN 4
                        ELSE 5
                    END AS fsm_band_narrow,
                    CASE
                        WHEN dims.fsm_pct_value IS NULL THEN NULL
                        WHEN dims.fsm_pct_value < 15 THEN 1
                        WHEN dims.fsm_pct_value < 30 THEN 2
                        ELSE 3
                    END AS fsm_band_wide,
                    CASE
                        WHEN dims.need_pct_value IS NULL THEN NULL
                        WHEN dims.need_pct_value < 5 THEN 1
                        WHEN dims.need_pct_value < 10 THEN 2
                        WHEN dims.need_pct_value < 15 THEN 3
                        WHEN dims.need_pct_value < 20 THEN 4
                        ELSE 5
                    END AS need_band_narrow,
                    CASE
                        WHEN dims.need_pct_value IS NULL THEN NULL
                        WHEN dims.need_pct_value < 10 THEN 1
                        WHEN dims.need_pct_value < 20 THEN 2
                        ELSE 3
                    END AS need_band_wide
                FROM school_band_dimensions AS dims
            ),
            area_crime_yearly AS (
                SELECT
                    context.urn,
                    extract(year from context.month)::int::text AS academic_year,
                    (
                        sum(context.incident_count)::double precision /
                        NULLIF(max(geo.population_total), 0)::double precision
                    ) * 1000.0 AS area_crime_incidents_per_1000
                FROM area_crime_context AS context
                INNER JOIN school_geo AS geo
                    ON geo.urn = context.urn
                GROUP BY context.urn, extract(year from context.month)::int
            ),
            area_house_price_yearly AS (
                SELECT
                    geo.urn,
                    extract(year from prices.month)::int::text AS academic_year,
                    avg(prices.average_price)::double precision AS area_house_price_average,
                    avg(prices.annual_change_pct)::double precision AS area_house_price_annual_change_pct
                FROM school_geo AS geo
                INNER JOIN area_house_price_context AS prices
                    ON prices.area_code = geo.lad_code
                GROUP BY geo.urn, extract(year from prices.month)::int
            ),
            metric_rows AS (
                {metric_rows_sql}
            )
            SELECT
                metric_rows.urn,
                metric_rows.academic_year,
                metric_rows.metric_key,
                metric_rows.metric_value,
                dimension_rows.phase,
                dimension_rows.lad_code,
                dimension_rows.lad_name,
                coalesce(dimension_rows.establishment_type_group, 'unknown') AS establishment_type_group,
                coalesce(dimension_rows.admissions_policy_group, 'missing') AS admissions_policy_group,
                coalesce(dimension_rows.religious_character_group, 'missing') AS religious_character_group,
                coalesce(dimension_rows.urban_rural_group, 'unknown') AS urban_rural_group,
                dimension_rows.pupil_roll_band_narrow,
                dimension_rows.pupil_roll_band_wide,
                dimension_rows.fsm_band_narrow,
                dimension_rows.fsm_band_wide,
                dimension_rows.need_band_narrow,
                dimension_rows.need_band_wide
            FROM metric_rows
            LEFT JOIN dimension_rows
                ON dimension_rows.urn = metric_rows.urn
               AND dimension_rows.academic_year = metric_rows.academic_year
            WHERE metric_rows.metric_value IS NOT NULL
            """
        )
    )


def _build_metric_row_selects(connection: Connection) -> tuple[str, ...]:
    selects: list[str] = []
    for table_name, alias, metrics in _TABLE_METRIC_COLUMNS:
        values_sql = _build_metric_values_sql(connection, table_name, alias, metrics)
        if values_sql is None:
            continue
        selects.append(
            f"""
                SELECT {alias}.urn, {alias}.academic_year, metric.metric_key, metric.metric_value
                FROM {table_name} AS {alias}
                CROSS JOIN LATERAL (
                    VALUES
{values_sql}
                ) AS metric(metric_key, metric_value)
            """.strip()
        )
    return tuple(selects)


def _build_metric_values_sql(
    connection: Connection,
    table_name: str,
    alias: str,
    metrics: tuple[tuple[str, str], ...],
) -> str | None:
    if not _table_exists(connection, table_name):
        return None

    available_columns = _table_columns(connection, table_name)
    value_rows = [
        f"                        ('{metric_key}', {alias}.{column_name}::double precision)"
        for metric_key, column_name in metrics
        if column_name in available_columns
    ]
    if len(value_rows) == 0:
        return None
    return ",\n".join(value_rows)


def _table_columns(connection: Connection, table_name: str) -> frozenset[str]:
    return frozenset(column["name"] for column in inspect(connection).get_columns(table_name))


def _build_similar_school_stage_rows(connection: Connection) -> None:
    connection.execute(
        text(
            """
            CREATE TEMP TABLE tmp_similar_stage_rows ON COMMIT DROP AS
            SELECT
                source_rows.urn,
                source_rows.academic_year,
                source_rows.metric_key,
                source_rows.metric_value,
                0 AS stage_order,
                concat_ws(
                    '|',
                    'stage_0',
                    coalesce(source_rows.phase, 'unknown'),
                    coalesce(source_rows.establishment_type_group, 'unknown'),
                    coalesce(source_rows.admissions_policy_group, 'missing'),
                    coalesce(source_rows.religious_character_group, 'missing'),
                    coalesce(source_rows.urban_rural_group, 'unknown'),
                    coalesce(source_rows.pupil_roll_band_narrow::text, 'na'),
                    coalesce(source_rows.fsm_band_narrow::text, 'na'),
                    coalesce(source_rows.need_band_narrow::text, 'na')
                ) AS cohort_signature,
                'Similar Schools' AS cohort_label,
                jsonb_build_object(
                    'benchmark_area', 'similar_school',
                    'phase', source_rows.phase,
                    'establishment_type_group', source_rows.establishment_type_group,
                    'admissions_policy', source_rows.admissions_policy_group,
                    'religious_character', source_rows.religious_character_group,
                    'urban_rural', source_rows.urban_rural_group,
                    'pupil_roll_band', source_rows.pupil_roll_band_narrow,
                    'pupil_roll_band_granularity', 'fixed_narrow',
                    'fsm_band', source_rows.fsm_band_narrow,
                    'fsm_band_granularity', 'fixed_narrow',
                    'need_band', source_rows.need_band_narrow,
                    'need_band_granularity', 'fixed_narrow',
                    'fallback_stage', 0
                ) AS definition_json
            FROM tmp_metric_benchmark_source_rows AS source_rows

            UNION ALL

            SELECT
                source_rows.urn,
                source_rows.academic_year,
                source_rows.metric_key,
                source_rows.metric_value,
                1 AS stage_order,
                concat_ws(
                    '|',
                    'stage_1',
                    coalesce(source_rows.phase, 'unknown'),
                    coalesce(source_rows.establishment_type_group, 'unknown'),
                    coalesce(source_rows.admissions_policy_group, 'missing'),
                    'any_religion',
                    coalesce(source_rows.urban_rural_group, 'unknown'),
                    coalesce(source_rows.pupil_roll_band_narrow::text, 'na'),
                    coalesce(source_rows.fsm_band_narrow::text, 'na'),
                    coalesce(source_rows.need_band_narrow::text, 'na')
                ) AS cohort_signature,
                'Similar Schools' AS cohort_label,
                jsonb_build_object(
                    'benchmark_area', 'similar_school',
                    'phase', source_rows.phase,
                    'establishment_type_group', source_rows.establishment_type_group,
                    'admissions_policy', source_rows.admissions_policy_group,
                    'religious_character', null,
                    'urban_rural', source_rows.urban_rural_group,
                    'pupil_roll_band', source_rows.pupil_roll_band_narrow,
                    'pupil_roll_band_granularity', 'fixed_narrow',
                    'fsm_band', source_rows.fsm_band_narrow,
                    'fsm_band_granularity', 'fixed_narrow',
                    'need_band', source_rows.need_band_narrow,
                    'need_band_granularity', 'fixed_narrow',
                    'fallback_stage', 1
                ) AS definition_json
            FROM tmp_metric_benchmark_source_rows AS source_rows

            UNION ALL

            SELECT
                source_rows.urn,
                source_rows.academic_year,
                source_rows.metric_key,
                source_rows.metric_value,
                2 AS stage_order,
                concat_ws(
                    '|',
                    'stage_2',
                    coalesce(source_rows.phase, 'unknown'),
                    coalesce(source_rows.establishment_type_group, 'unknown'),
                    coalesce(source_rows.admissions_policy_group, 'missing'),
                    'any_religion',
                    coalesce(source_rows.urban_rural_group, 'unknown'),
                    coalesce(source_rows.pupil_roll_band_narrow::text, 'na'),
                    coalesce(source_rows.fsm_band_narrow::text, 'na'),
                    coalesce(source_rows.need_band_wide::text, 'na')
                ) AS cohort_signature,
                'Similar Schools' AS cohort_label,
                jsonb_build_object(
                    'benchmark_area', 'similar_school',
                    'phase', source_rows.phase,
                    'establishment_type_group', source_rows.establishment_type_group,
                    'admissions_policy', source_rows.admissions_policy_group,
                    'religious_character', null,
                    'urban_rural', source_rows.urban_rural_group,
                    'pupil_roll_band', source_rows.pupil_roll_band_narrow,
                    'pupil_roll_band_granularity', 'fixed_narrow',
                    'fsm_band', source_rows.fsm_band_narrow,
                    'fsm_band_granularity', 'fixed_narrow',
                    'need_band', source_rows.need_band_wide,
                    'need_band_granularity', 'fixed_wide',
                    'fallback_stage', 2
                ) AS definition_json
            FROM tmp_metric_benchmark_source_rows AS source_rows

            UNION ALL

            SELECT
                source_rows.urn,
                source_rows.academic_year,
                source_rows.metric_key,
                source_rows.metric_value,
                3 AS stage_order,
                concat_ws(
                    '|',
                    'stage_3',
                    coalesce(source_rows.phase, 'unknown'),
                    coalesce(source_rows.establishment_type_group, 'unknown'),
                    coalesce(source_rows.admissions_policy_group, 'missing'),
                    'any_religion',
                    coalesce(source_rows.urban_rural_group, 'unknown'),
                    coalesce(source_rows.pupil_roll_band_narrow::text, 'na'),
                    coalesce(source_rows.fsm_band_wide::text, 'na'),
                    coalesce(source_rows.need_band_wide::text, 'na')
                ) AS cohort_signature,
                'Similar Schools' AS cohort_label,
                jsonb_build_object(
                    'benchmark_area', 'similar_school',
                    'phase', source_rows.phase,
                    'establishment_type_group', source_rows.establishment_type_group,
                    'admissions_policy', source_rows.admissions_policy_group,
                    'religious_character', null,
                    'urban_rural', source_rows.urban_rural_group,
                    'pupil_roll_band', source_rows.pupil_roll_band_narrow,
                    'pupil_roll_band_granularity', 'fixed_narrow',
                    'fsm_band', source_rows.fsm_band_wide,
                    'fsm_band_granularity', 'fixed_wide',
                    'need_band', source_rows.need_band_wide,
                    'need_band_granularity', 'fixed_wide',
                    'fallback_stage', 3
                ) AS definition_json
            FROM tmp_metric_benchmark_source_rows AS source_rows

            UNION ALL

            SELECT
                source_rows.urn,
                source_rows.academic_year,
                source_rows.metric_key,
                source_rows.metric_value,
                4 AS stage_order,
                concat_ws(
                    '|',
                    'stage_4',
                    coalesce(source_rows.phase, 'unknown'),
                    coalesce(source_rows.establishment_type_group, 'unknown'),
                    coalesce(source_rows.admissions_policy_group, 'missing'),
                    'any_religion',
                    coalesce(source_rows.urban_rural_group, 'unknown'),
                    coalesce(source_rows.pupil_roll_band_wide::text, 'na'),
                    coalesce(source_rows.fsm_band_wide::text, 'na'),
                    coalesce(source_rows.need_band_wide::text, 'na')
                ) AS cohort_signature,
                'Similar Schools' AS cohort_label,
                jsonb_build_object(
                    'benchmark_area', 'similar_school',
                    'phase', source_rows.phase,
                    'establishment_type_group', source_rows.establishment_type_group,
                    'admissions_policy', source_rows.admissions_policy_group,
                    'religious_character', null,
                    'urban_rural', source_rows.urban_rural_group,
                    'pupil_roll_band', source_rows.pupil_roll_band_wide,
                    'pupil_roll_band_granularity', 'fixed_wide',
                    'fsm_band', source_rows.fsm_band_wide,
                    'fsm_band_granularity', 'fixed_wide',
                    'need_band', source_rows.need_band_wide,
                    'need_band_granularity', 'fixed_wide',
                    'fallback_stage', 4
                ) AS definition_json
            FROM tmp_metric_benchmark_source_rows AS source_rows
            """
        )
    )
    connection.execute(
        text(
            """
            CREATE TEMP TABLE tmp_similar_stage_counts ON COMMIT DROP AS
            SELECT
                academic_year,
                metric_key,
                stage_order,
                cohort_signature,
                count(*)::integer AS school_count
            FROM tmp_similar_stage_rows
            GROUP BY academic_year, metric_key, stage_order, cohort_signature
            """
        )
    )
    connection.execute(
        text(
            """
            CREATE TEMP TABLE tmp_selected_similar_school_cohorts ON COMMIT DROP AS
            SELECT DISTINCT ON (stage_rows.urn, stage_rows.academic_year, stage_rows.metric_key)
                stage_rows.urn,
                stage_rows.academic_year,
                stage_rows.metric_key,
                stage_rows.stage_order,
                stage_rows.cohort_signature,
                stage_rows.cohort_label,
                stage_rows.definition_json,
                stage_counts.school_count
            FROM tmp_similar_stage_rows AS stage_rows
            INNER JOIN tmp_similar_stage_counts AS stage_counts
                ON stage_counts.academic_year = stage_rows.academic_year
               AND stage_counts.metric_key = stage_rows.metric_key
               AND stage_counts.stage_order = stage_rows.stage_order
               AND stage_counts.cohort_signature = stage_rows.cohort_signature
            WHERE stage_counts.school_count >= :minimum_school_count
            ORDER BY
                stage_rows.urn,
                stage_rows.academic_year,
                stage_rows.metric_key,
                stage_rows.stage_order
            """
        ),
        {"minimum_school_count": SIMILAR_SCHOOL_MIN_COHORT_SIZE},
    )


def _build_cohort_memberships(connection: Connection) -> None:
    connection.execute(
        text(
            """
            CREATE TEMP TABLE tmp_metric_benchmark_cohort_memberships ON COMMIT DROP AS
            SELECT
                source_rows.metric_key,
                source_rows.academic_year,
                'national' AS benchmark_scope,
                'england' AS benchmark_area,
                'scope_average' AS cohort_type,
                'England' AS cohort_label,
                'national|england' AS cohort_signature,
                jsonb_build_object('benchmark_area', 'england', 'scope', 'national') AS definition_json,
                source_rows.urn,
                source_rows.metric_value
            FROM tmp_metric_benchmark_source_rows AS source_rows

            UNION ALL

            SELECT
                source_rows.metric_key,
                source_rows.academic_year,
                'local_authority_district' AS benchmark_scope,
                source_rows.lad_code AS benchmark_area,
                'scope_average' AS cohort_type,
                coalesce(source_rows.lad_name, source_rows.lad_code, 'Unknown') AS cohort_label,
                concat('local_authority_district|', source_rows.lad_code) AS cohort_signature,
                jsonb_build_object('benchmark_area', source_rows.lad_code, 'scope', 'local_authority_district') AS definition_json,
                source_rows.urn,
                source_rows.metric_value
            FROM tmp_metric_benchmark_source_rows AS source_rows
            WHERE source_rows.lad_code IS NOT NULL

            UNION ALL

            SELECT
                source_rows.metric_key,
                source_rows.academic_year,
                'phase' AS benchmark_scope,
                source_rows.phase AS benchmark_area,
                'scope_average' AS cohort_type,
                coalesce(source_rows.phase, 'Unknown') AS cohort_label,
                concat('phase|', source_rows.phase) AS cohort_signature,
                jsonb_build_object('benchmark_area', source_rows.phase, 'scope', 'phase') AS definition_json,
                source_rows.urn,
                source_rows.metric_value
            FROM tmp_metric_benchmark_source_rows AS source_rows
            WHERE source_rows.phase IS NOT NULL

            UNION ALL

            SELECT
                stage_rows.metric_key,
                stage_rows.academic_year,
                'similar_school' AS benchmark_scope,
                'similar_school' AS benchmark_area,
                'similar_school' AS cohort_type,
                selected.cohort_label,
                selected.cohort_signature,
                selected.definition_json,
                stage_rows.urn,
                stage_rows.metric_value
            FROM (
                SELECT DISTINCT
                    academic_year,
                    metric_key,
                    stage_order,
                    cohort_signature,
                    cohort_label,
                    definition_json
                FROM tmp_selected_similar_school_cohorts
            ) AS selected
            INNER JOIN tmp_similar_stage_rows AS stage_rows
                ON stage_rows.academic_year = selected.academic_year
               AND stage_rows.metric_key = selected.metric_key
               AND stage_rows.stage_order = selected.stage_order
               AND stage_rows.cohort_signature = selected.cohort_signature
            """
        )
    )


def _insert_benchmark_tables(
    *,
    connection: Connection,
    updated_at_expression: str,
    definition_json_expression: str,
) -> None:
    connection.execute(
        text(
            """
            CREATE TEMP TABLE tmp_metric_benchmark_cohorts ON COMMIT DROP AS
            SELECT
                (
                    substr(
                        md5(
                            memberships.metric_key || '|' ||
                            memberships.academic_year || '|' ||
                            memberships.benchmark_scope || '|' ||
                            coalesce(memberships.benchmark_area, '') || '|' ||
                            memberships.cohort_type || '|' ||
                            memberships.cohort_signature || '|' ||
                            memberships.definition_json::text
                        ),
                        1,
                        8
                    ) || '-' ||
                    substr(
                        md5(
                            memberships.metric_key || '|' ||
                            memberships.academic_year || '|' ||
                            memberships.benchmark_scope || '|' ||
                            coalesce(memberships.benchmark_area, '') || '|' ||
                            memberships.cohort_type || '|' ||
                            memberships.cohort_signature || '|' ||
                            memberships.definition_json::text
                        ),
                        9,
                        4
                    ) || '-' ||
                    substr(
                        md5(
                            memberships.metric_key || '|' ||
                            memberships.academic_year || '|' ||
                            memberships.benchmark_scope || '|' ||
                            coalesce(memberships.benchmark_area, '') || '|' ||
                            memberships.cohort_type || '|' ||
                            memberships.cohort_signature || '|' ||
                            memberships.definition_json::text
                        ),
                        13,
                        4
                    ) || '-' ||
                    substr(
                        md5(
                            memberships.metric_key || '|' ||
                            memberships.academic_year || '|' ||
                            memberships.benchmark_scope || '|' ||
                            coalesce(memberships.benchmark_area, '') || '|' ||
                            memberships.cohort_type || '|' ||
                            memberships.cohort_signature || '|' ||
                            memberships.definition_json::text
                        ),
                        17,
                        4
                    ) || '-' ||
                    substr(
                        md5(
                            memberships.metric_key || '|' ||
                            memberships.academic_year || '|' ||
                            memberships.benchmark_scope || '|' ||
                            coalesce(memberships.benchmark_area, '') || '|' ||
                            memberships.cohort_type || '|' ||
                            memberships.cohort_signature || '|' ||
                            memberships.definition_json::text
                        ),
                        21,
                        12
                    )
                )::uuid AS cohort_id,
                memberships.academic_year,
                memberships.metric_key,
                memberships.benchmark_scope,
                memberships.benchmark_area,
                memberships.cohort_type,
                memberships.cohort_label,
                memberships.cohort_signature,
                memberships.definition_json AS definition_json,
                count(*)::integer AS school_count
            FROM tmp_metric_benchmark_cohort_memberships AS memberships
            GROUP BY
                memberships.academic_year,
                memberships.metric_key,
                memberships.benchmark_scope,
                memberships.benchmark_area,
                memberships.cohort_type,
                memberships.cohort_label,
                memberships.cohort_signature,
                memberships.definition_json
            """
        )
    )
    connection.execute(
        text(
            f"""
            INSERT INTO metric_benchmark_cohorts_yearly (
                cohort_id,
                academic_year,
                metric_key,
                benchmark_scope,
                cohort_type,
                cohort_label,
                cohort_signature,
                definition_json,
                school_count,
                computed_at_utc
            )
            SELECT
                cohort_id,
                academic_year,
                metric_key,
                benchmark_scope,
                cohort_type,
                cohort_label,
                cohort_signature,
                {definition_json_expression},
                school_count,
                {updated_at_expression}
            FROM tmp_metric_benchmark_cohorts
            """
        )
    )
    connection.execute(
        text(
            """
            INSERT INTO metric_benchmark_distributions_yearly (
                cohort_id,
                mean_value,
                p10_value,
                p25_value,
                median_value,
                p75_value,
                p90_value,
                minimum_value,
                maximum_value
            )
            SELECT
                cohorts.cohort_id,
                avg(memberships.metric_value)::numeric(14,4) AS mean_value,
                percentile_cont(0.10) WITHIN GROUP (ORDER BY memberships.metric_value)::numeric(14,4) AS p10_value,
                percentile_cont(0.25) WITHIN GROUP (ORDER BY memberships.metric_value)::numeric(14,4) AS p25_value,
                percentile_cont(0.50) WITHIN GROUP (ORDER BY memberships.metric_value)::numeric(14,4) AS median_value,
                percentile_cont(0.75) WITHIN GROUP (ORDER BY memberships.metric_value)::numeric(14,4) AS p75_value,
                percentile_cont(0.90) WITHIN GROUP (ORDER BY memberships.metric_value)::numeric(14,4) AS p90_value,
                min(memberships.metric_value)::numeric(14,4) AS minimum_value,
                max(memberships.metric_value)::numeric(14,4) AS maximum_value
            FROM tmp_metric_benchmark_cohort_memberships AS memberships
            INNER JOIN tmp_metric_benchmark_cohorts AS cohorts
                ON cohorts.metric_key = memberships.metric_key
               AND cohorts.academic_year = memberships.academic_year
               AND cohorts.benchmark_scope = memberships.benchmark_scope
               AND cohorts.cohort_signature = memberships.cohort_signature
            GROUP BY cohorts.cohort_id
            """
        )
    )
    connection.execute(
        text(
            f"""
            INSERT INTO school_metric_percentiles_yearly (
                urn,
                academic_year,
                metric_key,
                benchmark_scope,
                cohort_id,
                metric_value,
                percentile_rank,
                computed_at_utc
            )
            SELECT
                ranked.urn,
                ranked.academic_year,
                ranked.metric_key,
                ranked.benchmark_scope,
                ranked.cohort_id,
                ranked.metric_value,
                round((ranked.percentile_rank * 100.0)::numeric, 4) AS percentile_rank,
                {updated_at_expression}
            FROM (
                SELECT
                    memberships.urn,
                    memberships.academic_year,
                    memberships.metric_key,
                    memberships.benchmark_scope,
                    cohorts.cohort_id,
                    memberships.metric_value,
                    percent_rank() OVER (
                        PARTITION BY cohorts.cohort_id
                        ORDER BY memberships.metric_value
                    ) AS percentile_rank
                FROM tmp_metric_benchmark_cohort_memberships AS memberships
                INNER JOIN tmp_metric_benchmark_cohorts AS cohorts
                    ON cohorts.metric_key = memberships.metric_key
                   AND cohorts.academic_year = memberships.academic_year
                   AND cohorts.benchmark_scope = memberships.benchmark_scope
                   AND cohorts.cohort_signature = memberships.cohort_signature
                WHERE memberships.benchmark_scope <> 'similar_school'

                UNION ALL

                SELECT
                    ranked_members.urn,
                    ranked_members.academic_year,
                    ranked_members.metric_key,
                    'similar_school' AS benchmark_scope,
                    ranked_members.cohort_id,
                    ranked_members.metric_value,
                    ranked_members.percentile_rank
                FROM tmp_selected_similar_school_cohorts AS selected
                INNER JOIN (
                    SELECT
                        memberships.urn,
                        memberships.academic_year,
                        memberships.metric_key,
                        memberships.cohort_signature,
                        cohorts.cohort_id,
                        memberships.metric_value,
                        percent_rank() OVER (
                            PARTITION BY cohorts.cohort_id
                            ORDER BY memberships.metric_value
                        ) AS percentile_rank
                    FROM tmp_metric_benchmark_cohort_memberships AS memberships
                    INNER JOIN tmp_metric_benchmark_cohorts AS cohorts
                        ON cohorts.metric_key = memberships.metric_key
                       AND cohorts.academic_year = memberships.academic_year
                       AND cohorts.benchmark_scope = 'similar_school'
                       AND cohorts.cohort_signature = memberships.cohort_signature
                    WHERE memberships.benchmark_scope = 'similar_school'
                ) AS ranked_members
                    ON ranked_members.urn = selected.urn
                   AND ranked_members.academic_year = selected.academic_year
                   AND ranked_members.metric_key = selected.metric_key
                   AND ranked_members.cohort_signature = selected.cohort_signature
            ) AS ranked
            """
        )
    )
    if _table_exists(connection, "metric_benchmarks_yearly"):
        connection.execute(
            text(
                f"""
                INSERT INTO metric_benchmarks_yearly (
                    metric_key,
                    academic_year,
                    benchmark_scope,
                    benchmark_area,
                    benchmark_label,
                    benchmark_value,
                    updated_at
                )
                SELECT
                    cohorts.metric_key,
                    cohorts.academic_year,
                    cohorts.benchmark_scope,
                    cohorts.benchmark_area,
                    cohorts.cohort_label,
                    distributions.mean_value::double precision AS benchmark_value,
                    {updated_at_expression}
                FROM tmp_metric_benchmark_cohorts AS cohorts
                INNER JOIN metric_benchmark_distributions_yearly AS distributions
                    ON distributions.cohort_id = cohorts.cohort_id
                WHERE cohorts.benchmark_scope IN (
                    'national',
                    'local_authority_district',
                    'phase'
                )
                """
            )
        )


def _has_percentile_tables(connection: Connection) -> bool:
    return all(
        _table_exists(connection, table_name)
        for table_name in (
            "metric_benchmark_cohorts_yearly",
            "metric_benchmark_distributions_yearly",
            "school_metric_percentiles_yearly",
        )
    )


def _table_exists(connection: Connection, table_name: str) -> bool:
    if connection.dialect.name == "postgresql":
        return bool(
            connection.execute(
                text("SELECT to_regclass(:table_name) IS NOT NULL"),
                {"table_name": table_name},
            ).scalar_one()
        )

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
