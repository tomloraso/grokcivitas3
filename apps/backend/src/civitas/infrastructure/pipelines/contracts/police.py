from __future__ import annotations

import math
from datetime import date
from typing import Mapping, Sequence, TypedDict

CONTRACT_VERSION = "police_crime_context.v1"

REQUIRED_HEADERS: tuple[str, ...] = (
    "Crime type",
    "Longitude",
    "Latitude",
    "Month",
)


class NormalizedPoliceRow(TypedDict):
    month: date
    crime_category: str
    longitude: float
    latitude: float


def validate_headers(headers: Sequence[str]) -> None:
    header_set = set(headers)
    missing = [header for header in REQUIRED_HEADERS if header not in header_set]
    if missing:
        missing_fields = ", ".join(missing)
        raise ValueError(
            f"Police crime schema mismatch; missing required headers: {missing_fields}"
        )


def normalize_row(
    raw_row: Mapping[str, str],
) -> tuple[NormalizedPoliceRow | None, str | None]:
    raw_month = raw_row.get("Month")
    month = parse_month(raw_month)
    if month is None:
        return None, "invalid_month"

    crime_category = strip_or_none(raw_row.get("Crime type"))
    if crime_category is None:
        return None, "missing_crime_type"

    longitude_value = raw_row.get("Longitude")
    if strip_or_none(longitude_value) is None:
        return None, "missing_longitude"
    longitude = parse_coordinate(longitude_value, axis="longitude")
    if longitude is None:
        return None, "invalid_longitude"

    latitude_value = raw_row.get("Latitude")
    if strip_or_none(latitude_value) is None:
        return None, "missing_latitude"
    latitude = parse_coordinate(latitude_value, axis="latitude")
    if latitude is None:
        return None, "invalid_latitude"

    return (
        NormalizedPoliceRow(
            month=month,
            crime_category=crime_category,
            longitude=longitude,
            latitude=latitude,
        ),
        None,
    )


def parse_month(raw_value: str | None) -> date | None:
    value = (raw_value or "").strip()
    if len(value) != 7 or value[4] != "-" or not value[:4].isdigit() or not value[5:].isdigit():
        return None
    year = int(value[:4])
    month = int(value[5:])
    if month < 1 or month > 12:
        return None
    return date(year, month, 1)


def parse_coordinate(raw_value: str | None, *, axis: str) -> float | None:
    value = (raw_value or "").strip()
    if not value:
        return None
    try:
        parsed = float(value)
    except ValueError:
        return None
    if not math.isfinite(parsed):
        return None
    if axis == "longitude" and not (-180.0 <= parsed <= 180.0):
        return None
    if axis == "latitude" and not (-90.0 <= parsed <= 90.0):
        return None
    return parsed


def strip_or_none(raw_value: str | None) -> str | None:
    value = (raw_value or "").strip()
    return value or None
