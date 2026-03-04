from __future__ import annotations

from datetime import datetime

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from civitas.application.school_trends.errors import SchoolTrendsDataUnavailableError
from civitas.application.school_trends.ports.school_trends_repository import SchoolTrendsRepository
from civitas.domain.school_trends.models import (
    SchoolDemographicsSeries,
    SchoolDemographicsYearlyRow,
)


class PostgresSchoolTrendsRepository(SchoolTrendsRepository):
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def get_demographics_series(self, urn: str) -> SchoolDemographicsSeries | None:
        try:
            with self._engine.connect() as connection:
                school_exists = (
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
                if school_exists is None:
                    return None

                rows = (
                    connection.execute(
                        text(
                            """
                            SELECT
                                academic_year,
                                disadvantaged_pct,
                                sen_pct,
                                ehcp_pct,
                                eal_pct,
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
                    sen_pct=_to_optional_float(row["sen_pct"]),
                    ehcp_pct=_to_optional_float(row["ehcp_pct"]),
                    eal_pct=_to_optional_float(row["eal_pct"]),
                )
                for row in rows
            ),
            latest_updated_at=_max_optional_updated_at(tuple(row["updated_at"] for row in rows)),
        )


def _to_optional_float(value: object) -> float | None:
    if value is None:
        return None
    return float(str(value))


def _max_optional_updated_at(values: tuple[object, ...]) -> datetime | None:
    non_null_values = [value for value in values if isinstance(value, datetime)]
    if len(non_null_values) == 0:
        return None
    return max(non_null_values)
