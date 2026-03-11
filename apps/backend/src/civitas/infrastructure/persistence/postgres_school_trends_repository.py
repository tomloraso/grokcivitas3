from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import SQLAlchemyError

from civitas.application.school_trends.errors import SchoolTrendsDataUnavailableError
from civitas.application.school_trends.ports.school_trends_repository import SchoolTrendsRepository
from civitas.domain.school_trends.models import (
    BenchmarkScope,
    SchoolAdmissionsSeries,
    SchoolAdmissionsYearlyRow,
    SchoolAttendanceSeries,
    SchoolAttendanceYearlyRow,
    SchoolBehaviourSeries,
    SchoolBehaviourYearlyRow,
    SchoolDemographicsSeries,
    SchoolDemographicsYearlyRow,
    SchoolFinanceSeries,
    SchoolFinanceYearlyRow,
    SchoolMetricBenchmarkSeries,
    SchoolMetricBenchmarkYearlyRow,
    SchoolWorkforceSeries,
    SchoolWorkforceYearlyRow,
)

logger = logging.getLogger(__name__)


class PostgresSchoolTrendsRepository(SchoolTrendsRepository):
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def get_demographics_series(self, urn: str) -> SchoolDemographicsSeries | None:
        try:
            with self._engine.connect() as connection:
                if not _school_exists(connection, urn):
                    return None

                rows = (
                    connection.execute(
                        text(
                            """
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
                                updated_at
                            FROM school_demographics_yearly
                            WHERE urn = :urn
                            ORDER BY
                                substring(academic_year from 1 for 4)::integer ASC,
                                academic_year ASC
                            """
                        ),
                        {"urn": urn},
                    )
                    .mappings()
                    .all()
                )
        except SQLAlchemyError as exc:
            raise SchoolTrendsDataUnavailableError(
                "School trends datastore is unavailable."
            ) from exc

        return SchoolDemographicsSeries(
            urn=urn,
            rows=tuple(
                SchoolDemographicsYearlyRow(
                    academic_year=str(row["academic_year"]),
                    disadvantaged_pct=_to_optional_float(row["disadvantaged_pct"]),
                    fsm_pct=_to_optional_float(row["fsm_pct"]),
                    fsm6_pct=_to_optional_float(row["fsm6_pct"]),
                    sen_pct=_to_optional_float(row["sen_pct"]),
                    ehcp_pct=_to_optional_float(row["ehcp_pct"]),
                    eal_pct=_to_optional_float(row["eal_pct"]),
                    first_language_english_pct=_to_optional_float(
                        row["first_language_english_pct"]
                    ),
                    first_language_unclassified_pct=_to_optional_float(
                        row["first_language_unclassified_pct"]
                    ),
                    male_pct=_to_optional_float(row["male_pct"]),
                    female_pct=_to_optional_float(row["female_pct"]),
                    pupil_mobility_pct=_to_optional_float(row["pupil_mobility_pct"]),
                )
                for row in rows
            ),
            latest_updated_at=_max_optional_updated_at(tuple(row["updated_at"] for row in rows)),
        )

    def get_attendance_series(self, urn: str) -> SchoolAttendanceSeries | None:
        try:
            with self._engine.connect() as connection:
                if not _school_exists(connection, urn):
                    return None

                rows = (
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
                                substring(academic_year from 1 for 4)::integer ASC,
                                academic_year ASC
                            """
                        ),
                        {"urn": urn},
                    )
                    .mappings()
                    .all()
                )
        except SQLAlchemyError as exc:
            raise SchoolTrendsDataUnavailableError(
                "School trends datastore is unavailable."
            ) from exc

        return SchoolAttendanceSeries(
            urn=urn,
            rows=tuple(
                SchoolAttendanceYearlyRow(
                    academic_year=str(row["academic_year"]),
                    overall_attendance_pct=_to_optional_float(row["overall_attendance_pct"]),
                    overall_absence_pct=_to_optional_float(row["overall_absence_pct"]),
                    persistent_absence_pct=_to_optional_float(row["persistent_absence_pct"]),
                )
                for row in rows
            ),
            latest_updated_at=_max_optional_updated_at(tuple(row["updated_at"] for row in rows)),
        )

    def get_behaviour_series(self, urn: str) -> SchoolBehaviourSeries | None:
        try:
            with self._engine.connect() as connection:
                if not _school_exists(connection, urn):
                    return None

                rows = (
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
                                substring(academic_year from 1 for 4)::integer ASC,
                                academic_year ASC
                            """
                        ),
                        {"urn": urn},
                    )
                    .mappings()
                    .all()
                )
        except SQLAlchemyError as exc:
            raise SchoolTrendsDataUnavailableError(
                "School trends datastore is unavailable."
            ) from exc

        return SchoolBehaviourSeries(
            urn=urn,
            rows=tuple(
                SchoolBehaviourYearlyRow(
                    academic_year=str(row["academic_year"]),
                    suspensions_count=_to_optional_int(row["suspensions_count"]),
                    suspensions_rate=_to_optional_float(row["suspensions_rate"]),
                    permanent_exclusions_count=_to_optional_int(row["permanent_exclusions_count"]),
                    permanent_exclusions_rate=_to_optional_float(row["permanent_exclusions_rate"]),
                )
                for row in rows
            ),
            latest_updated_at=_max_optional_updated_at(tuple(row["updated_at"] for row in rows)),
        )

    def get_workforce_series(self, urn: str) -> SchoolWorkforceSeries | None:
        try:
            with self._engine.connect() as connection:
                if not _school_exists(connection, urn):
                    return None

                rows = (
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
                                teacher_headcount_total,
                                teacher_fte_total,
                                support_staff_headcount_total,
                                support_staff_fte_total,
                                leadership_share_of_teachers,
                                teacher_average_mean_salary_gbp,
                                teacher_average_median_salary_gbp,
                                teachers_on_leadership_pay_range_pct,
                                teacher_absence_pct,
                                teacher_absence_days_total,
                                teacher_absence_days_average,
                                teacher_absence_days_average_all_teachers,
                                teacher_vacancy_count,
                                teacher_vacancy_rate,
                                teacher_tempfilled_vacancy_count,
                                teacher_tempfilled_vacancy_rate,
                                third_party_support_staff_headcount,
                                updated_at
                            FROM school_workforce_yearly
                            WHERE urn = :urn
                            ORDER BY
                                substring(academic_year from 1 for 4)::integer ASC,
                                academic_year ASC
                            """
                        ),
                        {"urn": urn},
                    )
                    .mappings()
                    .all()
                )
        except SQLAlchemyError as exc:
            raise SchoolTrendsDataUnavailableError(
                "School trends datastore is unavailable."
            ) from exc

        return SchoolWorkforceSeries(
            urn=urn,
            rows=tuple(
                SchoolWorkforceYearlyRow(
                    academic_year=str(row["academic_year"]),
                    pupil_teacher_ratio=_to_optional_float(row["pupil_teacher_ratio"]),
                    supply_staff_pct=_to_optional_float(row["supply_staff_pct"]),
                    teachers_3plus_years_pct=_to_optional_float(row["teachers_3plus_years_pct"]),
                    teacher_turnover_pct=_to_optional_float(row["teacher_turnover_pct"]),
                    qts_pct=_to_optional_float(row["qts_pct"]),
                    qualifications_level6_plus_pct=_to_optional_float(
                        row["qualifications_level6_plus_pct"]
                    ),
                    teacher_headcount_total=_to_optional_float(row["teacher_headcount_total"]),
                    teacher_fte_total=_to_optional_float(row["teacher_fte_total"]),
                    support_staff_headcount_total=_to_optional_float(
                        row["support_staff_headcount_total"]
                    ),
                    support_staff_fte_total=_to_optional_float(row["support_staff_fte_total"]),
                    leadership_share_of_teachers=_to_optional_float(
                        row["leadership_share_of_teachers"]
                    ),
                    teacher_average_mean_salary_gbp=_to_optional_float(
                        row["teacher_average_mean_salary_gbp"]
                    ),
                    teacher_average_median_salary_gbp=_to_optional_float(
                        row["teacher_average_median_salary_gbp"]
                    ),
                    teachers_on_leadership_pay_range_pct=_to_optional_float(
                        row["teachers_on_leadership_pay_range_pct"]
                    ),
                    teacher_absence_pct=_to_optional_float(row["teacher_absence_pct"]),
                    teacher_absence_days_total=_to_optional_float(
                        row["teacher_absence_days_total"]
                    ),
                    teacher_absence_days_average=_to_optional_float(
                        row["teacher_absence_days_average"]
                    ),
                    teacher_absence_days_average_all_teachers=_to_optional_float(
                        row["teacher_absence_days_average_all_teachers"]
                    ),
                    teacher_vacancy_count=_to_optional_float(row["teacher_vacancy_count"]),
                    teacher_vacancy_rate=_to_optional_float(row["teacher_vacancy_rate"]),
                    teacher_tempfilled_vacancy_count=_to_optional_float(
                        row["teacher_tempfilled_vacancy_count"]
                    ),
                    teacher_tempfilled_vacancy_rate=_to_optional_float(
                        row["teacher_tempfilled_vacancy_rate"]
                    ),
                    third_party_support_staff_headcount=_to_optional_float(
                        row["third_party_support_staff_headcount"]
                    ),
                )
                for row in rows
            ),
            latest_updated_at=_max_optional_updated_at(tuple(row["updated_at"] for row in rows)),
        )

    def get_finance_series(self, urn: str) -> SchoolFinanceSeries | None:
        try:
            with self._engine.connect() as connection:
                school_row = _get_school_finance_context(connection, urn)
                if school_row is None:
                    return None

                rows = (
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
                                teaching_staff_costs_per_pupil_gbp,
                                revenue_reserve_gbp,
                                revenue_reserve_per_pupil_gbp,
                                supply_staff_costs_pct_of_staff_costs,
                                in_year_balance_gbp,
                                updated_at
                            FROM school_financials_yearly
                            WHERE urn = :urn
                            ORDER BY
                                substring(academic_year from 1 for 4)::integer ASC,
                                academic_year ASC
                            """
                        ),
                        {"urn": urn},
                    )
                    .mappings()
                    .all()
                )
        except SQLAlchemyError as exc:
            raise SchoolTrendsDataUnavailableError(
                "School trends datastore is unavailable."
            ) from exc

        is_applicable = len(rows) > 0 or _school_finance_is_applicable(
            school_type=_to_optional_str(school_row.get("type")),
            trust_name=_to_optional_str(school_row.get("trust_name")),
            trust_flag=_to_optional_str(school_row.get("trust_flag")),
        )
        return SchoolFinanceSeries(
            urn=urn,
            rows=tuple(
                SchoolFinanceYearlyRow(
                    academic_year=str(row["academic_year"]),
                    total_income_gbp=_to_optional_float(row["total_income_gbp"]),
                    total_expenditure_gbp=_to_optional_float(row["total_expenditure_gbp"]),
                    income_per_pupil_gbp=_to_optional_float(row["income_per_pupil_gbp"]),
                    expenditure_per_pupil_gbp=_to_optional_float(row["expenditure_per_pupil_gbp"]),
                    total_staff_costs_gbp=_to_optional_float(row["total_staff_costs_gbp"]),
                    staff_costs_pct_of_expenditure=_to_optional_float(
                        row["staff_costs_pct_of_expenditure"]
                    ),
                    teaching_staff_costs_per_pupil_gbp=_to_optional_float(
                        row["teaching_staff_costs_per_pupil_gbp"]
                    ),
                    revenue_reserve_gbp=_to_optional_float(row["revenue_reserve_gbp"]),
                    revenue_reserve_per_pupil_gbp=_to_optional_float(
                        row["revenue_reserve_per_pupil_gbp"]
                    ),
                    supply_staff_costs_pct_of_staff_costs=_to_optional_float(
                        row["supply_staff_costs_pct_of_staff_costs"]
                    ),
                    in_year_balance_gbp=_to_optional_float(row["in_year_balance_gbp"]),
                )
                for row in rows
            ),
            latest_updated_at=_max_optional_updated_at(tuple(row["updated_at"] for row in rows)),
            is_applicable=is_applicable,
        )

    def get_admissions_series(self, urn: str) -> SchoolAdmissionsSeries | None:
        try:
            with self._engine.connect() as connection:
                if not _school_exists(connection, urn):
                    return None

                rows = (
                    connection.execute(
                        text(
                            """
                            SELECT
                                academic_year,
                                oversubscription_ratio,
                                first_preference_offer_rate,
                                any_preference_offer_rate,
                                cross_la_applications,
                                cross_la_offers,
                                updated_at
                            FROM school_admissions_yearly
                            WHERE urn = :urn
                            ORDER BY
                                substring(academic_year from 1 for 4)::integer ASC,
                                academic_year ASC
                            """
                        ),
                        {"urn": urn},
                    )
                    .mappings()
                    .all()
                )
        except SQLAlchemyError as exc:
            raise SchoolTrendsDataUnavailableError(
                "School trends datastore is unavailable."
            ) from exc

        return SchoolAdmissionsSeries(
            urn=urn,
            rows=tuple(
                SchoolAdmissionsYearlyRow(
                    academic_year=str(row["academic_year"]),
                    oversubscription_ratio=_to_optional_float(row["oversubscription_ratio"]),
                    first_preference_offer_rate=_to_optional_float(
                        row["first_preference_offer_rate"]
                    ),
                    any_preference_offer_rate=_to_optional_float(row["any_preference_offer_rate"]),
                    cross_la_applications=_to_optional_int(row["cross_la_applications"]),
                    cross_la_offers=_to_optional_int(row["cross_la_offers"]),
                )
                for row in rows
            ),
            latest_updated_at=_max_optional_updated_at(tuple(row["updated_at"] for row in rows)),
        )

    def get_metric_benchmark_series(self, urn: str) -> SchoolMetricBenchmarkSeries | None:
        try:
            with self._engine.connect() as connection:
                if not _school_exists(connection, urn):
                    return None

                benchmark_rows = _get_metric_benchmark_rows_from_cache(connection, urn)
        except SQLAlchemyError as exc:
            raise SchoolTrendsDataUnavailableError(
                "School trends datastore is unavailable."
            ) from exc

        if len(benchmark_rows) == 0:
            logger.warning(
                "Metric benchmark cache miss for urn=%s; returning empty benchmark series.",
                urn,
            )
        elif _metric_benchmark_rows_are_partial(benchmark_rows):
            logger.warning(
                "Metric benchmark cache incomplete for urn=%s; returning partial benchmark data.",
                urn,
            )

        return SchoolMetricBenchmarkSeries(
            urn=urn,
            rows=tuple(
                SchoolMetricBenchmarkYearlyRow(
                    metric_key=str(row["metric_key"]),
                    academic_year=str(row["academic_year"]),
                    school_value=_to_optional_float(row["school_value"]),
                    national_value=_to_optional_float(row["national_value"]),
                    local_value=_to_optional_float(row["local_value"]),
                    local_scope=_to_benchmark_scope(row["local_scope"]),
                    local_area_code=_to_optional_str(row["local_area_code"]) or "unknown",
                    local_area_label=_to_optional_str(row["local_area_label"]) or "Unknown",
                )
                for row in benchmark_rows
            ),
            latest_updated_at=None,
        )

    def materialize_all_metric_benchmarks(self) -> int:
        try:
            with self._engine.begin() as connection:
                if connection.dialect.name == "postgresql":
                    connection.execute(text("SET LOCAL work_mem = '64MB'"))
                return _rebuild_metric_benchmark_rows(connection)
        except SQLAlchemyError as exc:
            raise SchoolTrendsDataUnavailableError(
                "School trends datastore is unavailable."
            ) from exc

    def materialize_metric_benchmarks_for_urns(self, urns: Sequence[str]) -> int:
        normalized_urns = tuple(
            dict.fromkeys(urn.strip() for urn in urns if urn is not None and urn.strip())
        )
        if len(normalized_urns) == 0:
            return self.materialize_all_metric_benchmarks()

        try:
            with self._engine.begin() as connection:
                if connection.dialect.name == "postgresql":
                    connection.execute(text("SET LOCAL work_mem = '64MB'"))
                persisted_rows = 0
                for urn in normalized_urns:
                    if not _school_exists(connection, urn):
                        continue
                    benchmark_rows = _compute_metric_benchmark_rows(connection, urn)
                    persisted_rows += _persist_metric_benchmark_rows(
                        connection,
                        [dict(benchmark_row) for benchmark_row in benchmark_rows],
                    )
                return persisted_rows
        except SQLAlchemyError as exc:
            raise SchoolTrendsDataUnavailableError(
                "School trends datastore is unavailable."
            ) from exc


def _school_exists(connection: Connection, urn: str) -> bool:
    return bool(
        connection.execute(
            text(
                """
                SELECT 1
                FROM schools
                WHERE urn = :urn
                """
            ),
            {"urn": urn},
        )
        .scalars()
        .first()
    )


def _get_school_finance_context(connection: Connection, urn: str) -> Mapping[str, object] | None:
    row = (
        connection.execute(
            text(
                """
                SELECT type, trust_name, trust_flag
                FROM schools
                WHERE urn = :urn
                """
            ),
            {"urn": urn},
        )
        .mappings()
        .first()
    )
    return dict(row) if row is not None else None


def _to_optional_float(value: object) -> float | None:
    if value is None:
        return None
    return float(str(value))


def _to_optional_int(value: object) -> int | None:
    if value is None:
        return None
    return int(float(str(value)))


def _max_optional_updated_at(values: tuple[object, ...]) -> datetime | None:
    non_null_values = [value for value in values if isinstance(value, datetime)]
    if len(non_null_values) == 0:
        return None
    return max(non_null_values)


def _to_optional_str(value: object) -> str | None:
    if value is None:
        return None
    text_value = str(value).strip()
    return text_value or None


def _to_benchmark_scope(value: object) -> BenchmarkScope:
    normalized = _to_optional_str(value)
    if normalized == "local_authority_district":
        return "local_authority_district"
    return "phase"


def _school_finance_is_applicable(
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


def _get_metric_benchmark_rows_from_cache(
    connection: Connection,
    urn: str,
) -> Sequence[Mapping[str, object]]:
    if not _table_exists(connection, "metric_benchmarks_yearly"):
        return ()

    rows = (
        connection.execute(
            text(
                """
                WITH target_school AS (
                    SELECT
                        schools.urn,
                        schools.phase,
                        deprivation.local_authority_district_code AS lad_code,
                        deprivation.local_authority_district_name AS lad_name,
                        deprivation.population_total AS population_total
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
                    WHERE schools.urn = :urn
                    LIMIT 1
                ),
                local_context AS (
                    SELECT
                        CASE
                            WHEN target_school.lad_code IS NOT NULL
                                THEN 'local_authority_district'
                            ELSE 'phase'
                        END AS local_scope,
                        coalesce(target_school.lad_code, target_school.phase, 'unknown')
                            AS local_area_code,
                        coalesce(target_school.lad_name, target_school.phase, 'Unknown')
                            AS local_area_label
                    FROM target_school
                ),
                area_crime_yearly AS (
                    SELECT
                        context.urn,
                        extract(year from context.month)::int::text AS academic_year,
                        (
                            sum(context.incident_count)::double precision /
                            NULLIF(max(target_school.population_total), 0)::double precision
                        ) * 1000.0 AS area_crime_incidents_per_1000
                    FROM area_crime_context AS context
                    INNER JOIN target_school
                        ON target_school.urn = context.urn
                    GROUP BY
                        context.urn,
                        extract(year from context.month)::int
                ),
                area_house_price_yearly AS (
                    SELECT
                        target_school.urn,
                        extract(year from prices.month)::int::text AS academic_year,
                        avg(prices.average_price)::double precision AS area_house_price_average,
                        avg(prices.annual_change_pct)::double precision AS area_house_price_annual_change_pct
                    FROM target_school
                    INNER JOIN area_house_price_context AS prices
                        ON prices.area_code = target_school.lad_code
                    GROUP BY
                        target_school.urn,
                        extract(year from prices.month)::int
                ),
                school_metric_rows AS (
                    SELECT
                        demographics.academic_year,
                        metric.metric_key,
                        metric.metric_value AS school_value
                    FROM school_demographics_yearly AS demographics
                    CROSS JOIN LATERAL (
                        VALUES
                            ('disadvantaged_pct', demographics.disadvantaged_pct::double precision),
                            ('fsm_pct', demographics.fsm_pct::double precision),
                            ('fsm6_pct', demographics.fsm6_pct::double precision),
                            ('sen_pct', demographics.sen_pct::double precision),
                            ('ehcp_pct', demographics.ehcp_pct::double precision),
                            ('eal_pct', demographics.eal_pct::double precision),
                            (
                                'first_language_english_pct',
                                demographics.first_language_english_pct::double precision
                            ),
                            (
                                'first_language_unclassified_pct',
                                demographics.first_language_unclassified_pct::double precision
                            ),
                            ('male_pct', demographics.male_pct::double precision),
                            ('female_pct', demographics.female_pct::double precision),
                            ('pupil_mobility_pct', demographics.pupil_mobility_pct::double precision)
                    ) AS metric(metric_key, metric_value)
                    WHERE demographics.urn = :urn

                    UNION ALL

                    SELECT
                        attendance.academic_year,
                        metric.metric_key,
                        metric.metric_value AS school_value
                    FROM school_attendance_yearly AS attendance
                    CROSS JOIN LATERAL (
                        VALUES
                            ('overall_attendance_pct', attendance.overall_attendance_pct::double precision),
                            ('overall_absence_pct', attendance.overall_absence_pct::double precision),
                            ('persistent_absence_pct', attendance.persistent_absence_pct::double precision)
                    ) AS metric(metric_key, metric_value)
                    WHERE attendance.urn = :urn

                    UNION ALL

                    SELECT
                        behaviour.academic_year,
                        metric.metric_key,
                        metric.metric_value AS school_value
                    FROM school_behaviour_yearly AS behaviour
                    CROSS JOIN LATERAL (
                        VALUES
                            ('suspensions_count', behaviour.suspensions_count::double precision),
                            ('suspensions_rate', behaviour.suspensions_rate::double precision),
                            (
                                'permanent_exclusions_count',
                                behaviour.permanent_exclusions_count::double precision
                            ),
                            (
                                'permanent_exclusions_rate',
                                behaviour.permanent_exclusions_rate::double precision
                            )
                    ) AS metric(metric_key, metric_value)
                    WHERE behaviour.urn = :urn

                    UNION ALL

                    SELECT
                        workforce.academic_year,
                        metric.metric_key,
                        metric.metric_value AS school_value
                    FROM school_workforce_yearly AS workforce
                    CROSS JOIN LATERAL (
                        VALUES
                            ('pupil_teacher_ratio', workforce.pupil_teacher_ratio::double precision),
                            ('supply_staff_pct', workforce.supply_staff_pct::double precision),
                            (
                                'teachers_3plus_years_pct',
                                workforce.teachers_3plus_years_pct::double precision
                            ),
                            ('teacher_turnover_pct', workforce.teacher_turnover_pct::double precision),
                            ('qts_pct', workforce.qts_pct::double precision),
                            (
                                'qualifications_level6_plus_pct',
                                workforce.qualifications_level6_plus_pct::double precision
                            ),
                            (
                                'teacher_headcount_total',
                                workforce.teacher_headcount_total::double precision
                            ),
                            ('teacher_fte_total', workforce.teacher_fte_total::double precision),
                            (
                                'support_staff_headcount_total',
                                workforce.support_staff_headcount_total::double precision
                            ),
                            ('support_staff_fte_total', workforce.support_staff_fte_total::double precision),
                            (
                                'leadership_share_of_teachers',
                                workforce.leadership_share_of_teachers::double precision
                            ),
                            (
                                'teacher_average_mean_salary_gbp',
                                workforce.teacher_average_mean_salary_gbp::double precision
                            ),
                            (
                                'teacher_average_median_salary_gbp',
                                workforce.teacher_average_median_salary_gbp::double precision
                            ),
                            (
                                'teachers_on_leadership_pay_range_pct',
                                workforce.teachers_on_leadership_pay_range_pct::double precision
                            ),
                            ('teacher_absence_pct', workforce.teacher_absence_pct::double precision),
                            (
                                'teacher_absence_days_total',
                                workforce.teacher_absence_days_total::double precision
                            ),
                            (
                                'teacher_absence_days_average',
                                workforce.teacher_absence_days_average::double precision
                            ),
                            (
                                'teacher_absence_days_average_all_teachers',
                                workforce.teacher_absence_days_average_all_teachers::double precision
                            ),
                            ('teacher_vacancy_count', workforce.teacher_vacancy_count::double precision),
                            ('teacher_vacancy_rate', workforce.teacher_vacancy_rate::double precision),
                            (
                                'teacher_tempfilled_vacancy_count',
                                workforce.teacher_tempfilled_vacancy_count::double precision
                            ),
                            (
                                'teacher_tempfilled_vacancy_rate',
                                workforce.teacher_tempfilled_vacancy_rate::double precision
                            ),
                            (
                                'third_party_support_staff_headcount',
                                workforce.third_party_support_staff_headcount::double precision
                            )
                    ) AS metric(metric_key, metric_value)
                    WHERE workforce.urn = :urn

                    UNION ALL

                    SELECT
                        finance.academic_year,
                        metric.metric_key,
                        metric.metric_value AS school_value
                    FROM school_financials_yearly AS finance
                    CROSS JOIN LATERAL (
                        VALUES
                            (
                                'finance_income_per_pupil_gbp',
                                finance.income_per_pupil_gbp::double precision
                            ),
                            (
                                'finance_expenditure_per_pupil_gbp',
                                finance.expenditure_per_pupil_gbp::double precision
                            ),
                            (
                                'finance_staff_costs_pct_of_expenditure',
                                finance.staff_costs_pct_of_expenditure::double precision
                            ),
                            (
                                'finance_revenue_reserve_per_pupil_gbp',
                                finance.revenue_reserve_per_pupil_gbp::double precision
                            ),
                            (
                                'finance_teaching_staff_costs_per_pupil_gbp',
                                finance.teaching_staff_costs_per_pupil_gbp::double precision
                            ),
                            (
                                'finance_supply_staff_costs_pct_of_staff_costs',
                                finance.supply_staff_costs_pct_of_staff_costs::double precision
                            )
                    ) AS metric(metric_key, metric_value)
                    WHERE finance.urn = :urn

                    UNION ALL

                    SELECT
                        admissions.academic_year,
                        metric.metric_key,
                        metric.metric_value AS school_value
                    FROM school_admissions_yearly AS admissions
                    CROSS JOIN LATERAL (
                        VALUES
                            (
                                'admissions_oversubscription_ratio',
                                admissions.oversubscription_ratio::double precision
                            ),
                            (
                                'admissions_first_preference_offer_rate',
                                admissions.first_preference_offer_rate::double precision
                            ),
                            (
                                'admissions_any_preference_offer_rate',
                                admissions.any_preference_offer_rate::double precision
                            ),
                            (
                                'admissions_cross_la_applications',
                                admissions.cross_la_applications::double precision
                            )
                    ) AS metric(metric_key, metric_value)
                    WHERE admissions.urn = :urn

                    UNION ALL

                    SELECT
                        performance.academic_year,
                        metric.metric_key,
                        metric.metric_value AS school_value
                    FROM school_performance_yearly AS performance
                    CROSS JOIN LATERAL (
                        VALUES
                            ('attainment8_average', performance.attainment8_average::double precision),
                            ('progress8_average', performance.progress8_average::double precision),
                            (
                                'progress8_disadvantaged',
                                performance.progress8_disadvantaged::double precision
                            ),
                            (
                                'progress8_not_disadvantaged',
                                performance.progress8_not_disadvantaged::double precision
                            ),
                            (
                                'progress8_disadvantaged_gap',
                                performance.progress8_disadvantaged_gap::double precision
                            ),
                            ('engmath_5_plus_pct', performance.engmath_5_plus_pct::double precision),
                            ('engmath_4_plus_pct', performance.engmath_4_plus_pct::double precision),
                            ('ebacc_entry_pct', performance.ebacc_entry_pct::double precision),
                            ('ebacc_5_plus_pct', performance.ebacc_5_plus_pct::double precision),
                            ('ebacc_4_plus_pct', performance.ebacc_4_plus_pct::double precision),
                            (
                                'ks2_reading_expected_pct',
                                performance.ks2_reading_expected_pct::double precision
                            ),
                            (
                                'ks2_writing_expected_pct',
                                performance.ks2_writing_expected_pct::double precision
                            ),
                            (
                                'ks2_maths_expected_pct',
                                performance.ks2_maths_expected_pct::double precision
                            ),
                            (
                                'ks2_combined_expected_pct',
                                performance.ks2_combined_expected_pct::double precision
                            ),
                            (
                                'ks2_reading_higher_pct',
                                performance.ks2_reading_higher_pct::double precision
                            ),
                            (
                                'ks2_writing_higher_pct',
                                performance.ks2_writing_higher_pct::double precision
                            ),
                            (
                                'ks2_maths_higher_pct',
                                performance.ks2_maths_higher_pct::double precision
                            ),
                            (
                                'ks2_combined_higher_pct',
                                performance.ks2_combined_higher_pct::double precision
                            )
                    ) AS metric(metric_key, metric_value)
                    WHERE performance.urn = :urn

                    UNION ALL

                    SELECT
                        yearly_crime.academic_year,
                        'area_crime_incidents_per_1000' AS metric_key,
                        yearly_crime.area_crime_incidents_per_1000 AS school_value
                    FROM area_crime_yearly AS yearly_crime

                    UNION ALL

                    SELECT
                        yearly_prices.academic_year,
                        metric.metric_key,
                        metric.metric_value AS school_value
                    FROM area_house_price_yearly AS yearly_prices
                    CROSS JOIN LATERAL (
                        VALUES
                            (
                                'area_house_price_average',
                                yearly_prices.area_house_price_average::double precision
                            ),
                            (
                                'area_house_price_annual_change_pct',
                                yearly_prices.area_house_price_annual_change_pct::double precision
                            )
                    ) AS metric(metric_key, metric_value)
                ),
                cache_rows AS (
                    SELECT
                        school_metric_rows.metric_key,
                        school_metric_rows.academic_year,
                        school_metric_rows.school_value,
                        national_benchmarks.metric_key AS national_metric_key,
                        national_benchmarks.benchmark_value AS national_value,
                        local_benchmarks.metric_key AS local_metric_key,
                        local_benchmarks.benchmark_value AS local_value,
                        local_context.local_scope,
                        local_context.local_area_code,
                        local_context.local_area_label
                    FROM school_metric_rows
                    INNER JOIN local_context
                        ON TRUE
                    LEFT JOIN metric_benchmarks_yearly AS national_benchmarks
                        ON national_benchmarks.metric_key = school_metric_rows.metric_key
                       AND national_benchmarks.academic_year = school_metric_rows.academic_year
                       AND national_benchmarks.benchmark_scope = 'national'
                       AND national_benchmarks.benchmark_area = 'england'
                    LEFT JOIN metric_benchmarks_yearly AS local_benchmarks
                        ON local_benchmarks.metric_key = school_metric_rows.metric_key
                       AND local_benchmarks.academic_year = school_metric_rows.academic_year
                       AND local_benchmarks.benchmark_scope = local_context.local_scope
                       AND local_benchmarks.benchmark_area = local_context.local_area_code
                ),
                missing_benchmark_rows AS (
                    SELECT 1
                    FROM cache_rows
                    WHERE national_metric_key IS NULL
                       OR local_metric_key IS NULL
                    LIMIT 1
                )
                SELECT
                    cache_rows.metric_key,
                    cache_rows.academic_year,
                    cache_rows.school_value,
                    cache_rows.national_metric_key,
                    cache_rows.national_value,
                    cache_rows.local_metric_key,
                    cache_rows.local_value,
                    cache_rows.local_scope,
                    cache_rows.local_area_code,
                    cache_rows.local_area_label
                FROM cache_rows
                """
            ),
            {"urn": urn},
        )
        .mappings()
        .all()
    )
    return tuple(dict(row) for row in rows)


def _metric_benchmark_rows_are_partial(rows: Sequence[Mapping[str, object]]) -> bool:
    return any(
        _to_optional_str(row.get("national_metric_key")) is None
        or _to_optional_str(row.get("local_metric_key")) is None
        for row in rows
    )


def _compute_metric_benchmark_rows(
    connection: Connection,
    urn: str,
) -> Sequence[Mapping[str, object]]:
    rows = (
        connection.execute(
            text(
                """
                WITH school_geo AS (
                    SELECT
                        schools.urn,
                        schools.phase,
                        deprivation.local_authority_district_code AS lad_code,
                        deprivation.local_authority_district_name AS lad_name,
                        deprivation.population_total AS population_total
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
                target_school AS (
                    SELECT
                        urn,
                        phase,
                        lad_code,
                        lad_name
                    FROM school_geo
                    WHERE urn = :urn
                    LIMIT 1
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
                    GROUP BY
                        context.urn,
                        extract(year from context.month)::int
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
                    GROUP BY
                        geo.urn,
                        extract(year from prices.month)::int
                ),
                metric_rows AS (
                    SELECT
                        demographics.urn,
                        demographics.academic_year,
                        geo.phase,
                        geo.lad_code,
                        metric.metric_key,
                        metric.metric_value
                    FROM school_demographics_yearly AS demographics
                    INNER JOIN school_geo AS geo
                        ON geo.urn = demographics.urn
                    CROSS JOIN LATERAL (
                        VALUES
                            ('disadvantaged_pct', demographics.disadvantaged_pct::double precision),
                            ('fsm_pct', demographics.fsm_pct::double precision),
                            ('fsm6_pct', demographics.fsm6_pct::double precision),
                            ('sen_pct', demographics.sen_pct::double precision),
                            ('ehcp_pct', demographics.ehcp_pct::double precision),
                            ('eal_pct', demographics.eal_pct::double precision),
                            ('first_language_english_pct', demographics.first_language_english_pct::double precision),
                            ('first_language_unclassified_pct', demographics.first_language_unclassified_pct::double precision),
                            ('male_pct', demographics.male_pct::double precision),
                            ('female_pct', demographics.female_pct::double precision),
                            ('pupil_mobility_pct', demographics.pupil_mobility_pct::double precision)
                    ) AS metric(metric_key, metric_value)

                    UNION ALL

                    SELECT
                        attendance.urn,
                        attendance.academic_year,
                        geo.phase,
                        geo.lad_code,
                        metric.metric_key,
                        metric.metric_value
                    FROM school_attendance_yearly AS attendance
                    INNER JOIN school_geo AS geo
                        ON geo.urn = attendance.urn
                    CROSS JOIN LATERAL (
                        VALUES
                            ('overall_attendance_pct', attendance.overall_attendance_pct::double precision),
                            ('overall_absence_pct', attendance.overall_absence_pct::double precision),
                            ('persistent_absence_pct', attendance.persistent_absence_pct::double precision)
                    ) AS metric(metric_key, metric_value)

                    UNION ALL

                    SELECT
                        behaviour.urn,
                        behaviour.academic_year,
                        geo.phase,
                        geo.lad_code,
                        metric.metric_key,
                        metric.metric_value
                    FROM school_behaviour_yearly AS behaviour
                    INNER JOIN school_geo AS geo
                        ON geo.urn = behaviour.urn
                    CROSS JOIN LATERAL (
                        VALUES
                            ('suspensions_count', behaviour.suspensions_count::double precision),
                            ('suspensions_rate', behaviour.suspensions_rate::double precision),
                            (
                                'permanent_exclusions_count',
                                behaviour.permanent_exclusions_count::double precision
                            ),
                            (
                                'permanent_exclusions_rate',
                                behaviour.permanent_exclusions_rate::double precision
                            )
                    ) AS metric(metric_key, metric_value)

                    UNION ALL

                    SELECT
                        workforce.urn,
                        workforce.academic_year,
                        geo.phase,
                        geo.lad_code,
                        metric.metric_key,
                        metric.metric_value
                    FROM school_workforce_yearly AS workforce
                    INNER JOIN school_geo AS geo
                        ON geo.urn = workforce.urn
                    CROSS JOIN LATERAL (
                        VALUES
                            ('pupil_teacher_ratio', workforce.pupil_teacher_ratio::double precision),
                            ('supply_staff_pct', workforce.supply_staff_pct::double precision),
                            ('teachers_3plus_years_pct', workforce.teachers_3plus_years_pct::double precision),
                            ('teacher_turnover_pct', workforce.teacher_turnover_pct::double precision),
                            ('qts_pct', workforce.qts_pct::double precision),
                            (
                                'qualifications_level6_plus_pct',
                                workforce.qualifications_level6_plus_pct::double precision
                            ),
                            (
                                'teacher_headcount_total',
                                workforce.teacher_headcount_total::double precision
                            ),
                            ('teacher_fte_total', workforce.teacher_fte_total::double precision),
                            (
                                'support_staff_headcount_total',
                                workforce.support_staff_headcount_total::double precision
                            ),
                            ('support_staff_fte_total', workforce.support_staff_fte_total::double precision),
                            (
                                'leadership_share_of_teachers',
                                workforce.leadership_share_of_teachers::double precision
                            ),
                            (
                                'teacher_average_mean_salary_gbp',
                                workforce.teacher_average_mean_salary_gbp::double precision
                            ),
                            (
                                'teacher_average_median_salary_gbp',
                                workforce.teacher_average_median_salary_gbp::double precision
                            ),
                            (
                                'teachers_on_leadership_pay_range_pct',
                                workforce.teachers_on_leadership_pay_range_pct::double precision
                            ),
                            ('teacher_absence_pct', workforce.teacher_absence_pct::double precision),
                            (
                                'teacher_absence_days_total',
                                workforce.teacher_absence_days_total::double precision
                            ),
                            (
                                'teacher_absence_days_average',
                                workforce.teacher_absence_days_average::double precision
                            ),
                            (
                                'teacher_absence_days_average_all_teachers',
                                workforce.teacher_absence_days_average_all_teachers::double precision
                            ),
                            ('teacher_vacancy_count', workforce.teacher_vacancy_count::double precision),
                            ('teacher_vacancy_rate', workforce.teacher_vacancy_rate::double precision),
                            (
                                'teacher_tempfilled_vacancy_count',
                                workforce.teacher_tempfilled_vacancy_count::double precision
                            ),
                            (
                                'teacher_tempfilled_vacancy_rate',
                                workforce.teacher_tempfilled_vacancy_rate::double precision
                            ),
                            (
                                'third_party_support_staff_headcount',
                                workforce.third_party_support_staff_headcount::double precision
                            )
                    ) AS metric(metric_key, metric_value)

                    UNION ALL

                    SELECT
                        finance.urn,
                        finance.academic_year,
                        geo.phase,
                        geo.lad_code,
                        metric.metric_key,
                        metric.metric_value
                    FROM school_financials_yearly AS finance
                    INNER JOIN school_geo AS geo
                        ON geo.urn = finance.urn
                    CROSS JOIN LATERAL (
                        VALUES
                            (
                                'finance_income_per_pupil_gbp',
                                finance.income_per_pupil_gbp::double precision
                            ),
                            (
                                'finance_expenditure_per_pupil_gbp',
                                finance.expenditure_per_pupil_gbp::double precision
                            ),
                            (
                                'finance_staff_costs_pct_of_expenditure',
                                finance.staff_costs_pct_of_expenditure::double precision
                            ),
                            (
                                'finance_revenue_reserve_per_pupil_gbp',
                                finance.revenue_reserve_per_pupil_gbp::double precision
                            ),
                            (
                                'finance_teaching_staff_costs_per_pupil_gbp',
                                finance.teaching_staff_costs_per_pupil_gbp::double precision
                            ),
                            (
                                'finance_supply_staff_costs_pct_of_staff_costs',
                                finance.supply_staff_costs_pct_of_staff_costs::double precision
                            )
                    ) AS metric(metric_key, metric_value)

                    UNION ALL

                    SELECT
                        admissions.urn,
                        admissions.academic_year,
                        geo.phase,
                        geo.lad_code,
                        metric.metric_key,
                        metric.metric_value
                    FROM school_admissions_yearly AS admissions
                    INNER JOIN school_geo AS geo
                        ON geo.urn = admissions.urn
                    CROSS JOIN LATERAL (
                        VALUES
                            (
                                'admissions_oversubscription_ratio',
                                admissions.oversubscription_ratio::double precision
                            ),
                            (
                                'admissions_first_preference_offer_rate',
                                admissions.first_preference_offer_rate::double precision
                            ),
                            (
                                'admissions_any_preference_offer_rate',
                                admissions.any_preference_offer_rate::double precision
                            ),
                            (
                                'admissions_cross_la_applications',
                                admissions.cross_la_applications::double precision
                            )
                    ) AS metric(metric_key, metric_value)

                    UNION ALL

                    SELECT
                        performance.urn,
                        performance.academic_year,
                        geo.phase,
                        geo.lad_code,
                        metric.metric_key,
                        metric.metric_value
                    FROM school_performance_yearly AS performance
                    INNER JOIN school_geo AS geo
                        ON geo.urn = performance.urn
                    CROSS JOIN LATERAL (
                        VALUES
                            ('attainment8_average', performance.attainment8_average::double precision),
                            ('progress8_average', performance.progress8_average::double precision),
                            (
                                'progress8_disadvantaged',
                                performance.progress8_disadvantaged::double precision
                            ),
                            (
                                'progress8_not_disadvantaged',
                                performance.progress8_not_disadvantaged::double precision
                            ),
                            (
                                'progress8_disadvantaged_gap',
                                performance.progress8_disadvantaged_gap::double precision
                            ),
                            ('engmath_5_plus_pct', performance.engmath_5_plus_pct::double precision),
                            ('engmath_4_plus_pct', performance.engmath_4_plus_pct::double precision),
                            ('ebacc_entry_pct', performance.ebacc_entry_pct::double precision),
                            ('ebacc_5_plus_pct', performance.ebacc_5_plus_pct::double precision),
                            ('ebacc_4_plus_pct', performance.ebacc_4_plus_pct::double precision),
                            (
                                'ks2_reading_expected_pct',
                                performance.ks2_reading_expected_pct::double precision
                            ),
                            (
                                'ks2_writing_expected_pct',
                                performance.ks2_writing_expected_pct::double precision
                            ),
                            (
                                'ks2_maths_expected_pct',
                                performance.ks2_maths_expected_pct::double precision
                            ),
                            (
                                'ks2_combined_expected_pct',
                                performance.ks2_combined_expected_pct::double precision
                            ),
                            (
                                'ks2_reading_higher_pct',
                                performance.ks2_reading_higher_pct::double precision
                            ),
                            (
                                'ks2_writing_higher_pct',
                                performance.ks2_writing_higher_pct::double precision
                            ),
                            (
                                'ks2_maths_higher_pct',
                                performance.ks2_maths_higher_pct::double precision
                            ),
                            (
                                'ks2_combined_higher_pct',
                                performance.ks2_combined_higher_pct::double precision
                            )
                    ) AS metric(metric_key, metric_value)

                    UNION ALL

                    SELECT
                        yearly_crime.urn,
                        yearly_crime.academic_year,
                        geo.phase,
                        geo.lad_code,
                        'area_crime_incidents_per_1000' AS metric_key,
                        yearly_crime.area_crime_incidents_per_1000 AS metric_value
                    FROM area_crime_yearly AS yearly_crime
                    INNER JOIN school_geo AS geo
                        ON geo.urn = yearly_crime.urn

                    UNION ALL

                    SELECT
                        yearly_prices.urn,
                        yearly_prices.academic_year,
                        geo.phase,
                        geo.lad_code,
                        metric.metric_key,
                        metric.metric_value
                    FROM area_house_price_yearly AS yearly_prices
                    INNER JOIN school_geo AS geo
                        ON geo.urn = yearly_prices.urn
                    CROSS JOIN LATERAL (
                        VALUES
                            (
                                'area_house_price_average',
                                yearly_prices.area_house_price_average::double precision
                            ),
                            (
                                'area_house_price_annual_change_pct',
                                yearly_prices.area_house_price_annual_change_pct::double precision
                            )
                    ) AS metric(metric_key, metric_value)
                ),
                school_metric_rows AS (
                    SELECT
                        metric_rows.metric_key,
                        metric_rows.academic_year,
                        metric_rows.metric_value AS school_value
                    FROM metric_rows
                    WHERE metric_rows.urn = :urn
                ),
                national_benchmarks AS (
                    SELECT
                        metric_rows.metric_key,
                        metric_rows.academic_year,
                        avg(metric_rows.metric_value) AS national_value
                    FROM metric_rows
                    WHERE metric_rows.metric_value IS NOT NULL
                    GROUP BY
                        metric_rows.metric_key,
                        metric_rows.academic_year
                ),
                local_benchmarks AS (
                    SELECT
                        metric_rows.metric_key,
                        metric_rows.academic_year,
                        avg(metric_rows.metric_value) AS local_value
                    FROM metric_rows
                    INNER JOIN target_school
                        ON TRUE
                    WHERE metric_rows.metric_value IS NOT NULL
                      AND (
                            (
                                target_school.lad_code IS NOT NULL
                                AND metric_rows.lad_code = target_school.lad_code
                            )
                            OR (
                                target_school.lad_code IS NULL
                                AND target_school.phase IS NOT NULL
                                AND metric_rows.phase = target_school.phase
                            )
                      )
                    GROUP BY
                        metric_rows.metric_key,
                        metric_rows.academic_year
                ),
                local_context AS (
                    SELECT
                        CASE
                            WHEN target_school.lad_code IS NOT NULL
                                THEN 'local_authority_district'
                            ELSE 'phase'
                        END AS local_scope,
                        coalesce(target_school.lad_code, target_school.phase, 'unknown')
                            AS local_area_code,
                        coalesce(target_school.lad_name, target_school.phase, 'Unknown')
                            AS local_area_label
                    FROM target_school
                )
                SELECT
                    school_metric_rows.metric_key,
                    school_metric_rows.academic_year,
                    school_metric_rows.school_value,
                    national_benchmarks.national_value,
                    local_benchmarks.local_value,
                    local_context.local_scope,
                    local_context.local_area_code,
                    local_context.local_area_label
                FROM school_metric_rows
                INNER JOIN local_context
                    ON TRUE
                LEFT JOIN national_benchmarks
                    ON national_benchmarks.metric_key = school_metric_rows.metric_key
                   AND national_benchmarks.academic_year = school_metric_rows.academic_year
                LEFT JOIN local_benchmarks
                    ON local_benchmarks.metric_key = school_metric_rows.metric_key
                   AND local_benchmarks.academic_year = school_metric_rows.academic_year
                """
            ),
            {"urn": urn},
        )
        .mappings()
        .all()
    )
    return tuple(dict(row) for row in rows)


def _persist_metric_benchmark_rows(
    connection: Connection,
    rows: Sequence[Mapping[str, object]],
) -> int:
    if len(rows) == 0 or not _table_exists(connection, "metric_benchmarks_yearly"):
        return 0

    upsert_rows: list[dict[str, object]] = []
    for row in rows:
        metric_key = _to_optional_str(row.get("metric_key"))
        academic_year = _to_optional_str(row.get("academic_year"))
        if metric_key is None or academic_year is None:
            continue

        national_value = _to_optional_float(row.get("national_value"))
        upsert_rows.append(
            {
                "metric_key": metric_key,
                "academic_year": academic_year,
                "benchmark_scope": "national",
                "benchmark_area": "england",
                "benchmark_label": "England",
                "benchmark_value": national_value,
            }
        )

        local_value = _to_optional_float(row.get("local_value"))
        local_scope = _to_benchmark_scope(row.get("local_scope"))
        local_area_code = _to_optional_str(row.get("local_area_code"))
        local_area_label = _to_optional_str(row.get("local_area_label"))
        if local_area_code is not None and local_area_label is not None:
            upsert_rows.append(
                {
                    "metric_key": metric_key,
                    "academic_year": academic_year,
                    "benchmark_scope": local_scope,
                    "benchmark_area": local_area_code,
                    "benchmark_label": local_area_label,
                    "benchmark_value": local_value,
                }
            )

    if len(upsert_rows) == 0:
        return 0

    if connection.dialect.name == "postgresql":
        connection.execute(
            text(
                """
                INSERT INTO metric_benchmarks_yearly (
                    metric_key,
                    academic_year,
                    benchmark_scope,
                    benchmark_area,
                    benchmark_label,
                    benchmark_value,
                    updated_at
                ) VALUES (
                    :metric_key,
                    :academic_year,
                    :benchmark_scope,
                    :benchmark_area,
                    :benchmark_label,
                    :benchmark_value,
                    timezone('utc', now())
                )
                ON CONFLICT (metric_key, academic_year, benchmark_scope, benchmark_area)
                DO UPDATE SET
                    benchmark_label = EXCLUDED.benchmark_label,
                    benchmark_value = EXCLUDED.benchmark_value,
                    updated_at = timezone('utc', now())
                """
            ),
            upsert_rows,
        )
        return len(upsert_rows)

    connection.execute(
        text(
            """
            INSERT INTO metric_benchmarks_yearly (
                metric_key,
                academic_year,
                benchmark_scope,
                benchmark_area,
                benchmark_label,
                benchmark_value,
                updated_at
            ) VALUES (
                :metric_key,
                :academic_year,
                :benchmark_scope,
                :benchmark_area,
                :benchmark_label,
                :benchmark_value,
                CURRENT_TIMESTAMP
            )
            ON CONFLICT(metric_key, academic_year, benchmark_scope, benchmark_area)
            DO UPDATE SET
                benchmark_label = excluded.benchmark_label,
                benchmark_value = excluded.benchmark_value,
                updated_at = CURRENT_TIMESTAMP
            """
        ),
        upsert_rows,
    )
    return len(upsert_rows)


def _rebuild_metric_benchmark_rows(connection: Connection) -> int:
    if not _table_exists(connection, "metric_benchmarks_yearly"):
        return 0

    connection.execute(text("DELETE FROM metric_benchmarks_yearly"))
    updated_at_expression = (
        "timezone('utc', now())" if connection.dialect.name == "postgresql" else "CURRENT_TIMESTAMP"
    )
    connection.execute(
        text(
            f"""
            WITH school_geo AS (
                SELECT
                    schools.urn,
                    schools.phase,
                    deprivation.local_authority_district_code AS lad_code,
                    deprivation.local_authority_district_name AS lad_name,
                    deprivation.population_total AS population_total
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
                GROUP BY
                    context.urn,
                    extract(year from context.month)::int
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
                GROUP BY
                    geo.urn,
                    extract(year from prices.month)::int
            ),
            metric_rows AS (
                SELECT
                    demographics.urn,
                    demographics.academic_year,
                    geo.phase,
                    geo.lad_code,
                    geo.lad_name,
                    metric.metric_key,
                    metric.metric_value
                FROM school_demographics_yearly AS demographics
                INNER JOIN school_geo AS geo
                    ON geo.urn = demographics.urn
                CROSS JOIN LATERAL (
                    VALUES
                        ('disadvantaged_pct', demographics.disadvantaged_pct::double precision),
                        ('fsm_pct', demographics.fsm_pct::double precision),
                        ('fsm6_pct', demographics.fsm6_pct::double precision),
                        ('sen_pct', demographics.sen_pct::double precision),
                        ('ehcp_pct', demographics.ehcp_pct::double precision),
                        ('eal_pct', demographics.eal_pct::double precision),
                        (
                            'first_language_english_pct',
                            demographics.first_language_english_pct::double precision
                        ),
                        (
                            'first_language_unclassified_pct',
                            demographics.first_language_unclassified_pct::double precision
                        ),
                        ('male_pct', demographics.male_pct::double precision),
                        ('female_pct', demographics.female_pct::double precision),
                        ('pupil_mobility_pct', demographics.pupil_mobility_pct::double precision)
                ) AS metric(metric_key, metric_value)

                UNION ALL

                SELECT
                    attendance.urn,
                    attendance.academic_year,
                    geo.phase,
                    geo.lad_code,
                    geo.lad_name,
                    metric.metric_key,
                    metric.metric_value
                FROM school_attendance_yearly AS attendance
                INNER JOIN school_geo AS geo
                    ON geo.urn = attendance.urn
                CROSS JOIN LATERAL (
                    VALUES
                        ('overall_attendance_pct', attendance.overall_attendance_pct::double precision),
                        ('overall_absence_pct', attendance.overall_absence_pct::double precision),
                        ('persistent_absence_pct', attendance.persistent_absence_pct::double precision)
                ) AS metric(metric_key, metric_value)

                UNION ALL

                SELECT
                    behaviour.urn,
                    behaviour.academic_year,
                    geo.phase,
                    geo.lad_code,
                    geo.lad_name,
                    metric.metric_key,
                    metric.metric_value
                FROM school_behaviour_yearly AS behaviour
                INNER JOIN school_geo AS geo
                    ON geo.urn = behaviour.urn
                CROSS JOIN LATERAL (
                    VALUES
                        ('suspensions_count', behaviour.suspensions_count::double precision),
                        ('suspensions_rate', behaviour.suspensions_rate::double precision),
                        (
                            'permanent_exclusions_count',
                            behaviour.permanent_exclusions_count::double precision
                        ),
                        (
                            'permanent_exclusions_rate',
                            behaviour.permanent_exclusions_rate::double precision
                        )
                ) AS metric(metric_key, metric_value)

                UNION ALL

                SELECT
                    workforce.urn,
                    workforce.academic_year,
                    geo.phase,
                    geo.lad_code,
                    geo.lad_name,
                    metric.metric_key,
                    metric.metric_value
                FROM school_workforce_yearly AS workforce
                INNER JOIN school_geo AS geo
                    ON geo.urn = workforce.urn
                CROSS JOIN LATERAL (
                    VALUES
                        ('pupil_teacher_ratio', workforce.pupil_teacher_ratio::double precision),
                        ('supply_staff_pct', workforce.supply_staff_pct::double precision),
                        (
                            'teachers_3plus_years_pct',
                            workforce.teachers_3plus_years_pct::double precision
                        ),
                        ('teacher_turnover_pct', workforce.teacher_turnover_pct::double precision),
                        ('qts_pct', workforce.qts_pct::double precision),
                        (
                            'qualifications_level6_plus_pct',
                            workforce.qualifications_level6_plus_pct::double precision
                        ),
                        (
                            'teacher_headcount_total',
                            workforce.teacher_headcount_total::double precision
                        ),
                        ('teacher_fte_total', workforce.teacher_fte_total::double precision),
                        (
                            'support_staff_headcount_total',
                            workforce.support_staff_headcount_total::double precision
                        ),
                        (
                            'support_staff_fte_total',
                            workforce.support_staff_fte_total::double precision
                        ),
                        (
                            'leadership_share_of_teachers',
                            workforce.leadership_share_of_teachers::double precision
                        ),
                        (
                            'teacher_average_mean_salary_gbp',
                            workforce.teacher_average_mean_salary_gbp::double precision
                        ),
                        (
                            'teacher_average_median_salary_gbp',
                            workforce.teacher_average_median_salary_gbp::double precision
                        ),
                        (
                            'teachers_on_leadership_pay_range_pct',
                            workforce.teachers_on_leadership_pay_range_pct::double precision
                        ),
                        (
                            'teacher_absence_pct',
                            workforce.teacher_absence_pct::double precision
                        ),
                        (
                            'teacher_absence_days_total',
                            workforce.teacher_absence_days_total::double precision
                        ),
                        (
                            'teacher_absence_days_average',
                            workforce.teacher_absence_days_average::double precision
                        ),
                        (
                            'teacher_absence_days_average_all_teachers',
                            workforce.teacher_absence_days_average_all_teachers::double precision
                        ),
                        (
                            'teacher_vacancy_count',
                            workforce.teacher_vacancy_count::double precision
                        ),
                        (
                            'teacher_vacancy_rate',
                            workforce.teacher_vacancy_rate::double precision
                        ),
                        (
                            'teacher_tempfilled_vacancy_count',
                            workforce.teacher_tempfilled_vacancy_count::double precision
                        ),
                        (
                            'teacher_tempfilled_vacancy_rate',
                            workforce.teacher_tempfilled_vacancy_rate::double precision
                        ),
                        (
                            'third_party_support_staff_headcount',
                            workforce.third_party_support_staff_headcount::double precision
                        )
                ) AS metric(metric_key, metric_value)

                UNION ALL

                SELECT
                    finance.urn,
                    finance.academic_year,
                    geo.phase,
                    geo.lad_code,
                    geo.lad_name,
                    metric.metric_key,
                    metric.metric_value
                FROM school_financials_yearly AS finance
                INNER JOIN school_geo AS geo
                    ON geo.urn = finance.urn
                CROSS JOIN LATERAL (
                    VALUES
                        (
                            'finance_income_per_pupil_gbp',
                            finance.income_per_pupil_gbp::double precision
                        ),
                        (
                            'finance_expenditure_per_pupil_gbp',
                            finance.expenditure_per_pupil_gbp::double precision
                        ),
                        (
                            'finance_staff_costs_pct_of_expenditure',
                            finance.staff_costs_pct_of_expenditure::double precision
                        ),
                        (
                            'finance_revenue_reserve_per_pupil_gbp',
                            finance.revenue_reserve_per_pupil_gbp::double precision
                        ),
                        (
                            'finance_teaching_staff_costs_per_pupil_gbp',
                            finance.teaching_staff_costs_per_pupil_gbp::double precision
                        )
                ) AS metric(metric_key, metric_value)

                UNION ALL

                SELECT
                    admissions.urn,
                    admissions.academic_year,
                    geo.phase,
                    geo.lad_code,
                    geo.lad_name,
                    metric.metric_key,
                    metric.metric_value
                FROM school_admissions_yearly AS admissions
                INNER JOIN school_geo AS geo
                    ON geo.urn = admissions.urn
                CROSS JOIN LATERAL (
                    VALUES
                        (
                            'admissions_oversubscription_ratio',
                            admissions.oversubscription_ratio::double precision
                        ),
                        (
                            'admissions_first_preference_offer_rate',
                            admissions.first_preference_offer_rate::double precision
                        ),
                        (
                            'admissions_any_preference_offer_rate',
                            admissions.any_preference_offer_rate::double precision
                        ),
                        (
                            'admissions_cross_la_applications',
                            admissions.cross_la_applications::double precision
                        )
                ) AS metric(metric_key, metric_value)

                UNION ALL

                SELECT
                    performance.urn,
                    performance.academic_year,
                    geo.phase,
                    geo.lad_code,
                    geo.lad_name,
                    metric.metric_key,
                    metric.metric_value
                FROM school_performance_yearly AS performance
                INNER JOIN school_geo AS geo
                    ON geo.urn = performance.urn
                CROSS JOIN LATERAL (
                    VALUES
                        ('attainment8_average', performance.attainment8_average::double precision),
                        ('progress8_average', performance.progress8_average::double precision),
                        (
                            'progress8_disadvantaged',
                            performance.progress8_disadvantaged::double precision
                        ),
                        (
                            'progress8_not_disadvantaged',
                            performance.progress8_not_disadvantaged::double precision
                        ),
                        (
                            'progress8_disadvantaged_gap',
                            performance.progress8_disadvantaged_gap::double precision
                        ),
                        ('engmath_5_plus_pct', performance.engmath_5_plus_pct::double precision),
                        ('engmath_4_plus_pct', performance.engmath_4_plus_pct::double precision),
                        ('ebacc_entry_pct', performance.ebacc_entry_pct::double precision),
                        ('ebacc_5_plus_pct', performance.ebacc_5_plus_pct::double precision),
                        ('ebacc_4_plus_pct', performance.ebacc_4_plus_pct::double precision),
                        (
                            'ks2_reading_expected_pct',
                            performance.ks2_reading_expected_pct::double precision
                        ),
                        (
                            'ks2_writing_expected_pct',
                            performance.ks2_writing_expected_pct::double precision
                        ),
                        (
                            'ks2_maths_expected_pct',
                            performance.ks2_maths_expected_pct::double precision
                        ),
                        (
                            'ks2_combined_expected_pct',
                            performance.ks2_combined_expected_pct::double precision
                        ),
                        (
                            'ks2_reading_higher_pct',
                            performance.ks2_reading_higher_pct::double precision
                        ),
                        (
                            'ks2_writing_higher_pct',
                            performance.ks2_writing_higher_pct::double precision
                        ),
                        (
                            'ks2_maths_higher_pct',
                            performance.ks2_maths_higher_pct::double precision
                        ),
                        (
                            'ks2_combined_higher_pct',
                            performance.ks2_combined_higher_pct::double precision
                        )
                ) AS metric(metric_key, metric_value)

                UNION ALL

                SELECT
                    yearly_crime.urn,
                    yearly_crime.academic_year,
                    geo.phase,
                    geo.lad_code,
                    geo.lad_name,
                    'area_crime_incidents_per_1000' AS metric_key,
                    yearly_crime.area_crime_incidents_per_1000 AS metric_value
                FROM area_crime_yearly AS yearly_crime
                INNER JOIN school_geo AS geo
                    ON geo.urn = yearly_crime.urn

                UNION ALL

                SELECT
                    yearly_prices.urn,
                    yearly_prices.academic_year,
                    geo.phase,
                    geo.lad_code,
                    geo.lad_name,
                    metric.metric_key,
                    metric.metric_value
                FROM area_house_price_yearly AS yearly_prices
                INNER JOIN school_geo AS geo
                    ON geo.urn = yearly_prices.urn
                CROSS JOIN LATERAL (
                    VALUES
                        (
                            'area_house_price_average',
                            yearly_prices.area_house_price_average::double precision
                        ),
                        (
                            'area_house_price_annual_change_pct',
                            yearly_prices.area_house_price_annual_change_pct::double precision
                        )
                ) AS metric(metric_key, metric_value)
            ),
            national_benchmark_values AS (
                SELECT
                    metric_rows.metric_key,
                    metric_rows.academic_year,
                    avg(metric_rows.metric_value) AS benchmark_value
                FROM metric_rows
                WHERE metric_rows.metric_value IS NOT NULL
                GROUP BY
                    metric_rows.metric_key,
                    metric_rows.academic_year
            ),
            lad_benchmark_values AS (
                SELECT
                    metric_rows.metric_key,
                    metric_rows.academic_year,
                    metric_rows.lad_code,
                    avg(metric_rows.metric_value) AS benchmark_value
                FROM metric_rows
                WHERE metric_rows.metric_value IS NOT NULL
                  AND metric_rows.lad_code IS NOT NULL
                GROUP BY
                    metric_rows.metric_key,
                    metric_rows.academic_year,
                    metric_rows.lad_code
            ),
            phase_benchmark_values AS (
                SELECT
                    metric_rows.metric_key,
                    metric_rows.academic_year,
                    metric_rows.phase,
                    avg(metric_rows.metric_value) AS benchmark_value
                FROM metric_rows
                WHERE metric_rows.metric_value IS NOT NULL
                  AND metric_rows.phase IS NOT NULL
                GROUP BY
                    metric_rows.metric_key,
                    metric_rows.academic_year,
                    metric_rows.phase
            )
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
                benchmark_rows.metric_key,
                benchmark_rows.academic_year,
                benchmark_rows.benchmark_scope,
                benchmark_rows.benchmark_area,
                benchmark_rows.benchmark_label,
                benchmark_rows.benchmark_value,
                {updated_at_expression}
            FROM (
                SELECT DISTINCT
                    metric_rows.metric_key,
                    metric_rows.academic_year,
                    'national' AS benchmark_scope,
                    'england' AS benchmark_area,
                    'England' AS benchmark_label,
                    national_benchmark_values.benchmark_value
                FROM metric_rows
                LEFT JOIN national_benchmark_values
                    ON national_benchmark_values.metric_key = metric_rows.metric_key
                   AND national_benchmark_values.academic_year = metric_rows.academic_year

                UNION ALL

                SELECT DISTINCT
                    metric_rows.metric_key,
                    metric_rows.academic_year,
                    'local_authority_district' AS benchmark_scope,
                    metric_rows.lad_code AS benchmark_area,
                    coalesce(metric_rows.lad_name, metric_rows.lad_code, 'Unknown')
                        AS benchmark_label,
                    lad_benchmark_values.benchmark_value
                FROM metric_rows
                LEFT JOIN lad_benchmark_values
                    ON lad_benchmark_values.metric_key = metric_rows.metric_key
                   AND lad_benchmark_values.academic_year = metric_rows.academic_year
                   AND lad_benchmark_values.lad_code = metric_rows.lad_code
                WHERE metric_rows.lad_code IS NOT NULL

                UNION ALL

                SELECT DISTINCT
                    metric_rows.metric_key,
                    metric_rows.academic_year,
                    'phase' AS benchmark_scope,
                    metric_rows.phase AS benchmark_area,
                    metric_rows.phase AS benchmark_label,
                    phase_benchmark_values.benchmark_value
                FROM metric_rows
                LEFT JOIN phase_benchmark_values
                    ON phase_benchmark_values.metric_key = metric_rows.metric_key
                   AND phase_benchmark_values.academic_year = metric_rows.academic_year
                   AND phase_benchmark_values.phase = metric_rows.phase
                WHERE metric_rows.phase IS NOT NULL
            ) AS benchmark_rows
            """
        )
    )
    return int(
        connection.execute(text("SELECT count(*) FROM metric_benchmarks_yearly")).scalar_one()
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
