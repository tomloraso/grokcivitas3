from __future__ import annotations

from datetime import datetime
from typing import TypedDict
from uuid import UUID, uuid4

from sqlalchemy import bindparam, text
from sqlalchemy.engine import Connection, Engine, RowMapping

from civitas.application.favourites.dto import (
    AccountFavouriteSchoolDto,
    PostcodeSchoolSearchAcademicMetricDto,
    PostcodeSchoolSearchLatestOfstedDto,
)
from civitas.application.favourites.errors import SavedSchoolNotFoundError
from civitas.application.favourites.ports.favourite_repository import FavouriteRepository
from civitas.domain.favourites.models import SavedSchool

PRIMARY_METRIC_KEY = "ks2_combined_expected_pct"
PRIMARY_METRIC_LABEL = "KS2 expected standard"
SECONDARY_METRIC_KEY = "progress8_average"
SECONDARY_METRIC_LABEL = "Progress 8"


class AcademicMetricSummary(TypedDict):
    metric_key: str
    label: str
    sort_value: float | None
    availability: str


class PostgresFavouriteRepository(FavouriteRepository):
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def get_saved_school(self, *, user_id: UUID, school_urn: str) -> SavedSchool | None:
        with self._engine.connect() as connection:
            row = _select_saved_school(
                connection=connection,
                user_id=user_id,
                school_urn=school_urn,
            )
        return None if row is None else _map_saved_school_row(row)

    def create_saved_school(
        self,
        *,
        user_id: UUID,
        school_urn: str,
        created_at: datetime,
    ) -> SavedSchool:
        with self._engine.begin() as connection:
            existing = _select_saved_school(
                connection=connection,
                user_id=user_id,
                school_urn=school_urn,
            )
            if existing is not None:
                return _map_saved_school_row(existing)

            school_exists = connection.execute(
                text(
                    """
                    SELECT 1
                    FROM schools
                    WHERE urn = :school_urn
                    """
                ),
                {"school_urn": school_urn},
            ).first()
            if school_exists is None:
                raise SavedSchoolNotFoundError(school_urn)

            connection.execute(
                text(
                    """
                    INSERT INTO saved_schools (
                        id,
                        user_id,
                        school_urn,
                        created_at
                    ) VALUES (
                        :id,
                        :user_id,
                        :school_urn,
                        :created_at
                    )
                    ON CONFLICT (user_id, school_urn) DO NOTHING
                    """
                ),
                {
                    "id": uuid4(),
                    "user_id": user_id,
                    "school_urn": school_urn,
                    "created_at": created_at,
                },
            )

            row = _select_saved_school(
                connection=connection,
                user_id=user_id,
                school_urn=school_urn,
            )
            if row is None:
                raise RuntimeError("saved school insert did not persist a row")
            return _map_saved_school_row(row)

    def delete_saved_school(self, *, saved_school_id: UUID) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    """
                    DELETE FROM saved_schools
                    WHERE id = :saved_school_id
                    """
                ),
                {"saved_school_id": saved_school_id},
            )

    def list_saved_schools(
        self,
        *,
        user_id: UUID,
        school_urns: tuple[str, ...] | None = None,
    ) -> tuple[SavedSchool, ...]:
        with self._engine.connect() as connection:
            if school_urns is None:
                rows = connection.execute(
                    text(
                        """
                        SELECT
                            id,
                            user_id,
                            school_urn,
                            created_at
                        FROM saved_schools
                        WHERE user_id = :user_id
                        ORDER BY created_at DESC, school_urn ASC
                        """
                    ),
                    {"user_id": user_id},
                ).mappings()
                return tuple(_map_saved_school_row(row) for row in rows)

            if len(school_urns) == 0:
                return ()

            rows = connection.execute(
                text(
                    """
                    SELECT
                        id,
                        user_id,
                        school_urn,
                        created_at
                    FROM saved_schools
                    WHERE user_id = :user_id
                      AND school_urn IN :school_urns
                    ORDER BY created_at DESC, school_urn ASC
                    """
                ).bindparams(bindparam("school_urns", expanding=True)),
                {"user_id": user_id, "school_urns": list(school_urns)},
            ).mappings()
            return tuple(_map_saved_school_row(row) for row in rows)

    def list_saved_school_summaries(
        self,
        *,
        user_id: UUID,
    ) -> tuple[AccountFavouriteSchoolDto, ...]:
        with self._engine.connect() as connection:
            rows = connection.execute(
                text(
                    """
                    SELECT
                        schools.urn,
                        schools.name AS school_name,
                        schools.type AS school_type,
                        schools.phase AS school_phase,
                        schools.postcode AS school_postcode,
                        schools.pupil_count AS school_pupil_count,
                        summary.name AS summary_name,
                        summary.type AS summary_type,
                        summary.phase AS summary_phase,
                        summary.postcode AS summary_postcode,
                        summary.pupil_count AS summary_pupil_count,
                        summary.latest_ofsted_label,
                        summary.latest_ofsted_sort_rank,
                        summary.latest_ofsted_availability,
                        summary.primary_academic_metric_key,
                        summary.primary_academic_metric_label,
                        summary.primary_academic_metric_value,
                        summary.primary_academic_metric_availability,
                        summary.secondary_academic_metric_key,
                        summary.secondary_academic_metric_label,
                        summary.secondary_academic_metric_value,
                        summary.secondary_academic_metric_availability,
                        saved_schools.created_at AS saved_at
                    FROM saved_schools
                    INNER JOIN schools
                        ON schools.urn = saved_schools.school_urn
                    LEFT JOIN school_search_summary AS summary
                        ON summary.urn = saved_schools.school_urn
                    WHERE saved_schools.user_id = :user_id
                    ORDER BY saved_schools.created_at DESC, schools.urn ASC
                    """
                ),
                {"user_id": user_id},
            ).mappings()
            return tuple(_map_saved_school_summary_row(row) for row in rows)


def _select_saved_school(
    *,
    connection: Connection,
    user_id: UUID,
    school_urn: str,
) -> RowMapping | None:
    return (
        connection.execute(
            text(
                """
                SELECT
                    id,
                    user_id,
                    school_urn,
                    created_at
                FROM saved_schools
                WHERE user_id = :user_id
                  AND school_urn = :school_urn
                """
            ),
            {"user_id": user_id, "school_urn": school_urn},
        )
        .mappings()
        .first()
    )


def _map_saved_school_row(row: RowMapping) -> SavedSchool:
    return SavedSchool(
        id=_to_uuid(row["id"]),
        user_id=_to_uuid(row["user_id"]),
        school_urn=str(row["school_urn"]),
        created_at=_to_datetime(row["created_at"]),
    )


def _map_saved_school_summary_row(row: RowMapping) -> AccountFavouriteSchoolDto:
    phase = _optional_text(row["summary_phase"]) or _optional_text(row["school_phase"])
    name = _required_summary_text(row, "name")
    metric = _resolve_academic_metric_summary(row=row, phase=phase)
    return AccountFavouriteSchoolDto(
        urn=str(row["urn"]),
        name=name,
        school_type=_summary_text(row, "type"),
        phase=phase,
        postcode=_summary_text(row, "postcode"),
        pupil_count=_summary_int(row, "pupil_count"),
        latest_ofsted=PostcodeSchoolSearchLatestOfstedDto(
            label=_optional_text(row["latest_ofsted_label"]),
            sort_rank=_optional_int(row["latest_ofsted_sort_rank"]),
            availability=_optional_text(row["latest_ofsted_availability"]) or "not_published",
        ),
        academic_metric=PostcodeSchoolSearchAcademicMetricDto(
            metric_key=metric["metric_key"],
            label=metric["label"],
            display_value=_format_academic_metric(metric["metric_key"], metric["sort_value"]),
            sort_value=metric["sort_value"],
            availability=metric["availability"],
        ),
        saved_at=_to_datetime(row["saved_at"]),
    )


def _summary_text(row: RowMapping, field_name: str) -> str | None:
    return _optional_text(row[f"summary_{field_name}"]) or _optional_text(
        row[f"school_{field_name}"]
    )


def _required_summary_text(row: RowMapping, field_name: str) -> str:
    value = _summary_text(row, field_name)
    if value is None:
        raise TypeError(f"Expected a non-null value for {field_name}.")
    return value


def _summary_int(row: RowMapping, field_name: str) -> int | None:
    summary_value = _optional_int(row[f"summary_{field_name}"])
    if summary_value is not None:
        return summary_value
    return _optional_int(row[f"school_{field_name}"])


def _resolve_academic_metric_summary(
    *,
    row: RowMapping,
    phase: str | None,
) -> AcademicMetricSummary:
    primary = _academic_metric_choice(
        metric_key=_optional_text(row["primary_academic_metric_key"]) or PRIMARY_METRIC_KEY,
        label=_optional_text(row["primary_academic_metric_label"]) or PRIMARY_METRIC_LABEL,
        sort_value=_optional_float(row["primary_academic_metric_value"]),
        availability=_optional_text(row["primary_academic_metric_availability"]),
        fallback_availability="not_published"
        if phase in {"Primary", "Middle deemed primary", "All-through"}
        else "unsupported",
    )
    secondary = _academic_metric_choice(
        metric_key=_optional_text(row["secondary_academic_metric_key"]) or SECONDARY_METRIC_KEY,
        label=_optional_text(row["secondary_academic_metric_label"]) or SECONDARY_METRIC_LABEL,
        sort_value=_optional_float(row["secondary_academic_metric_value"]),
        availability=_optional_text(row["secondary_academic_metric_availability"]),
        fallback_availability="not_published"
        if phase in {"Secondary", "Middle deemed secondary"}
        else ("not_published" if phase == "All-through" else "unsupported"),
    )
    if phase in {"Primary", "Middle deemed primary", "All-through"}:
        return primary
    if phase in {"Secondary", "Middle deemed secondary"}:
        return secondary
    if secondary["availability"] != "unsupported":
        return secondary
    return primary


def _academic_metric_choice(
    *,
    metric_key: str,
    label: str,
    sort_value: float | None,
    availability: str | None,
    fallback_availability: str,
) -> AcademicMetricSummary:
    return {
        "metric_key": metric_key,
        "label": label,
        "sort_value": sort_value,
        "availability": availability or fallback_availability,
    }


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


def _to_uuid(value: object) -> UUID:
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


def _to_datetime(value: object) -> datetime:
    if isinstance(value, datetime):
        return value
    raise TypeError(f"Expected datetime, got {type(value).__name__}.")
