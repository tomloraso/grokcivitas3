from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from datetime import date

from sqlalchemy import bindparam, text
from sqlalchemy.engine import Engine, RowMapping
from sqlalchemy.sql.elements import TextClause

from civitas.application.school_summaries.ports.summary_context_repository import (
    SummaryContextRepository,
)
from civitas.domain.school_summaries.models import (
    CrimeCategoryCount,
    InspectionHistoryPoint,
    MetricTrendPoint,
    SchoolAnalystContext,
    SchoolOverviewContext,
)


class PostgresSummaryContextRepository(SummaryContextRepository):
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def list_overview_contexts(
        self,
        urns: Sequence[str] | None = None,
    ) -> list[SchoolOverviewContext]:
        with self._engine.connect() as connection:
            statement, params = _overview_statement(urns)
            rows = connection.execute(statement, params).mappings()
            return [_map_overview_context(row) for row in rows]

    def list_analyst_contexts(
        self,
        urns: Sequence[str] | None = None,
    ) -> list[SchoolAnalystContext]:
        with self._engine.connect() as connection:
            statement, params = _analyst_statement(urns)
            rows = connection.execute(statement, params).mappings()
            return [_map_analyst_context(row) for row in rows]


def _overview_statement(
    urns: Sequence[str] | None,
) -> tuple[TextClause, dict[str, object]]:
    query = """
        SELECT
            schools.urn,
            schools.name,
            schools.phase,
            schools.type AS school_type,
            schools.status,
            schools.postcode,
            schools.website,
            schools.telephone,
            NULLIF(
                trim(
                    concat_ws(
                        ' ',
                        schools.head_title,
                        schools.head_first_name,
                        schools.head_last_name
                    )
                ),
                ''
            ) AS head_name,
            schools.head_job_title,
            schools.statutory_low_age,
            schools.statutory_high_age,
            schools.gender,
            schools.religious_character,
            schools.admissions_policy,
            schools.sixth_form,
            schools.trust_name,
            schools.la_name,
            schools.urban_rural,
            schools.pupil_count,
            schools.capacity,
            schools.number_of_boys,
            schools.number_of_girls,
            demographics.fsm_pct,
            demographics.eal_pct,
            demographics.sen_pct,
            demographics.ehcp_pct,
            performance.progress8_average AS progress_8,
            performance.attainment8_average AS attainment_8,
            performance.ks2_reading_expected_pct AS ks2_reading_met,
            performance.ks2_maths_expected_pct AS ks2_maths_met,
            ofsted.overall_effectiveness_label AS overall_effectiveness,
            COALESCE(
                ofsted.latest_oeif_inspection_start_date,
                ofsted.inspection_start_date,
                ofsted.latest_ungraded_inspection_date
            ) AS inspection_date,
            deprivation.imd_decile
        FROM schools
        LEFT JOIN LATERAL (
            SELECT
                fsm_pct,
                eal_pct,
                sen_pct,
                ehcp_pct
            FROM school_demographics_yearly
            WHERE school_demographics_yearly.urn = schools.urn
            ORDER BY substring(academic_year from 1 for 4)::integer DESC, academic_year DESC
            LIMIT 1
        ) AS demographics ON TRUE
        LEFT JOIN LATERAL (
            SELECT
                progress8_average,
                attainment8_average,
                ks2_reading_expected_pct,
                ks2_maths_expected_pct
            FROM school_performance_yearly
            WHERE school_performance_yearly.urn = schools.urn
            ORDER BY substring(academic_year from 1 for 4)::integer DESC, academic_year DESC
            LIMIT 1
        ) AS performance ON TRUE
        LEFT JOIN school_ofsted_latest AS ofsted
            ON ofsted.urn = schools.urn
        LEFT JOIN area_deprivation AS deprivation
            ON deprivation.lsoa_code = schools.lsoa_code
    """
    return _statement_with_optional_urn_filter(query, urns)


def _analyst_statement(
    urns: Sequence[str] | None,
) -> tuple[TextClause, dict[str, object]]:
    query = """
        SELECT
            schools.urn,
            schools.name,
            schools.phase,
            schools.type AS school_type,
            schools.status,
            schools.postcode,
            schools.website,
            schools.telephone,
            NULLIF(
                trim(
                    concat_ws(
                        ' ',
                        schools.head_title,
                        schools.head_first_name,
                        schools.head_last_name
                    )
                ),
                ''
            ) AS head_name,
            schools.head_job_title,
            schools.statutory_low_age,
            schools.statutory_high_age,
            schools.gender,
            schools.religious_character,
            schools.admissions_policy,
            schools.sixth_form,
            schools.trust_name,
            schools.la_name,
            schools.urban_rural,
            schools.pupil_count,
            schools.capacity,
            schools.number_of_boys,
            schools.number_of_girls,
            demographics_latest.fsm_pct,
            demographics_latest.eal_pct,
            demographics_latest.sen_pct,
            demographics_latest.ehcp_pct,
            performance_latest.progress8_average AS progress_8,
            performance_latest.attainment8_average AS attainment_8,
            performance_latest.ks2_reading_expected_pct AS ks2_reading_met,
            performance_latest.ks2_maths_expected_pct AS ks2_maths_met,
            ofsted.overall_effectiveness_label AS overall_effectiveness,
            COALESCE(
                ofsted.latest_oeif_inspection_start_date,
                ofsted.inspection_start_date,
                ofsted.latest_ungraded_inspection_date
            ) AS inspection_date,
            deprivation.imd_decile,
            ofsted.quality_of_education_label AS quality_of_education,
            ofsted.behaviour_and_attitudes_label AS behaviour_and_attitudes,
            ofsted.personal_development_label AS personal_development,
            ofsted.leadership_and_management_label AS leadership_and_management,
            deprivation.imd_rank,
            deprivation.idaci_decile,
            demographics_trends.fsm_pct_trend,
            demographics_trends.eal_pct_trend,
            demographics_trends.sen_pct_trend,
            performance_trends.progress_8_trend,
            performance_trends.attainment_8_trend,
            inspection_history.inspection_history,
            crime_context.total_incidents_12m,
            crime_context.top_crime_categories
        FROM schools
        LEFT JOIN LATERAL (
            SELECT
                fsm_pct,
                eal_pct,
                sen_pct,
                ehcp_pct
            FROM school_demographics_yearly
            WHERE school_demographics_yearly.urn = schools.urn
            ORDER BY substring(academic_year from 1 for 4)::integer DESC, academic_year DESC
            LIMIT 1
        ) AS demographics_latest ON TRUE
        LEFT JOIN LATERAL (
            SELECT
                json_agg(
                    json_build_object('year', academic_year, 'value', fsm_pct)
                    ORDER BY substring(academic_year from 1 for 4)::integer DESC, academic_year DESC
                ) FILTER (WHERE fsm_pct IS NOT NULL) AS fsm_pct_trend,
                json_agg(
                    json_build_object('year', academic_year, 'value', eal_pct)
                    ORDER BY substring(academic_year from 1 for 4)::integer DESC, academic_year DESC
                ) FILTER (WHERE eal_pct IS NOT NULL) AS eal_pct_trend,
                json_agg(
                    json_build_object('year', academic_year, 'value', sen_pct)
                    ORDER BY substring(academic_year from 1 for 4)::integer DESC, academic_year DESC
                ) FILTER (WHERE sen_pct IS NOT NULL) AS sen_pct_trend
            FROM school_demographics_yearly
            WHERE school_demographics_yearly.urn = schools.urn
        ) AS demographics_trends ON TRUE
        LEFT JOIN LATERAL (
            SELECT
                progress8_average,
                attainment8_average,
                ks2_reading_expected_pct,
                ks2_maths_expected_pct
            FROM school_performance_yearly
            WHERE school_performance_yearly.urn = schools.urn
            ORDER BY substring(academic_year from 1 for 4)::integer DESC, academic_year DESC
            LIMIT 1
        ) AS performance_latest ON TRUE
        LEFT JOIN LATERAL (
            SELECT
                json_agg(
                    json_build_object('year', academic_year, 'value', progress8_average)
                    ORDER BY substring(academic_year from 1 for 4)::integer DESC, academic_year DESC
                ) FILTER (WHERE progress8_average IS NOT NULL) AS progress_8_trend,
                json_agg(
                    json_build_object('year', academic_year, 'value', attainment8_average)
                    ORDER BY substring(academic_year from 1 for 4)::integer DESC, academic_year DESC
                ) FILTER (WHERE attainment8_average IS NOT NULL) AS attainment_8_trend
            FROM school_performance_yearly
            WHERE school_performance_yearly.urn = schools.urn
        ) AS performance_trends ON TRUE
        LEFT JOIN school_ofsted_latest AS ofsted
            ON ofsted.urn = schools.urn
        LEFT JOIN LATERAL (
            SELECT
                json_agg(
                    json_build_object(
                        'inspection_date',
                        inspection_start_date,
                        'overall_effectiveness',
                        overall_effectiveness_label
                    )
                    ORDER BY inspection_start_date DESC
                ) FILTER (WHERE inspection_start_date IS NOT NULL) AS inspection_history
            FROM ofsted_inspections
            WHERE ofsted_inspections.urn = schools.urn
        ) AS inspection_history ON TRUE
        LEFT JOIN area_deprivation AS deprivation
            ON deprivation.lsoa_code = schools.lsoa_code
        LEFT JOIN LATERAL (
            SELECT
                CAST(COALESCE(SUM(area_crime_context.incident_count), 0) AS integer)
                    AS total_incidents_12m,
                (
                    SELECT json_agg(
                        json_build_object(
                            'category',
                            category_totals.crime_category,
                            'incident_count',
                            category_totals.total_incidents
                        )
                        ORDER BY
                            category_totals.total_incidents DESC,
                            category_totals.crime_category ASC
                    )
                    FROM (
                        SELECT
                            crime_category,
                            CAST(SUM(incident_count) AS integer) AS total_incidents
                        FROM area_crime_context
                        WHERE area_crime_context.urn = schools.urn
                        GROUP BY crime_category
                    ) AS category_totals
                ) AS top_crime_categories
            FROM area_crime_context
            WHERE area_crime_context.urn = schools.urn
        ) AS crime_context ON TRUE
    """
    return _statement_with_optional_urn_filter(query, urns)


def _statement_with_optional_urn_filter(
    query: str,
    urns: Sequence[str] | None,
) -> tuple[TextClause, dict[str, object]]:
    if urns is None:
        return text(query + " ORDER BY schools.urn ASC"), {}
    return (
        text(query + " WHERE schools.urn IN :urns ORDER BY schools.urn ASC").bindparams(
            bindparam("urns", expanding=True)
        ),
        {"urns": list(urns)},
    )


def _map_overview_context(row: RowMapping) -> SchoolOverviewContext:
    return SchoolOverviewContext(
        urn=str(row["urn"]),
        name=str(row["name"]),
        phase=_to_optional_str(row["phase"]),
        school_type=_to_optional_str(row["school_type"]),
        status=_to_optional_str(row["status"]),
        postcode=_to_optional_str(row["postcode"]),
        website=_to_optional_str(row["website"]),
        telephone=_to_optional_str(row["telephone"]),
        head_name=_to_optional_str(row["head_name"]),
        head_job_title=_to_optional_str(row["head_job_title"]),
        statutory_low_age=_to_optional_int(row["statutory_low_age"]),
        statutory_high_age=_to_optional_int(row["statutory_high_age"]),
        gender=_to_optional_str(row["gender"]),
        religious_character=_to_optional_str(row["religious_character"]),
        admissions_policy=_to_optional_str(row["admissions_policy"]),
        sixth_form=_to_optional_str(row["sixth_form"]),
        trust_name=_to_optional_str(row["trust_name"]),
        la_name=_to_optional_str(row["la_name"]),
        urban_rural=_to_optional_str(row["urban_rural"]),
        pupil_count=_to_optional_int(row["pupil_count"]),
        capacity=_to_optional_int(row["capacity"]),
        number_of_boys=_to_optional_int(row["number_of_boys"]),
        number_of_girls=_to_optional_int(row["number_of_girls"]),
        fsm_pct=_to_optional_float(row["fsm_pct"]),
        eal_pct=_to_optional_float(row["eal_pct"]),
        sen_pct=_to_optional_float(row["sen_pct"]),
        ehcp_pct=_to_optional_float(row["ehcp_pct"]),
        progress_8=_to_optional_float(row["progress_8"]),
        attainment_8=_to_optional_float(row["attainment_8"]),
        ks2_reading_met=_to_optional_float(row["ks2_reading_met"]),
        ks2_maths_met=_to_optional_float(row["ks2_maths_met"]),
        overall_effectiveness=_to_optional_str(row["overall_effectiveness"]),
        inspection_date=_to_optional_date(row["inspection_date"]),
        imd_decile=_to_optional_int(row["imd_decile"]),
    )


def _map_analyst_context(row: RowMapping) -> SchoolAnalystContext:
    overview = _map_overview_context(row)
    return SchoolAnalystContext(
        **overview.__dict__,
        fsm_pct_trend=_to_metric_trend_points(row["fsm_pct_trend"]),
        eal_pct_trend=_to_metric_trend_points(row["eal_pct_trend"]),
        sen_pct_trend=_to_metric_trend_points(row["sen_pct_trend"]),
        progress_8_trend=_to_metric_trend_points(row["progress_8_trend"]),
        attainment_8_trend=_to_metric_trend_points(row["attainment_8_trend"]),
        quality_of_education=_to_optional_str(row["quality_of_education"]),
        behaviour_and_attitudes=_to_optional_str(row["behaviour_and_attitudes"]),
        personal_development=_to_optional_str(row["personal_development"]),
        leadership_and_management=_to_optional_str(row["leadership_and_management"]),
        inspection_history=_to_inspection_history(row["inspection_history"]),
        imd_rank=_to_optional_int(row["imd_rank"]),
        idaci_decile=_to_optional_int(row["idaci_decile"]),
        total_incidents_12m=_to_optional_int(row["total_incidents_12m"]),
        top_crime_categories=_to_crime_categories(row["top_crime_categories"]),
    )


def _to_metric_trend_points(value: object) -> tuple[MetricTrendPoint, ...]:
    return tuple(
        MetricTrendPoint(
            year=_required_str(item, "year"),
            value=_optional_float_from_mapping(item, "value"),
        )
        for item in _mapping_sequence(value)
    )


def _to_inspection_history(value: object) -> tuple[InspectionHistoryPoint, ...]:
    return tuple(
        InspectionHistoryPoint(
            inspection_date=_required_date(item, "inspection_date"),
            overall_effectiveness=_optional_str_from_mapping(item, "overall_effectiveness"),
        )
        for item in _mapping_sequence(value)
    )


def _to_crime_categories(value: object) -> tuple[CrimeCategoryCount, ...]:
    return tuple(
        CrimeCategoryCount(
            category=_required_str(item, "category"),
            incident_count=_required_int(item, "incident_count"),
        )
        for item in _mapping_sequence(value)
    )


def _mapping_sequence(value: object) -> tuple[Mapping[str, object], ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        parsed = json.loads(value)
        if not isinstance(parsed, list):
            return ()
        return tuple(item for item in parsed if isinstance(item, Mapping))
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return tuple(item for item in value if isinstance(item, Mapping))
    return ()


def _required_str(mapping: Mapping[str, object], key: str) -> str:
    value = mapping.get(key)
    if isinstance(value, str):
        normalized = value.strip()
        if normalized:
            return normalized
    raise TypeError(f"Expected non-empty string for '{key}'.")


def _optional_str_from_mapping(mapping: Mapping[str, object], key: str) -> str | None:
    return _to_optional_str(mapping.get(key))


def _required_int(mapping: Mapping[str, object], key: str) -> int:
    value = _to_optional_int(mapping.get(key))
    if value is None:
        raise TypeError(f"Expected integer for '{key}'.")
    return value


def _optional_float_from_mapping(mapping: Mapping[str, object], key: str) -> float | None:
    return _to_optional_float(mapping.get(key))


def _required_date(mapping: Mapping[str, object], key: str) -> date:
    value = _to_optional_date(mapping.get(key))
    if value is None:
        raise TypeError(f"Expected date for '{key}'.")
    return value


def _to_optional_str(value: object) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _to_optional_int(value: object) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str) and value.strip():
        return int(float(value.strip()))
    raise TypeError(f"Expected optional integer-compatible value, got {type(value).__name__}.")


def _to_optional_float(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str) and value.strip():
        return float(value.strip())
    raise TypeError(f"Expected optional float-compatible value, got {type(value).__name__}.")


def _to_optional_date(value: object) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value.strip():
        return date.fromisoformat(value.strip())
    raise TypeError(f"Expected optional date-compatible value, got {type(value).__name__}.")
