"""Verify Phase 1 external source contracts.

Run from repo root:
  uv run --project apps/backend python tools/scripts/verify_phase1_sources.py
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
from urllib.request import Request, urlopen

DEFAULT_DFE_DATASET_ID = "019afee4-ba17-73cb-85e0-f88c101bb734"
DEFAULT_DFE_PUBLICATION_TITLE = "Key stage 2 attainment"

DFE_BASE_URL = "https://api.education.gov.uk/statistics/v1"
DFE_PUBLICATIONS_URL = f"{DFE_BASE_URL}/publications?page=1&pageSize=20"
DFE_DATASETS_URL_TEMPLATE = f"{DFE_BASE_URL}/publications/{{publication_id}}/data-sets?page=1&pageSize=20"
DFE_DATASET_URL_TEMPLATE = f"{DFE_BASE_URL}/data-sets/{{dataset_id}}"
DFE_DATASET_META_URL_TEMPLATE = f"{DFE_BASE_URL}/data-sets/{{dataset_id}}/meta"
DFE_DATASET_QUERY_URL_TEMPLATE = f"{DFE_BASE_URL}/data-sets/{{dataset_id}}/query?page=1&pageSize=1"
DFE_DATASET_CSV_URL_TEMPLATE = f"{DFE_BASE_URL}/data-sets/{{dataset_id}}/csv"

OFSTED_LANDING_PAGE_URL = (
    "https://www.gov.uk/government/statistical-data-sets/"
    "monthly-management-information-ofsteds-school-inspections-outcomes"
)

REQUIRED_DFE_CSV_HEADERS = [
    "school_urn",
    "time_period",
    "ptfsm6cla1a",
    "psenelek",
    "psenelk",
    "psenele",
    "ptealgrp2",
    "ptealgrp1",
    "ptealgrp3",
]

REQUIRED_OFSTED_CSV_HEADERS = [
    "URN",
    "Inspection start date",
    "Publication date",
    "Latest OEIF overall effectiveness",
    "Ungraded inspection overall outcome",
]

_OFSTED_ASSET_URL_PATTERN = re.compile(
    r"https://assets\.publishing\.service\.gov\.uk/[^\"'<> ]*latest_inspections[^\"'<> ]*\.csv",
    flags=re.IGNORECASE,
)


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
            # Some responses may include gzip markers while remaining plain text.
            pass
    return raw_bytes.decode("utf-8-sig", errors="replace")


def fetch_url(url: str, *, timeout_seconds: float = 20.0) -> HttpResponse:
    request = Request(url=url, headers={"User-Agent": "civitas-phase1-source-verifier/1.0"})
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            status_code = int(response.getcode())
            raw_bytes = response.read()
            body = _decode_response_bytes(raw_bytes, response.headers.get("Content-Encoding"))
            return HttpResponse(status_code=status_code, body=body)
    except HTTPError as exc:
        body = exc.read().decode("utf-8-sig", errors="replace")
        return HttpResponse(status_code=int(exc.code), body=body)
    except URLError as exc:
        msg = f"Request failed for {url}: {exc.reason}"
        raise RuntimeError(msg) from exc


def parse_csv_headers(csv_text: str) -> list[str]:
    try:
        reader = csv.reader(io.StringIO(csv_text, newline=""))
        header_row = next(reader, None)
    except csv.Error as exc:
        raise ValueError(f"CSV response could not be parsed: {exc}") from exc
    if header_row is None:
        raise ValueError("CSV response was empty")

    cleaned_headers = [header.strip() for header in header_row]
    if cleaned_headers:
        cleaned_headers[0] = cleaned_headers[0].lstrip("\ufeff")
    return cleaned_headers


def extract_latest_ofsted_asset_url(landing_html: str) -> str:
    matches = _OFSTED_ASSET_URL_PATTERN.findall(landing_html)
    if not matches:
        msg = "Unable to locate latest Ofsted CSV asset URL on landing page"
        raise ValueError(msg)

    ranked_urls: list[tuple[datetime, str]] = []
    seen_urls: set[str] = set()
    for url in matches:
        if url in seen_urls:
            continue
        seen_urls.add(url)
        date_match = re.search(r"_(?:as_at|at)_(\d{1,2}_[A-Za-z]{3}_\d{4})\.csv$", url)
        if date_match is None:
            continue
        try:
            date_value = datetime.strptime(date_match.group(1), "%d_%b_%Y")
        except ValueError:
            continue
        ranked_urls.append((date_value, url))

    if ranked_urls:
        ranked_urls.sort(key=lambda entry: entry[0], reverse=True)
        return ranked_urls[0][1]

    return matches[0]


def _missing_headers(required: list[str], actual: list[str]) -> list[str]:
    actual_set = {header.strip() for header in actual}
    return [header for header in required if header not in actual_set]


def _find_publication_id(publications_json: str, publication_title: str) -> str:
    try:
        payload = json.loads(publications_json)
    except json.JSONDecodeError as exc:
        raise ValueError("DfE publications response was not valid JSON") from exc

    results = payload.get("results")
    if not isinstance(results, list):
        raise ValueError("DfE publications response missing results[]")

    target_title = publication_title.casefold()
    for publication in results:
        if not isinstance(publication, dict):
            continue
        title = publication.get("title")
        publication_id = publication.get("id")
        if (
            isinstance(title, str)
            and isinstance(publication_id, str)
            and title.casefold() == target_title
        ):
            return publication_id

    raise ValueError(
        f"DfE publication title '{publication_title}' not found in {DFE_PUBLICATIONS_URL}"
    )


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


def verify_phase1_sources(
    *,
    fetcher: Callable[[str], HttpResponse] = fetch_url,
    dataset_id: str = DEFAULT_DFE_DATASET_ID,
    publication_title: str = DEFAULT_DFE_PUBLICATION_TITLE,
) -> VerificationOutcome:
    issues: list[str] = []

    publications_response = fetcher(DFE_PUBLICATIONS_URL)
    publication_id: str | None = None
    if _assert_status_ok(
        response=publications_response,
        url=DFE_PUBLICATIONS_URL,
        source_label="DfE publications",
        issues=issues,
    ):
        try:
            publication_id = _find_publication_id(
                publications_json=publications_response.body,
                publication_title=publication_title,
            )
        except ValueError as exc:
            issues.append(str(exc))

    if publication_id is not None:
        dfe_dataset_list_url = DFE_DATASETS_URL_TEMPLATE.format(publication_id=publication_id)
        dataset_list_response = fetcher(dfe_dataset_list_url)
        _assert_status_ok(
            response=dataset_list_response,
            url=dfe_dataset_list_url,
            source_label="DfE publication datasets",
            issues=issues,
        )

    dataset_url = DFE_DATASET_URL_TEMPLATE.format(dataset_id=dataset_id)
    dataset_response = fetcher(dataset_url)
    _assert_status_ok(
        response=dataset_response,
        url=dataset_url,
        source_label="DfE dataset summary",
        issues=issues,
    )

    dataset_meta_url = DFE_DATASET_META_URL_TEMPLATE.format(dataset_id=dataset_id)
    dataset_meta_response = fetcher(dataset_meta_url)
    _assert_status_ok(
        response=dataset_meta_response,
        url=dataset_meta_url,
        source_label="DfE dataset metadata",
        issues=issues,
    )

    dataset_query_url = DFE_DATASET_QUERY_URL_TEMPLATE.format(dataset_id=dataset_id)
    dataset_query_response = fetcher(dataset_query_url)
    _assert_status_ok(
        response=dataset_query_response,
        url=dataset_query_url,
        source_label="DfE dataset query",
        issues=issues,
    )

    dataset_csv_url = DFE_DATASET_CSV_URL_TEMPLATE.format(dataset_id=dataset_id)
    dataset_csv_response = fetcher(dataset_csv_url)
    if _assert_status_ok(
        response=dataset_csv_response,
        url=dataset_csv_url,
        source_label="DfE dataset CSV",
        issues=issues,
    ):
        try:
            dfe_headers = parse_csv_headers(dataset_csv_response.body)
            missing_dfe_headers = _missing_headers(REQUIRED_DFE_CSV_HEADERS, dfe_headers)
            if missing_dfe_headers:
                issues.append("Missing DfE CSV header(s): " + ", ".join(missing_dfe_headers))
        except ValueError as exc:
            issues.append(f"DfE CSV parse error: {exc}")

    ofsted_landing_response = fetcher(OFSTED_LANDING_PAGE_URL)
    ofsted_asset_url: str | None = None
    if _assert_status_ok(
        response=ofsted_landing_response,
        url=OFSTED_LANDING_PAGE_URL,
        source_label="Ofsted landing page",
        issues=issues,
    ):
        try:
            ofsted_asset_url = extract_latest_ofsted_asset_url(ofsted_landing_response.body)
        except ValueError as exc:
            issues.append(str(exc))

    if ofsted_asset_url is not None:
        ofsted_csv_response = fetcher(ofsted_asset_url)
        if _assert_status_ok(
            response=ofsted_csv_response,
            url=ofsted_asset_url,
            source_label="Ofsted latest CSV",
            issues=issues,
        ):
            try:
                ofsted_headers = parse_csv_headers(ofsted_csv_response.body)
                missing_ofsted_headers = _missing_headers(REQUIRED_OFSTED_CSV_HEADERS, ofsted_headers)
                if missing_ofsted_headers:
                    issues.append("Missing Ofsted CSV header(s): " + ", ".join(missing_ofsted_headers))
            except ValueError as exc:
                issues.append(f"Ofsted CSV parse error: {exc}")

    return VerificationOutcome(ok=not issues, issues=issues)


def main() -> int:
    dataset_id = os.getenv("CIVITAS_DFE_CHARACTERISTICS_DATASET_ID", DEFAULT_DFE_DATASET_ID).strip()
    if not dataset_id:
        print("FAIL: CIVITAS_DFE_CHARACTERISTICS_DATASET_ID is empty", file=sys.stderr)
        return 1

    publication_title = os.getenv("CIVITAS_DFE_PUBLICATION_TITLE", DEFAULT_DFE_PUBLICATION_TITLE).strip()
    if not publication_title:
        print("FAIL: CIVITAS_DFE_PUBLICATION_TITLE is empty", file=sys.stderr)
        return 1

    try:
        outcome = verify_phase1_sources(
            fetcher=fetch_url,
            dataset_id=dataset_id,
            publication_title=publication_title,
        )
    except RuntimeError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    if outcome.ok:
        print("PASS: Phase 1 source contracts verified")
        return 0

    print("FAIL: Phase 1 source contract verification failed")
    for issue in outcome.issues:
        print(f"- {issue}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
