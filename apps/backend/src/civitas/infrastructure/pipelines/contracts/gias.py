from __future__ import annotations

from datetime import date, datetime
from typing import Mapping, Sequence, TypedDict
from urllib.parse import urlparse

CONTRACT_VERSION = "gias.v3"

REQUIRED_HEADERS: tuple[str, ...] = (
    "URN",
    "EstablishmentNumber",
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
    "SchoolWebsite",
    "TelephoneNum",
    "HeadTitle (name)",
    "HeadFirstName",
    "HeadLastName",
    "HeadPreferredJobTitle",
    "Street",
    "Locality",
    "Address3",
    "Town",
    "County (name)",
    "StatutoryLowAge",
    "StatutoryHighAge",
    "Gender (name)",
    "ReligiousCharacter (name)",
    "Diocese (name)",
    "AdmissionsPolicy (name)",
    "OfficialSixthForm (name)",
    "NurseryProvision (name)",
    "Boarders (name)",
    "PercentageFSM",
    "Trusts (name)",
    "TrustSchoolFlag (name)",
    "Federations (name)",
    "FederationFlag (name)",
    "LA (name)",
    "LA (code)",
    "UrbanRural (name)",
    "NumberOfBoys",
    "NumberOfGirls",
    "LSOA (code)",
    "LSOA (name)",
    "LastChangedDate",
)

NUMERIC_SENTINELS: set[str] = {"", "SUPP", "NE", "N/A", "NA", "X"}
EASTING_RANGE = (0.0, 700000.0)
NORTHING_RANGE = (0.0, 1300000.0)
AGE_RANGE = (0, 25)
PERCENTAGE_RANGE = (0.0, 100.0)


class NormalizationWarning(TypedDict):
    field_name: str
    reason_code: str
    raw_value: str | None


class NormalizedGiasRow(TypedDict):
    urn: str
    establishment_number: str | None
    school_laestab: str | None
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
    website: str | None
    telephone: str | None
    head_title: str | None
    head_first_name: str | None
    head_last_name: str | None
    head_job_title: str | None
    address_street: str | None
    address_locality: str | None
    address_line3: str | None
    address_town: str | None
    address_county: str | None
    statutory_low_age: int | None
    statutory_high_age: int | None
    gender: str | None
    religious_character: str | None
    diocese: str | None
    admissions_policy: str | None
    sixth_form: str | None
    nursery_provision: str | None
    boarders: str | None
    fsm_pct_gias: float | None
    trust_name: str | None
    trust_flag: str | None
    federation_name: str | None
    federation_flag: str | None
    la_name: str | None
    la_code: str | None
    urban_rural: str | None
    number_of_boys: int | None
    number_of_girls: int | None
    lsoa_code: str | None
    lsoa_name: str | None
    last_changed_date: date | None


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


def normalize_row(
    raw_row: Mapping[str, str],
) -> tuple[NormalizedGiasRow | None, str | None, tuple[NormalizationWarning, ...]]:
    urn = raw_row["URN"].strip()
    if not urn:
        return None, "missing_urn", ()

    easting_raw = raw_row["Easting"].strip()
    northing_raw = raw_row["Northing"].strip()
    if not easting_raw or not northing_raw:
        return None, "missing_coordinates", ()

    try:
        easting = float(easting_raw)
        northing = float(northing_raw)
    except ValueError:
        return None, "invalid_coordinates", ()

    if not is_coordinate_in_range(easting, northing):
        return None, "invalid_coordinate_range", ()

    try:
        open_date = parse_optional_date(raw_row["OpenDate"])
    except ValueError:
        return None, "invalid_open_date", ()

    try:
        close_date = parse_optional_date(raw_row["CloseDate"])
    except ValueError:
        return None, "invalid_close_date", ()

    try:
        pupil_count = parse_optional_integer(raw_row["NumberOfPupils"])
    except ValueError:
        return None, "invalid_pupil_count", ()

    try:
        capacity = parse_optional_integer(raw_row["SchoolCapacity"])
    except ValueError:
        return None, "invalid_capacity", ()

    warnings: list[NormalizationWarning] = []

    website, warning = normalize_website(raw_row["SchoolWebsite"])
    if warning is not None:
        warnings.append(warning)

    telephone, warning = normalize_telephone(raw_row["TelephoneNum"])
    if warning is not None:
        warnings.append(warning)

    statutory_low_age, warning = parse_optional_integer_with_warning(
        raw_value=raw_row["StatutoryLowAge"],
        field_name="StatutoryLowAge",
        min_value=AGE_RANGE[0],
        max_value=AGE_RANGE[1],
        range_reason_code="age_out_of_range",
    )
    if warning is not None:
        warnings.append(warning)

    statutory_high_age, warning = parse_optional_integer_with_warning(
        raw_value=raw_row["StatutoryHighAge"],
        field_name="StatutoryHighAge",
        min_value=AGE_RANGE[0],
        max_value=AGE_RANGE[1],
        range_reason_code="age_out_of_range",
    )
    if warning is not None:
        warnings.append(warning)

    fsm_pct_gias, warning = parse_optional_float_with_warning(
        raw_value=raw_row["PercentageFSM"],
        field_name="PercentageFSM",
        min_value=PERCENTAGE_RANGE[0],
        max_value=PERCENTAGE_RANGE[1],
        range_reason_code="percentage_out_of_range",
    )
    if warning is not None:
        warnings.append(warning)

    number_of_boys, warning = parse_optional_integer_with_warning(
        raw_value=raw_row["NumberOfBoys"],
        field_name="NumberOfBoys",
    )
    if warning is not None:
        warnings.append(warning)

    number_of_girls, warning = parse_optional_integer_with_warning(
        raw_value=raw_row["NumberOfGirls"],
        field_name="NumberOfGirls",
    )
    if warning is not None:
        warnings.append(warning)

    last_changed_date, warning = parse_optional_date_with_warning(
        raw_value=raw_row["LastChangedDate"],
        field_name="LastChangedDate",
    )
    if warning is not None:
        warnings.append(warning)

    return (
        NormalizedGiasRow(
            urn=urn,
            establishment_number=strip_or_none(raw_row["EstablishmentNumber"]),
            school_laestab=build_school_laestab(
                la_code=raw_row["LA (code)"],
                establishment_number=raw_row["EstablishmentNumber"],
            ),
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
            website=website,
            telephone=telephone,
            head_title=strip_or_none(raw_row["HeadTitle (name)"]),
            head_first_name=strip_or_none(raw_row["HeadFirstName"]),
            head_last_name=strip_or_none(raw_row["HeadLastName"]),
            head_job_title=strip_or_none(raw_row["HeadPreferredJobTitle"]),
            address_street=strip_or_none(raw_row["Street"]),
            address_locality=strip_or_none(raw_row["Locality"]),
            address_line3=strip_or_none(raw_row["Address3"]),
            address_town=strip_or_none(raw_row["Town"]),
            address_county=strip_or_none(raw_row["County (name)"]),
            statutory_low_age=statutory_low_age,
            statutory_high_age=statutory_high_age,
            gender=strip_or_none(raw_row["Gender (name)"]),
            religious_character=strip_or_none(raw_row["ReligiousCharacter (name)"]),
            diocese=strip_or_none(raw_row["Diocese (name)"]),
            admissions_policy=strip_or_none(raw_row["AdmissionsPolicy (name)"]),
            sixth_form=strip_or_none(raw_row["OfficialSixthForm (name)"]),
            nursery_provision=strip_or_none(raw_row["NurseryProvision (name)"]),
            boarders=strip_or_none(raw_row["Boarders (name)"]),
            fsm_pct_gias=fsm_pct_gias,
            trust_name=strip_or_none(raw_row["Trusts (name)"]),
            trust_flag=strip_or_none(raw_row["TrustSchoolFlag (name)"]),
            federation_name=strip_or_none(raw_row["Federations (name)"]),
            federation_flag=strip_or_none(raw_row["FederationFlag (name)"]),
            la_name=strip_or_none(raw_row["LA (name)"]),
            la_code=strip_or_none(raw_row["LA (code)"]),
            urban_rural=strip_or_none(raw_row["UrbanRural (name)"]),
            number_of_boys=number_of_boys,
            number_of_girls=number_of_girls,
            lsoa_code=strip_or_none(raw_row["LSOA (code)"]),
            lsoa_name=strip_or_none(raw_row["LSOA (name)"]),
            last_changed_date=last_changed_date,
        ),
        None,
        tuple(warnings),
    )


def build_school_laestab(*, la_code: str | None, establishment_number: str | None) -> str | None:
    normalized_la_code = strip_or_none(la_code)
    normalized_establishment_number = strip_or_none(establishment_number)
    if (
        normalized_la_code is None
        or normalized_establishment_number is None
        or not normalized_la_code.isdigit()
        or not normalized_establishment_number.isdigit()
    ):
        return None
    return f"{normalized_la_code}{normalized_establishment_number.zfill(4)}"


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


def normalize_website(
    raw_value: str | None,
) -> tuple[str | None, NormalizationWarning | None]:
    value = strip_or_none(raw_value)
    if value is None:
        return None, None

    candidate = value if "://" in value else f"https://{value}"
    parsed = urlparse(candidate)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or " " in parsed.netloc:
        return None, build_warning(
            field_name="SchoolWebsite",
            reason_code="invalid_website",
            raw_value=raw_value,
        )
    return parsed.geturl(), None


def normalize_telephone(
    raw_value: str | None,
) -> tuple[str | None, NormalizationWarning | None]:
    value = strip_or_none(raw_value)
    if value is None:
        return None, None

    digits = "".join(character for character in value if character.isdigit())
    normalized = f"+{digits}" if value.startswith("+") and digits else digits
    if not normalized:
        return None, build_warning(
            field_name="TelephoneNum",
            reason_code="invalid_telephone",
            raw_value=raw_value,
        )
    return normalized, None


def parse_optional_integer_with_warning(
    *,
    raw_value: str | None,
    field_name: str,
    min_value: int | None = None,
    max_value: int | None = None,
    range_reason_code: str = "integer_out_of_range",
) -> tuple[int | None, NormalizationWarning | None]:
    try:
        value = parse_optional_integer(raw_value)
    except ValueError:
        return None, build_warning(
            field_name=field_name,
            reason_code="invalid_integer",
            raw_value=raw_value,
        )

    if value is None:
        return None, None
    if min_value is not None and value < min_value:
        return None, build_warning(
            field_name=field_name,
            reason_code=range_reason_code,
            raw_value=raw_value,
        )
    if max_value is not None and value > max_value:
        return None, build_warning(
            field_name=field_name,
            reason_code=range_reason_code,
            raw_value=raw_value,
        )
    return value, None


def parse_optional_float_with_warning(
    *,
    raw_value: str | None,
    field_name: str,
    min_value: float | None = None,
    max_value: float | None = None,
    range_reason_code: str = "float_out_of_range",
) -> tuple[float | None, NormalizationWarning | None]:
    value = strip_or_none(raw_value)
    if value is None or value.upper() in NUMERIC_SENTINELS:
        return None, None

    try:
        parsed = float(value)
    except ValueError:
        return None, build_warning(
            field_name=field_name,
            reason_code="invalid_float",
            raw_value=raw_value,
        )

    if min_value is not None and parsed < min_value:
        return None, build_warning(
            field_name=field_name,
            reason_code=range_reason_code,
            raw_value=raw_value,
        )
    if max_value is not None and parsed > max_value:
        return None, build_warning(
            field_name=field_name,
            reason_code=range_reason_code,
            raw_value=raw_value,
        )
    return parsed, None


def parse_optional_date_with_warning(
    *,
    raw_value: str | None,
    field_name: str,
) -> tuple[date | None, NormalizationWarning | None]:
    try:
        return parse_optional_date(raw_value), None
    except ValueError:
        return None, build_warning(
            field_name=field_name,
            reason_code="invalid_date",
            raw_value=raw_value,
        )


def build_warning(
    *,
    field_name: str,
    reason_code: str,
    raw_value: str | None,
) -> NormalizationWarning:
    return NormalizationWarning(
        field_name=field_name,
        reason_code=reason_code,
        raw_value=raw_value,
    )
