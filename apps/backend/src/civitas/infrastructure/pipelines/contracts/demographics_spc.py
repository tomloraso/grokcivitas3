from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Mapping, Sequence, TypedDict

CONTRACT_VERSION = "demographics_spc.v2"

_REQUIRED_FIELDS: dict[str, tuple[str, ...]] = {
    "urn": ("urn", "URN"),
    "fsm_pct": ("% of pupils known to be eligible for free school meals",),
    "disadvantaged_pct": (
        "% of pupils known to be eligible for free school meals (Performance Tables)",
    ),
    "eal_pct": ("% of pupils whose first language is known or believed to be other than English",),
    "first_language_english_pct": (
        "% of pupils whose first language is known or believed to be English",
    ),
    "first_language_unclassified_pct": ("% of pupils whose first language is unclassified",),
}

_OPTIONAL_FIELDS: dict[str, tuple[str, ...]] = {
    "fsm6_pct": (
        "% of pupils known to be eligible for free school meals (Performance Tables)",
        "ptfsm6cla1a",
    ),
    "male_pct": (
        "% of pupils who are male",
        "% of pupils who are boys",
        "male pupils (%)",
        "pbelig",
    ),
    "female_pct": (
        "% of pupils who are female",
        "% of pupils who are girls",
        "female pupils (%)",
        "pgelig",
    ),
    "male_count": ("headcount total male",),
    "female_count": ("headcount total female",),
    "gender_total_pupils_count": (
        "Number of pupils (used for FSM calculation in Performance Tables)",
        "total pupils",
    ),
    "pupil_mobility_pct": (
        "% of pupils who are mobile",
        "% of mobile pupils",
        "ptmobn",
    ),
}


@dataclass(frozen=True)
class EthnicityGroupField:
    key: str
    label: str
    count_header: str
    pct_header: str


ETHNICITY_GROUP_FIELDS: tuple[EthnicityGroupField, ...] = (
    EthnicityGroupField(
        key="white_british",
        label="White British",
        count_header="number of pupils classified as white British ethnic origin",
        pct_header="% of pupils classified as white British ethnic origin",
    ),
    EthnicityGroupField(
        key="irish",
        label="Irish",
        count_header="number of pupils classified as Irish ethnic origin",
        pct_header="% of pupils classified as Irish ethnic origin",
    ),
    EthnicityGroupField(
        key="traveller_of_irish_heritage",
        label="Traveller of Irish heritage",
        count_header="number of pupils classified as traveller of Irish heritage ethnic origin",
        pct_header="% of pupils classified as traveller of Irish heritage ethnic origin",
    ),
    EthnicityGroupField(
        key="any_other_white_background",
        label="Any other white background",
        count_header="number of pupils classified as any other white background ethnic origin",
        pct_header="% of pupils classified as any other white background ethnic origin",
    ),
    EthnicityGroupField(
        key="gypsy_roma",
        label="Gypsy/Roma",
        count_header="number of pupils classified as Gypsy/Roma ethnic origin",
        pct_header="% of pupils classified as Gypsy/Roma ethnic origin",
    ),
    EthnicityGroupField(
        key="white_and_black_caribbean",
        label="White and Black Caribbean",
        count_header="number of pupils classified as white and black Caribbean ethnic origin",
        pct_header="% of pupils classified as white and black Caribbean ethnic origin",
    ),
    EthnicityGroupField(
        key="white_and_black_african",
        label="White and Black African",
        count_header="number of pupils classified as white and black African ethnic origin",
        pct_header="% of pupils classified as white and black African ethnic origin",
    ),
    EthnicityGroupField(
        key="white_and_asian",
        label="White and Asian",
        count_header="number of pupils classified as white and Asian ethnic origin",
        pct_header="% of pupils classified as white and Asian ethnic origin",
    ),
    EthnicityGroupField(
        key="any_other_mixed_background",
        label="Any other mixed background",
        count_header="number of pupils classified as any other mixed background ethnic origin",
        pct_header="% of pupils classified as any other mixed background ethnic origin",
    ),
    EthnicityGroupField(
        key="indian",
        label="Indian",
        count_header="number of pupils classified as Indian ethnic origin",
        pct_header="% of pupils classified as Indian ethnic origin",
    ),
    EthnicityGroupField(
        key="pakistani",
        label="Pakistani",
        count_header="number of pupils classified as Pakistani ethnic origin",
        pct_header="% of pupils classified as Pakistani ethnic origin",
    ),
    EthnicityGroupField(
        key="bangladeshi",
        label="Bangladeshi",
        count_header="number of pupils classified as Bangladeshi ethnic origin",
        pct_header="% of pupils classified as Bangladeshi ethnic origin",
    ),
    EthnicityGroupField(
        key="any_other_asian_background",
        label="Any other Asian background",
        count_header="number of pupils classified as any other Asian background ethnic origin",
        pct_header="% of pupils classified as any other Asian background ethnic origin",
    ),
    EthnicityGroupField(
        key="caribbean",
        label="Caribbean",
        count_header="number of pupils classified as Caribbean ethnic origin",
        pct_header="% of pupils classified as Caribbean ethnic origin",
    ),
    EthnicityGroupField(
        key="african",
        label="African",
        count_header="number of pupils classified as African ethnic origin",
        pct_header="% of pupils classified as African ethnic origin",
    ),
    EthnicityGroupField(
        key="any_other_black_background",
        label="Any other black background",
        count_header="number of pupils classified as any other black background ethnic origin",
        pct_header="% of pupils classified as any other black background ethnic origin",
    ),
    EthnicityGroupField(
        key="chinese",
        label="Chinese",
        count_header="number of pupils classified as Chinese ethnic origin",
        pct_header="% of pupils classified as Chinese ethnic origin",
    ),
    EthnicityGroupField(
        key="any_other_ethnic_group",
        label="Any other ethnic group",
        count_header="number of pupils classified as any other ethnic group ethnic origin",
        pct_header="% of pupils classified as any other ethnic group ethnic origin",
    ),
    EthnicityGroupField(
        key="unclassified",
        label="Unclassified",
        count_header="number of pupils unclassified",
        pct_header="% of pupils unclassified",
    ),
)

TIME_PERIOD_FIELDS: tuple[str, ...] = ("time_period", "Time period")
SENTINEL_TOKENS: set[str] = {"", "SUPP", "NE", "N/A", "NA", "X", "Z", "C"}
_RELEASE_SLUG_PATTERN = re.compile(r"^(?P<start>\d{4})-(?P<end>\d{2})$")
_LANGUAGE_COUNT_PATTERN = re.compile(r"^number of pupils whose first language is (?P<label>.+)$")
_LANGUAGE_PCT_PATTERN = re.compile(r"^% of pupils whose first language is (?P<label>.+)$")
_EXCLUDED_LANGUAGE_LABELS: set[str] = {
    "known or believed to be other than english",
    "known or believed to be english",
    "unclassified",
}


class NormalizedTopLanguage(TypedDict):
    key: str
    label: str
    count: int | None
    percentage: float | None


class NormalizedSpcRow(TypedDict):
    urn: str
    academic_year: str
    fsm_pct: float | None
    disadvantaged_pct: float | None
    eal_pct: float | None
    first_language_english_pct: float | None
    first_language_unclassified_pct: float | None
    fsm6_pct: float | None
    male_pct: float | None
    female_pct: float | None
    pupil_mobility_pct: float | None
    has_fsm6_data: bool
    has_gender_data: bool
    has_mobility_data: bool
    ethnicity_percentages: dict[str, float | None]
    ethnicity_counts: dict[str, int | None]
    has_ethnicity_data: bool
    top_home_languages: tuple[NormalizedTopLanguage, ...]
    has_top_languages_data: bool


def validate_headers(headers: Sequence[str]) -> dict[str, str]:
    normalized_headers = {_normalize_header(header): header for header in headers}

    resolved_fields: dict[str, str] = {}
    missing: list[str] = []

    for field_name, candidates in _REQUIRED_FIELDS.items():
        resolved = _resolve_candidate(candidates, normalized_headers)
        if resolved is None:
            missing.append(candidates[0])
            continue
        resolved_fields[field_name] = resolved

    for field_name, candidates in _OPTIONAL_FIELDS.items():
        resolved = _resolve_candidate(candidates, normalized_headers)
        if resolved is not None:
            resolved_fields[field_name] = resolved

    for group in ETHNICITY_GROUP_FIELDS:
        resolved_count = _resolve_candidate((group.count_header,), normalized_headers)
        if resolved_count is None:
            missing.append(group.count_header)
        else:
            resolved_fields[f"ethnicity_{group.key}_count"] = resolved_count

        resolved_pct = _resolve_candidate((group.pct_header,), normalized_headers)
        if resolved_pct is None:
            missing.append(group.pct_header)
        else:
            resolved_fields[f"ethnicity_{group.key}_pct"] = resolved_pct

    if missing:
        raise ValueError("SPC schema mismatch; missing required headers: " + ", ".join(missing))

    time_period_column = _resolve_candidate(TIME_PERIOD_FIELDS, normalized_headers)
    if time_period_column is not None:
        resolved_fields["time_period"] = time_period_column

    return resolved_fields


def normalize_row(
    raw_row: Mapping[str, str],
    *,
    column_map: Mapping[str, str],
    release_slug: str,
) -> tuple[NormalizedSpcRow | None, str | None]:
    urn_column = column_map["urn"]
    urn = (raw_row.get(urn_column) or "").strip()
    if not urn:
        return None, "missing_urn"

    try:
        academic_year = _resolve_academic_year(
            raw_row=raw_row, column_map=column_map, release_slug=release_slug
        )
    except ValueError:
        return None, "invalid_academic_year"

    try:
        fsm_pct = _parse_optional_percentage(raw_row.get(column_map["fsm_pct"]))
    except ValueError:
        return None, "invalid_fsm_pct"

    try:
        disadvantaged_pct = _parse_optional_percentage(raw_row.get(column_map["disadvantaged_pct"]))
    except ValueError:
        return None, "invalid_disadvantaged_pct"

    try:
        eal_pct = _parse_optional_percentage(raw_row.get(column_map["eal_pct"]))
    except ValueError:
        return None, "invalid_eal_pct"

    try:
        first_language_english_pct = _parse_optional_percentage(
            raw_row.get(column_map["first_language_english_pct"])
        )
    except ValueError:
        return None, "invalid_first_language_english_pct"

    try:
        first_language_unclassified_pct = _parse_optional_percentage(
            raw_row.get(column_map["first_language_unclassified_pct"])
        )
    except ValueError:
        return None, "invalid_first_language_unclassified_pct"

    fsm6_column = column_map.get("fsm6_pct", column_map["disadvantaged_pct"])
    has_fsm6_data = fsm6_column in column_map.values()
    try:
        fsm6_pct = _parse_optional_percentage(raw_row.get(fsm6_column))
    except ValueError:
        return None, "invalid_fsm6_pct"

    male_column = column_map.get("male_pct")
    female_column = column_map.get("female_pct")
    male_count_column = column_map.get("male_count")
    female_count_column = column_map.get("female_count")
    gender_total_pupils_count_column = column_map.get("gender_total_pupils_count")
    has_gender_data = (
        male_column is not None
        or female_column is not None
        or (
            gender_total_pupils_count_column is not None
            and (male_count_column is not None or female_count_column is not None)
        )
    )
    try:
        male_pct = _parse_optional_percentage(raw_row.get(male_column)) if male_column else None
    except ValueError:
        return None, "invalid_male_pct"
    try:
        female_pct = (
            _parse_optional_percentage(raw_row.get(female_column)) if female_column else None
        )
    except ValueError:
        return None, "invalid_female_pct"

    if (
        (male_pct is None or female_pct is None)
        and gender_total_pupils_count_column is not None
        and (male_count_column is not None or female_count_column is not None)
    ):
        try:
            gender_total_pupils = _parse_optional_count(
                raw_row.get(gender_total_pupils_count_column)
            )
        except ValueError:
            return None, "invalid_gender_total_pupils_count"

        if gender_total_pupils is not None and gender_total_pupils > 0:
            if male_pct is None and male_count_column is not None:
                try:
                    male_count = _parse_optional_count(raw_row.get(male_count_column))
                except ValueError:
                    return None, "invalid_male_count"
                male_pct = _derive_percentage_from_counts(
                    count=male_count,
                    total=gender_total_pupils,
                )

            if female_pct is None and female_count_column is not None:
                try:
                    female_count = _parse_optional_count(raw_row.get(female_count_column))
                except ValueError:
                    return None, "invalid_female_count"
                female_pct = _derive_percentage_from_counts(
                    count=female_count,
                    total=gender_total_pupils,
                )

    mobility_column = column_map.get("pupil_mobility_pct")
    has_mobility_data = mobility_column is not None
    try:
        pupil_mobility_pct = (
            _parse_optional_percentage(raw_row.get(mobility_column)) if mobility_column else None
        )
    except ValueError:
        return None, "invalid_pupil_mobility_pct"

    ethnicity_percentages: dict[str, float | None] = {}
    ethnicity_counts: dict[str, int | None] = {}

    for group in ETHNICITY_GROUP_FIELDS:
        try:
            ethnicity_counts[group.key] = _parse_optional_count(
                raw_row.get(column_map[f"ethnicity_{group.key}_count"])
            )
        except ValueError:
            return None, f"invalid_ethnicity_{group.key}_count"

        try:
            ethnicity_percentages[group.key] = _parse_optional_percentage(
                raw_row.get(column_map[f"ethnicity_{group.key}_pct"])
            )
        except ValueError:
            return None, f"invalid_ethnicity_{group.key}_pct"

    has_ethnicity_data = any(
        value is not None for value in (*ethnicity_percentages.values(), *ethnicity_counts.values())
    )
    top_home_languages = _extract_top_home_languages(raw_row)
    has_top_languages_data = len(top_home_languages) > 0

    return (
        NormalizedSpcRow(
            urn=urn,
            academic_year=academic_year,
            fsm_pct=fsm_pct,
            disadvantaged_pct=disadvantaged_pct,
            eal_pct=eal_pct,
            first_language_english_pct=first_language_english_pct,
            first_language_unclassified_pct=first_language_unclassified_pct,
            fsm6_pct=fsm6_pct,
            male_pct=male_pct,
            female_pct=female_pct,
            pupil_mobility_pct=pupil_mobility_pct,
            has_fsm6_data=has_fsm6_data,
            has_gender_data=has_gender_data,
            has_mobility_data=has_mobility_data,
            ethnicity_percentages=ethnicity_percentages,
            ethnicity_counts=ethnicity_counts,
            has_ethnicity_data=has_ethnicity_data,
            top_home_languages=top_home_languages,
            has_top_languages_data=has_top_languages_data,
        ),
        None,
    )


def normalize_academic_year(raw_value: str | None) -> str:
    value = (raw_value or "").strip()

    if len(value) == 7 and value[4] == "/" and value[:4].isdigit() and value[5:].isdigit():
        return value

    if len(value) == 6 and value.isdigit():
        return f"{value[:4]}/{value[4:]}"

    raise ValueError("invalid academic year")


def parse_release_slug_academic_year(release_slug: str) -> str:
    match = _RELEASE_SLUG_PATTERN.match(release_slug.strip())
    if match is None:
        raise ValueError("invalid release slug")

    start_year = int(match.group("start"))
    end_suffix = int(match.group("end"))
    if start_year % 100 != ((end_suffix - 1) % 100):
        raise ValueError("invalid release slug")

    return f"{start_year:04d}/{end_suffix:02d}"


def _resolve_academic_year(
    *,
    raw_row: Mapping[str, str],
    column_map: Mapping[str, str],
    release_slug: str,
) -> str:
    time_period_column = column_map.get("time_period")
    if time_period_column is not None:
        raw_time_period = raw_row.get(time_period_column)
        if raw_time_period is not None and raw_time_period.strip():
            return normalize_academic_year(raw_time_period)
    return parse_release_slug_academic_year(release_slug)


def _parse_optional_percentage(raw_value: str | None) -> float | None:
    if raw_value is None:
        return None
    value = raw_value.strip()
    if not value:
        return None
    if value.upper() in SENTINEL_TOKENS:
        return None

    try:
        parsed = float(value)
    except ValueError as exc:
        raise ValueError("invalid numeric value") from exc

    if not math.isfinite(parsed):
        raise ValueError("numeric value must be finite")
    if parsed < 0.0 or parsed > 100.0:
        raise ValueError("percentage out of range")

    return parsed


def _parse_optional_count(raw_value: str | None) -> int | None:
    if raw_value is None:
        return None
    value = raw_value.strip()
    if not value:
        return None
    if value.upper() in SENTINEL_TOKENS:
        return None

    try:
        parsed = float(value)
    except ValueError as exc:
        raise ValueError("invalid numeric value") from exc

    if not math.isfinite(parsed):
        raise ValueError("numeric value must be finite")
    if parsed < 0:
        raise ValueError("count out of range")
    if not parsed.is_integer():
        raise ValueError("count must be an integer")

    return int(parsed)


def _derive_percentage_from_counts(*, count: int | None, total: int) -> float | None:
    if count is None or total <= 0:
        return None
    return (count / total) * 100.0


def _resolve_candidate(
    candidates: Sequence[str],
    normalized_headers: Mapping[str, str],
) -> str | None:
    for candidate in candidates:
        resolved = normalized_headers.get(_normalize_header(candidate))
        if resolved is not None:
            return resolved
    return None


def _normalize_header(value: str) -> str:
    return value.lstrip("\ufeff").strip().casefold()


def _extract_top_home_languages(raw_row: Mapping[str, str]) -> tuple[NormalizedTopLanguage, ...]:
    by_key: dict[str, NormalizedTopLanguage] = {}

    for header, raw_value in raw_row.items():
        normalized_header = _normalize_header(header)

        count_match = _LANGUAGE_COUNT_PATTERN.match(normalized_header)
        if count_match is not None:
            normalized_label = _normalize_language_label(count_match.group("label"))
            if normalized_label is None:
                continue
            key = _language_key(normalized_label)
            entry = by_key.setdefault(
                key,
                NormalizedTopLanguage(
                    key=key,
                    label=_display_language_label(normalized_label),
                    count=None,
                    percentage=None,
                ),
            )
            try:
                entry["count"] = _parse_optional_count(raw_value)
            except ValueError:
                entry["count"] = None
            continue

        pct_match = _LANGUAGE_PCT_PATTERN.match(normalized_header)
        if pct_match is None:
            continue

        normalized_label = _normalize_language_label(pct_match.group("label"))
        if normalized_label is None:
            continue
        key = _language_key(normalized_label)
        entry = by_key.setdefault(
            key,
            NormalizedTopLanguage(
                key=key,
                label=_display_language_label(normalized_label),
                count=None,
                percentage=None,
            ),
        )
        try:
            entry["percentage"] = _parse_optional_percentage(raw_value)
        except ValueError:
            entry["percentage"] = None

    published_languages = [
        language
        for language in by_key.values()
        if language["count"] is not None or language["percentage"] is not None
    ]
    ranked = sorted(
        published_languages,
        key=lambda item: (
            item["count"] is None,
            -(item["count"] or 0),
            item["percentage"] is None,
            -(item["percentage"] or 0.0),
            item["label"],
        ),
    )

    return tuple(ranked[:5])


def _normalize_language_label(raw_value: str) -> str | None:
    value = raw_value.strip().casefold()
    if not value:
        return None
    if value in _EXCLUDED_LANGUAGE_LABELS:
        return None
    return value


def _display_language_label(normalized_label: str) -> str:
    return " ".join(segment.capitalize() for segment in normalized_label.split())


def _language_key(normalized_label: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", normalized_label).strip("_")
