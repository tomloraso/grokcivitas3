from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from civitas.application.school_profiles.errors import SchoolProfileDataUnavailableError
from civitas.application.school_profiles.ports.school_profile_repository import (
    SchoolProfileRepository,
)
from civitas.domain.school_profiles.models import (
    SchoolDemographicsCoverage,
    SchoolDemographicsLatest,
    SchoolOfstedLatest,
    SchoolProfile,
    SchoolProfileSchool,
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
        )


def _to_optional_float(value: object) -> float | None:
    if value is None:
        return None
    return float(str(value))


def _to_optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)
