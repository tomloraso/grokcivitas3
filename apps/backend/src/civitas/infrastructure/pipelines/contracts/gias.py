from __future__ import annotations

from datetime import date, datetime
from typing import Mapping, Sequence, TypedDict

CONTRACT_VERSION = "gias.v1"

REQUIRED_HEADERS: tuple[str, ...] = (
    "URN",
    "EstablishmentName",
    "TypeOfEstablishment (name)",
    "PhaseOfEducation (name)",
    "EstablishmentStatus (name)",
    "Postcode",
    "Easting",
    "Northing",
    "OpenDate",
    "CloseDate",
    "NumberOfPupils",
    "SchoolCapacity",
)

NUMERIC_SENTINELS: set[str] = {"", "SUPP", "NE", "N/A", "NA", "X"}
EASTING_RANGE = (0.0, 700000.0)
NORTHING_RANGE = (0.0, 1300000.0)


class NormalizedGiasRow(TypedDict):
    urn: str
    name: str
    phase: str | None
    school_type: str | None
    status: str | None
    postcode: str | None
    easting: float
    northing: float
    open_date: date | None
    close_date: date | None
    pupil_count: int | None
    capacity: int | None


def normalize_postcode(raw_postcode: str | None) -> str | None:
    if raw_postcode is None:
        return None

    compact = "".join(raw_postcode.strip().upper().split())
    if not compact:
        return None
    if len(compact) <= 3:
        return compact
    return f"{compact[:-3]} {compact[-3:]}"


def validate_headers(headers: Sequence[str]) -> None:
    header_set = set(headers)
    missing = [header for header in REQUIRED_HEADERS if header not in header_set]
    if missing:
        missing_fields = ", ".join(missing)
        raise ValueError(f"GIAS schema mismatch; missing required headers: {missing_fields}")


def normalize_row(raw_row: Mapping[str, str]) -> tuple[NormalizedGiasRow | None, str | None]:
    urn = raw_row["URN"].strip()
    if not urn:
        return None, "missing_urn"

    easting_raw = raw_row["Easting"].strip()
    northing_raw = raw_row["Northing"].strip()
    if not easting_raw or not northing_raw:
        return None, "missing_coordinates"

    try:
        easting = float(easting_raw)
        northing = float(northing_raw)
    except ValueError:
        return None, "invalid_coordinates"

    if not is_coordinate_in_range(easting, northing):
        return None, "invalid_coordinate_range"

    try:
        open_date = parse_optional_date(raw_row["OpenDate"])
    except ValueError:
        return None, "invalid_open_date"

    try:
        close_date = parse_optional_date(raw_row["CloseDate"])
    except ValueError:
        return None, "invalid_close_date"

    try:
        pupil_count = parse_optional_integer(raw_row["NumberOfPupils"])
    except ValueError:
        return None, "invalid_pupil_count"

    try:
        capacity = parse_optional_integer(raw_row["SchoolCapacity"])
    except ValueError:
        return None, "invalid_capacity"

    return (
        NormalizedGiasRow(
            urn=urn,
            name=raw_row["EstablishmentName"].strip(),
            phase=strip_or_none(raw_row["PhaseOfEducation (name)"]),
            school_type=strip_or_none(raw_row["TypeOfEstablishment (name)"]),
            status=strip_or_none(raw_row["EstablishmentStatus (name)"]),
            postcode=normalize_postcode(raw_row["Postcode"]),
            easting=easting,
            northing=northing,
            open_date=open_date,
            close_date=close_date,
            pupil_count=pupil_count,
            capacity=capacity,
        ),
        None,
    )


def is_coordinate_in_range(easting: float, northing: float) -> bool:
    return (
        EASTING_RANGE[0] <= easting <= EASTING_RANGE[1]
        and NORTHING_RANGE[0] <= northing <= NORTHING_RANGE[1]
    )


def parse_optional_integer(raw_value: str | None) -> int | None:
    if raw_value is None:
        return None
    value = raw_value.strip()
    if not value or value.upper() in NUMERIC_SENTINELS:
        return None
    try:
        return int(float(value))
    except ValueError as exc:
        raise ValueError("invalid integer value") from exc


def parse_optional_date(raw_value: str | None) -> date | None:
    if raw_value is None:
        return None
    value = raw_value.strip()
    if not value:
        return None

    supported_formats = (
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y-%m-%d",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%d-%m-%Y %H:%M:%S",
        "%d-%m-%Y %H:%M",
    )
    for date_format in supported_formats:
        try:
            return datetime.strptime(value, date_format).date()
        except ValueError:
            continue
    raise ValueError(f"unsupported date value '{value}'")


def strip_or_none(raw_value: str | None) -> str | None:
    if raw_value is None:
        return None
    value = raw_value.strip()
    return value or None
