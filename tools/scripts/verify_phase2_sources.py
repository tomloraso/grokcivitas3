"""Verify Phase 2 external source contracts.

Run from repo root:
  uv run --project apps/backend python tools/scripts/verify_phase2_sources.py
"""

from __future__ import annotations

import csv
import gzip
import io
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

OFSTED_LANDING_PAGE_URL = (
    "https://www.gov.uk/government/statistical-data-sets/"
    "monthly-management-information-ofsteds-school-inspections-outcomes"
)

IMD_2025_LANDING_PAGE_URL = "https://www.gov.uk/government/statistics/english-indices-of-deprivation-2025"
IMD_2025_FILE_7_URL = (
    "https://assets.publishing.service.gov.uk/media/691ded56d140bbbaa59a2a7d/"
    "File_7_IoD2025_All_Ranks_Scores_Deciles_Population_Denominators.csv"
)
IMD_2019_LANDING_PAGE_URL = "https://www.gov.uk/government/statistics/english-indices-of-deprivation-2019"
IMD_2019_FILE_7_URL = (
    "https://assets.publishing.service.gov.uk/media/5dc407b440f0b6379a7acc8d/"
    "File_7_-_All_IoD2019_Scores__Ranks__Deciles_and_Population_Denominators_3.csv"
)

POLICE_ARCHIVE_INDEX_URL = "https://data.police.uk/data/archive/"
POLICE_COLUMNS_REFERENCE_URL = "https://data.police.uk/about/#columns"
POLICE_LAST_UPDATED_URL = "https://data.police.uk/api/crime-last-updated"
POLICE_STREET_DATES_URL = "https://data.police.uk/api/crimes-street-dates"
POLICE_CRIME_CATEGORIES_URL_TEMPLATE = "https://data.police.uk/api/crime-categories?date={month}"
POLICE_ALL_CRIME_URL_TEMPLATE = (
    "https://data.police.uk/api/crimes-street/all-crime?lat={lat}&lng={lng}&date={month}"
)
POLICE_API_LIMITS_URL = "https://data.police.uk/docs/api-call-limits/"

POSTCODES_IO_URL_TEMPLATE = "https://api.postcodes.io/postcodes/{postcode}"

DEFAULT_POLICE_SAMPLE_LAT = "51.5072"
DEFAULT_POLICE_SAMPLE_LNG = "-0.1276"
DEFAULT_POSTCODE_SAMPLE = "SW1A2AA"

REQUIRED_OFSTED_ALL_INSPECTIONS_HEADERS = [
    "URN",
    "Inspection number",
    "Inspection type",
    "Inspection start date",
    "Publication date",
]

REQUIRED_OFSTED_LATEST_HEADERS = [
    "URN",
    "Inspection start date",
    "Publication date",
    "Latest OEIF overall effectiveness",
    "Inspection start date of latest OEIF graded inspection",
    "Publication date of latest OEIF graded inspection",
    "Latest OEIF quality of education",
    "Latest OEIF behaviour and attitudes",
    "Latest OEIF personal development",
    "Latest OEIF effectiveness of leadership and management",
    "Date of latest ungraded inspection",
    "Ungraded inspection publication date",
    "Ungraded inspection overall outcome",
]

REQUIRED_OFSTED_HISTORICAL_HEADERS = [
    "Academic year",
    "URN",
    "Inspection number",
    "Inspection start date",
    "Publication date",
    "Overall effectiveness",
]

REQUIRED_IMD_2025_HEADERS = [
    "LSOA code (2021)",
    "LSOA name (2021)",
    "Index of Multiple Deprivation (IMD) Decile (where 1 is most deprived 10% of LSOAs)",
    "Income Deprivation Affecting Children Index (IDACI) Score (rate)",
    "Income Deprivation Affecting Children Index (IDACI) Decile (where 1 is most deprived 10% of LSOAs)",
]

REQUIRED_IMD_2019_HEADERS = [
    "LSOA code (2011)",
    "Index of Multiple Deprivation (IMD) Decile (where 1 is most deprived 10% of LSOAs)",
    "Income Deprivation Affecting Children Index (IDACI) Score (rate)",
    "Income Deprivation Affecting Children Index (IDACI) Decile (where 1 is most deprived 10% of LSOAs)",
]

REQUIRED_POLICE_COLUMNS_TEXT = ["Longitude", "Latitude", "LSOA code", "Crime type"]
REQUIRED_POLICE_CRIME_KEYS = ["category", "location", "month"]
REQUIRED_POSTCODE_FIELDS = [
    ("result", "codes", "lsoa"),
    ("result", "lsoa"),
    ("result", "latitude"),
    ("result", "longitude"),
]

_OFSTED_ASSET_URL_PATTERN = re.compile(
    r"https://assets\.publishing\.service\.gov\.uk/[^\"'<> ]+\.csv",
    flags=re.IGNORECASE,
)
_POLICE_ARCHIVE_PATTERN = re.compile(
    r"(?:https://data\.police\.uk)?/data/archive/(?P<month>\d{4}-\d{2})\.zip",
    flags=re.IGNORECASE,
)
_OFSTED_DATE_SUFFIX_PATTERN = re.compile(r"_(?P<date>\d{1,2}_[A-Za-z]{3}_\d{4})\.csv$", flags=re.IGNORECASE)


@dataclass(frozen=True)
class HttpResponse:
    status_code: int
    body: str


@dataclass(frozen=True)
class VerificationOutcome:
    ok: bool
    issues: list[str]


def _decode_response_bytes(raw_bytes: bytes, content_encoding: str | None) -> str:
    encoding_value = (content_encoding or "").casefold()
    should_try_gzip = "gzip" in encoding_value or raw_bytes.startswith(b"\x1f\x8b")
    if should_try_gzip:
        try:
            raw_bytes = gzip.decompress(raw_bytes)
        except OSError:
            pass
    return raw_bytes.decode("utf-8-sig", errors="replace")


def fetch_url(
    url: str,
    *,
    timeout_seconds: float = 20.0,
    max_bytes: int | None = None,
) -> HttpResponse:
    request = Request(url=url, headers={"User-Agent": "civitas-phase2-source-verifier/1.0"})
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            status_code = int(response.getcode())
            raw_bytes = response.read() if max_bytes is None else response.read(max_bytes)
            body = _decode_response_bytes(raw_bytes, response.headers.get("Content-Encoding"))
            return HttpResponse(status_code=status_code, body=body)
    except HTTPError as exc:
        body = exc.read().decode("utf-8-sig", errors="replace")
        return HttpResponse(status_code=int(exc.code), body=body)
    except URLError as exc:
        msg = f"Request failed for {url}: {exc.reason}"
        raise RuntimeError(msg) from exc


def parse_csv_headers(csv_text: str, *, skip_rows: int = 0) -> list[str]:
    try:
        reader = csv.reader(io.StringIO(csv_text, newline=""))
        header_row: list[str] | None = None
        for _ in range(skip_rows + 1):
            header_row = next(reader, None)
    except csv.Error as exc:
        raise ValueError(f"CSV response could not be parsed: {exc}") from exc
    if header_row is None:
        raise ValueError("CSV response was empty")

    cleaned_headers = [header.strip() for header in header_row]
    if cleaned_headers:
        cleaned_headers[0] = cleaned_headers[0].lstrip("\ufeff")
    return cleaned_headers


def _missing_headers(required: list[str], actual: list[str]) -> list[str]:
    actual_set = {header.strip() for header in actual}
    return [header for header in required if header not in actual_set]


def _select_latest_date_url(urls: list[str]) -> str | None:
    dated_candidates: list[tuple[datetime, str]] = []
    for url in urls:
        match = _OFSTED_DATE_SUFFIX_PATTERN.search(url)
        if match is None:
            continue
        try:
            date_value = datetime.strptime(match.group("date"), "%d_%b_%Y")
        except ValueError:
            continue
        dated_candidates.append((date_value, url))

    if not dated_candidates:
        return None

    dated_candidates.sort(key=lambda item: item[0], reverse=True)
    return dated_candidates[0][1]


def extract_ofsted_timeline_asset_urls(landing_html: str) -> tuple[str, str, str]:
    matches = _OFSTED_ASSET_URL_PATTERN.findall(landing_html)
    if not matches:
        raise ValueError("Unable to locate Ofsted CSV asset URLs on landing page")

    unique_urls: list[str] = []
    seen_urls: set[str] = set()
    for url in matches:
        if url in seen_urls:
            continue
        seen_urls.add(url)
        unique_urls.append(url)

    all_inspections_candidates = [url for url in unique_urls if "all_inspections" in url.casefold()]
    latest_inspections_candidates = [url for url in unique_urls if "latest_inspections" in url.casefold()]
    historical_candidates = [
        url
        for url in unique_urls
        if "1_september_2015_to_31_august_2019" in url.casefold()
    ]

    all_inspections_url = _select_latest_date_url(all_inspections_candidates) or (
        all_inspections_candidates[0] if all_inspections_candidates else None
    )
    latest_inspections_url = _select_latest_date_url(latest_inspections_candidates) or (
        latest_inspections_candidates[0] if latest_inspections_candidates else None
    )
    historical_url = historical_candidates[0] if historical_candidates else None

    if all_inspections_url is None:
        raise ValueError("Unable to locate Ofsted all_inspections CSV asset URL")
    if latest_inspections_url is None:
        raise ValueError("Unable to locate Ofsted latest_inspections CSV asset URL")
    if historical_url is None:
        raise ValueError("Unable to locate Ofsted 2015-2019 baseline CSV asset URL")

    return all_inspections_url, latest_inspections_url, historical_url


def extract_latest_police_archive_url(index_html: str, *, base_url: str = "https://data.police.uk") -> str:
    matches = list(_POLICE_ARCHIVE_PATTERN.finditer(index_html))
    if not matches:
        raise ValueError("Unable to locate Police archive monthly zip links")

    month_to_url: dict[str, str] = {}
    for match in matches:
        month = match.group("month")
        raw_url = match.group(0)
        absolute_url = raw_url if raw_url.startswith("http") else urljoin(base_url, raw_url)
        month_to_url[month] = absolute_url

    latest_month = max(month_to_url.keys())
    return month_to_url[latest_month]


def _json_loads_or_issue(payload: str, *, source_label: str, issues: list[str]) -> object | None:
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        issues.append(f"{source_label} response was not valid JSON")
        return None


def _assert_status_ok(
    *,
    response: HttpResponse,
    url: str,
    source_label: str,
    issues: list[str],
) -> bool:
    if response.status_code == 200:
        return True
    issues.append(f"{source_label} endpoint returned {response.status_code}: {url}")
    return False


def _get_nested(data: object, path: tuple[str, ...]) -> object | None:
    current: object = data
    for key in path:
        if not isinstance(current, dict):
            return None
        if key not in current:
            return None
        current = current[key]
    return current


def verify_phase2_sources(
    *,
    fetcher: Callable[[str], HttpResponse] = fetch_url,
    archive_fetcher: Callable[[str], HttpResponse] | None = None,
    ofsted_landing_url: str = OFSTED_LANDING_PAGE_URL,
    ofsted_asset_override_csv: str | None = None,
    imd_2025_landing_url: str = IMD_2025_LANDING_PAGE_URL,
    imd_2025_file_url: str = IMD_2025_FILE_7_URL,
    imd_2019_landing_url: str = IMD_2019_LANDING_PAGE_URL,
    imd_2019_file_url: str = IMD_2019_FILE_7_URL,
    police_archive_index_url: str = POLICE_ARCHIVE_INDEX_URL,
    police_archive_url_override: str | None = None,
    police_sample_lat: str = DEFAULT_POLICE_SAMPLE_LAT,
    police_sample_lng: str = DEFAULT_POLICE_SAMPLE_LNG,
    postcode_sample: str = DEFAULT_POSTCODE_SAMPLE,
) -> VerificationOutcome:
    issues: list[str] = []

    ofsted_landing_response = fetcher(ofsted_landing_url)
    all_inspections_url: str | None = None
    latest_inspections_url: str | None = None
    historical_url: str | None = None
    if _assert_status_ok(
        response=ofsted_landing_response,
        url=ofsted_landing_url,
        source_label="Ofsted landing page",
        issues=issues,
    ):
        if ofsted_asset_override_csv:
            try:
                all_inspections_url, latest_inspections_url, historical_url = extract_ofsted_timeline_asset_urls(
                    "\n".join(part.strip() for part in ofsted_asset_override_csv.split(",") if part.strip())
                )
            except ValueError as exc:
                issues.append(f"Ofsted asset override parse error: {exc}")
        else:
            try:
                all_inspections_url, latest_inspections_url, historical_url = extract_ofsted_timeline_asset_urls(
                    ofsted_landing_response.body
                )
            except ValueError as exc:
                issues.append(str(exc))

    if all_inspections_url is not None:
        response = fetcher(all_inspections_url)
        if _assert_status_ok(
            response=response,
            url=all_inspections_url,
            source_label="Ofsted all_inspections CSV",
            issues=issues,
        ):
            try:
                headers = parse_csv_headers(response.body)
                missing = _missing_headers(REQUIRED_OFSTED_ALL_INSPECTIONS_HEADERS, headers)
                if missing:
                    issues.append("Missing Ofsted all_inspections header(s): " + ", ".join(missing))
            except ValueError as exc:
                issues.append(f"Ofsted all_inspections CSV parse error: {exc}")

    if latest_inspections_url is not None:
        response = fetcher(latest_inspections_url)
        if _assert_status_ok(
            response=response,
            url=latest_inspections_url,
            source_label="Ofsted latest_inspections CSV",
            issues=issues,
        ):
            try:
                headers = parse_csv_headers(response.body)
                missing = _missing_headers(REQUIRED_OFSTED_LATEST_HEADERS, headers)
                if missing:
                    issues.append("Missing Ofsted latest_inspections header(s): " + ", ".join(missing))
            except ValueError as exc:
                issues.append(f"Ofsted latest_inspections CSV parse error: {exc}")

    if historical_url is not None:
        response = fetcher(historical_url)
        if _assert_status_ok(
            response=response,
            url=historical_url,
            source_label="Ofsted historical baseline CSV",
            issues=issues,
        ):
            try:
                headers = parse_csv_headers(response.body, skip_rows=1)
                missing = _missing_headers(REQUIRED_OFSTED_HISTORICAL_HEADERS, headers)
                if missing:
                    issues.append("Missing Ofsted historical header(s): " + ", ".join(missing))
            except ValueError as exc:
                issues.append(f"Ofsted historical CSV parse error: {exc}")

    imd_2025_landing_response = fetcher(imd_2025_landing_url)
    _assert_status_ok(
        response=imd_2025_landing_response,
        url=imd_2025_landing_url,
        source_label="IoD2025 landing page",
        issues=issues,
    )

    imd_2025_file_response = fetcher(imd_2025_file_url)
    if _assert_status_ok(
        response=imd_2025_file_response,
        url=imd_2025_file_url,
        source_label="IoD2025 File 7 CSV",
        issues=issues,
    ):
        try:
            headers = parse_csv_headers(imd_2025_file_response.body)
            missing = _missing_headers(REQUIRED_IMD_2025_HEADERS, headers)
            if missing:
                issues.append("Missing IoD2025 CSV header(s): " + ", ".join(missing))
        except ValueError as exc:
            issues.append(f"IoD2025 CSV parse error: {exc}")

    imd_2019_landing_response = fetcher(imd_2019_landing_url)
    _assert_status_ok(
        response=imd_2019_landing_response,
        url=imd_2019_landing_url,
        source_label="IoD2019 landing page",
        issues=issues,
    )

    imd_2019_file_response = fetcher(imd_2019_file_url)
    if _assert_status_ok(
        response=imd_2019_file_response,
        url=imd_2019_file_url,
        source_label="IoD2019 File 7 CSV",
        issues=issues,
    ):
        try:
            headers = parse_csv_headers(imd_2019_file_response.body)
            missing = _missing_headers(REQUIRED_IMD_2019_HEADERS, headers)
            if missing:
                issues.append("Missing IoD2019 CSV header(s): " + ", ".join(missing))
        except ValueError as exc:
            issues.append(f"IoD2019 CSV parse error: {exc}")

    police_archive_index_response = fetcher(police_archive_index_url)
    archive_url: str | None = police_archive_url_override
    if _assert_status_ok(
        response=police_archive_index_response,
        url=police_archive_index_url,
        source_label="Police archive index",
        issues=issues,
    ) and archive_url is None:
        try:
            archive_url = extract_latest_police_archive_url(police_archive_index_response.body)
        except ValueError as exc:
            issues.append(str(exc))

    if archive_url is not None:
        archive_response = (archive_fetcher or fetcher)(archive_url)
        _assert_status_ok(
            response=archive_response,
            url=archive_url,
            source_label="Police monthly archive",
            issues=issues,
        )

    police_columns_response = fetcher(POLICE_COLUMNS_REFERENCE_URL)
    if _assert_status_ok(
        response=police_columns_response,
        url=POLICE_COLUMNS_REFERENCE_URL,
        source_label="Police columns reference",
        issues=issues,
    ):
        for required_text in REQUIRED_POLICE_COLUMNS_TEXT:
            if required_text not in police_columns_response.body:
                issues.append(f"Police columns reference missing text: {required_text}")

    police_last_updated_response = fetcher(POLICE_LAST_UPDATED_URL)
    police_latest_month: str | None = None
    if _assert_status_ok(
        response=police_last_updated_response,
        url=POLICE_LAST_UPDATED_URL,
        source_label="Police crime-last-updated",
        issues=issues,
    ):
        payload = _json_loads_or_issue(
            police_last_updated_response.body,
            source_label="Police crime-last-updated",
            issues=issues,
        )
        if isinstance(payload, dict):
            date_value = payload.get("date")
            if isinstance(date_value, str) and len(date_value) >= 7:
                police_latest_month = date_value[:7]
            else:
                issues.append("Police crime-last-updated missing date")

    police_dates_response = fetcher(POLICE_STREET_DATES_URL)
    if _assert_status_ok(
        response=police_dates_response,
        url=POLICE_STREET_DATES_URL,
        source_label="Police crimes-street-dates",
        issues=issues,
    ):
        payload = _json_loads_or_issue(
            police_dates_response.body,
            source_label="Police crimes-street-dates",
            issues=issues,
        )
        if isinstance(payload, list):
            dates = [item.get("date") for item in payload if isinstance(item, dict)]
            if police_latest_month is not None and police_latest_month not in dates:
                issues.append(
                    "Police crimes-street-dates does not include month from crime-last-updated: "
                    f"{police_latest_month}"
                )
        else:
            issues.append("Police crimes-street-dates response missing date list")

    if police_latest_month is not None:
        categories_url = POLICE_CRIME_CATEGORIES_URL_TEMPLATE.format(month=police_latest_month)
        categories_response = fetcher(categories_url)
        if _assert_status_ok(
            response=categories_response,
            url=categories_url,
            source_label="Police crime-categories",
            issues=issues,
        ):
            payload = _json_loads_or_issue(
                categories_response.body,
                source_label="Police crime-categories",
                issues=issues,
            )
            if isinstance(payload, list):
                if not payload:
                    issues.append("Police crime-categories returned no categories")
                else:
                    first = payload[0]
                    if not isinstance(first, dict) or "url" not in first or "name" not in first:
                        issues.append("Police crime-categories payload missing url/name keys")
            else:
                issues.append("Police crime-categories response was not a JSON list")

        all_crime_url = POLICE_ALL_CRIME_URL_TEMPLATE.format(
            lat=police_sample_lat,
            lng=police_sample_lng,
            month=police_latest_month,
        )
        all_crime_response = fetcher(all_crime_url)
        if _assert_status_ok(
            response=all_crime_response,
            url=all_crime_url,
            source_label="Police all-crime sample",
            issues=issues,
        ):
            payload = _json_loads_or_issue(
                all_crime_response.body,
                source_label="Police all-crime sample",
                issues=issues,
            )
            if isinstance(payload, list):
                if not payload:
                    issues.append("Police all-crime sample returned no records")
                else:
                    first = payload[0]
                    if not isinstance(first, dict):
                        issues.append("Police all-crime sample first record was not an object")
                    else:
                        for key in REQUIRED_POLICE_CRIME_KEYS:
                            if key not in first:
                                issues.append(f"Police all-crime sample missing key: {key}")
                        location = first.get("location")
                        if not isinstance(location, dict):
                            issues.append("Police all-crime sample location was not an object")
                        else:
                            if "latitude" not in location:
                                issues.append("Police all-crime sample location missing latitude")
                            if "longitude" not in location:
                                issues.append("Police all-crime sample location missing longitude")
            else:
                issues.append("Police all-crime sample response was not a JSON list")

    police_limits_response = fetcher(POLICE_API_LIMITS_URL)
    if _assert_status_ok(
        response=police_limits_response,
        url=POLICE_API_LIMITS_URL,
        source_label="Police API limits page",
        issues=issues,
    ):
        body = police_limits_response.body
        if "15 requests per second" not in body:
            issues.append("Police API limits page missing expected 15 requests per second text")
        if "429" not in body:
            issues.append("Police API limits page missing expected 429 reference")

    postcode_lookup_url = POSTCODES_IO_URL_TEMPLATE.format(postcode=postcode_sample)
    postcode_response = fetcher(postcode_lookup_url)
    if _assert_status_ok(
        response=postcode_response,
        url=postcode_lookup_url,
        source_label="Postcodes.io lookup",
        issues=issues,
    ):
        payload = _json_loads_or_issue(
            postcode_response.body,
            source_label="Postcodes.io lookup",
            issues=issues,
        )
        if payload is not None:
            for field_path in REQUIRED_POSTCODE_FIELDS:
                if _get_nested(payload, field_path) is None:
                    issues.append("Postcodes.io missing field: " + ".".join(field_path))

    return VerificationOutcome(ok=not issues, issues=issues)


def main() -> int:
    ofsted_landing_url = os.getenv("CIVITAS_OFSTED_TIMELINE_SOURCE_INDEX_URL", OFSTED_LANDING_PAGE_URL).strip()
    if not ofsted_landing_url:
        print("FAIL: CIVITAS_OFSTED_TIMELINE_SOURCE_INDEX_URL is empty", file=sys.stderr)
        return 1

    ofsted_assets_override = os.getenv("CIVITAS_OFSTED_TIMELINE_SOURCE_ASSETS", "").strip() or None
    police_archive_override = os.getenv("CIVITAS_POLICE_CRIME_SOURCE_ARCHIVE_URL", "").strip() or None
    police_sample_lat = os.getenv("CIVITAS_POLICE_SAMPLE_LAT", DEFAULT_POLICE_SAMPLE_LAT).strip()
    police_sample_lng = os.getenv("CIVITAS_POLICE_SAMPLE_LNG", DEFAULT_POLICE_SAMPLE_LNG).strip()
    postcode_sample = os.getenv("CIVITAS_POSTCODE_SAMPLE", DEFAULT_POSTCODE_SAMPLE).strip()

    if not police_sample_lat or not police_sample_lng:
        print("FAIL: CIVITAS_POLICE_SAMPLE_LAT/CIVITAS_POLICE_SAMPLE_LNG must be set", file=sys.stderr)
        return 1
    if not postcode_sample:
        print("FAIL: CIVITAS_POSTCODE_SAMPLE is empty", file=sys.stderr)
        return 1

    try:
        float(police_sample_lat)
        float(police_sample_lng)
    except ValueError:
        print("FAIL: CIVITAS_POLICE_SAMPLE_LAT/CIVITAS_POLICE_SAMPLE_LNG must be numeric", file=sys.stderr)
        return 1

    try:
        outcome = verify_phase2_sources(
            fetcher=fetch_url,
            archive_fetcher=lambda url: fetch_url(url, max_bytes=1),
            ofsted_landing_url=ofsted_landing_url,
            ofsted_asset_override_csv=ofsted_assets_override,
            police_archive_url_override=police_archive_override,
            police_sample_lat=police_sample_lat,
            police_sample_lng=police_sample_lng,
            postcode_sample=postcode_sample,
        )
    except RuntimeError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    if outcome.ok:
        print("PASS: Phase 2 source contracts verified")
        return 0

    print("FAIL: Phase 2 source contract verification failed")
    for issue in outcome.issues:
        print(f"- {issue}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
