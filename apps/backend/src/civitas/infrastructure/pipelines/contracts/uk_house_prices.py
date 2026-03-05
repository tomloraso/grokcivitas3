from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from datetime import date, datetime
from typing import TypedDict

CONTRACT_VERSION = "uk_house_prices.v1"

DATE_HEADER = "Date"
AREA_NAME_HEADER = "Region_Name"
AREA_CODE_HEADER = "Area_Code"
AVERAGE_PRICE_HEADER = "Average_Price"
MONTHLY_CHANGE_HEADER = "Monthly_Change"
ANNUAL_CHANGE_HEADER = "Annual_Change"

NULL_TOKENS = {"", "na", "n/a", "null", ".", "-"}


class NormalizedUkHousePriceRow(TypedDict):
    month: date
    area_name: str
    area_code: str
    average_price: float
    monthly_change_pct: float | None
    annual_change_pct: float | None


def validate_headers(headers: Sequence[str]) -> None:
    required_headers = (
        DATE_HEADER,
        AREA_NAME_HEADER,
        AREA_CODE_HEADER,
        AVERAGE_PRICE_HEADER,
        MONTHLY_CHANGE_HEADER,
        ANNUAL_CHANGE_HEADER,
    )
    header_set = set(headers)
    missing = [header for header in required_headers if header not in header_set]
    if missing:
        raise ValueError(
            "UK house-price schema mismatch; missing required headers: " + ", ".join(missing)
        )


def normalize_row(
    raw_row: Mapping[str, str],
) -> tuple[NormalizedUkHousePriceRow | None, str | None]:
    area_code = _strip_or_none(raw_row.get(AREA_CODE_HEADER))
    if area_code is None:
        return None, "missing_area_code"

    area_name = _strip_or_none(raw_row.get(AREA_NAME_HEADER))
    if area_name is None:
        return None, "missing_area_name"

    try:
        month = _parse_date(raw_row.get(DATE_HEADER))
    except ValueError:
        return None, "invalid_month"

    try:
        average_price = _parse_required_float(raw_row.get(AVERAGE_PRICE_HEADER), min_value=0.0)
    except ValueError:
        return None, "invalid_average_price"

    try:
        monthly_change_pct = _parse_optional_float(raw_row.get(MONTHLY_CHANGE_HEADER))
    except ValueError:
        return None, "invalid_monthly_change_pct"

    try:
        annual_change_pct = _parse_optional_float(raw_row.get(ANNUAL_CHANGE_HEADER))
    except ValueError:
        return None, "invalid_annual_change_pct"

    return (
        NormalizedUkHousePriceRow(
            month=month,
            area_name=area_name,
            area_code=area_code,
            average_price=average_price,
            monthly_change_pct=monthly_change_pct,
            annual_change_pct=annual_change_pct,
        ),
        None,
    )


def _strip_or_none(raw_value: str | None) -> str | None:
    value = (raw_value or "").strip()
    return value or None


def _parse_date(raw_value: str | None) -> date:
    value = (raw_value or "").strip()
    if not value:
        raise ValueError("missing date")
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError("invalid date") from exc


def _parse_required_float(raw_value: str | None, *, min_value: float | None = None) -> float:
    value = (raw_value or "").strip()
    if not value:
        raise ValueError("missing float")
    try:
        parsed = float(value.replace(",", ""))
    except ValueError as exc:
        raise ValueError("invalid float") from exc
    if not math.isfinite(parsed):
        raise ValueError("non-finite float")
    if min_value is not None and parsed < min_value:
        raise ValueError("value below minimum")
    return parsed


def _parse_optional_float(raw_value: str | None) -> float | None:
    value = (raw_value or "").strip()
    if value.casefold() in NULL_TOKENS:
        return None
    return _parse_required_float(value)
