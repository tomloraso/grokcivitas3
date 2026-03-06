"""Verify Phase 4 demographics sources and contracts.

Run from repo root:
  uv run --project apps/backend python tools/scripts/verify_phase_s_sources.py
"""

from __future__ import annotations

import csv
import gzip
import io
import json
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

from civitas.infrastructure.config.settings import AppSettings
from civitas.infrastructure.pipelines.contracts import demographics_spc
from civitas.infrastructure.pipelines.demographics_release_files import (
    DemographicsSourceFamily,
    build_release_page_url,
    parse_release_version_from_page,
    select_school_level_file,
)

REQUIRED_SPC_COLUMNS = (
    "% of pupils known to be eligible for free school meals",
    "% of pupils known to be eligible for free school meals (Performance Tables)",
    "% of pupils whose first language is known or believed to be other than English",
    "% of pupils whose first language is known or believed to be English",
    "% of pupils whose first language is unclassified",
    *tuple(
        group.count_header for group in demographics_spc.ETHNICITY_GROUP_FIELDS
    ),
    *tuple(
        group.pct_header for group in demographics_spc.ETHNICITY_GROUP_FIELDS
    ),
)
REQUIRED_SEN_COLUMNS = (
    "URN",
    "time_period",
    "Total pupils",
    "SEN support",
    "EHC plan",
)


@dataclass(frozen=True)
class HttpResponse:
    status_code: int
    body: str


@dataclass(frozen=True)
class SourceCatalogEntry:
    family: str
    publication_slug: str
    release_slug: str
    release_version_id: str
    file_id: str
    file_name: str


@dataclass(frozen=True)
class VerificationOutcome:
    ok: bool
    issues: tuple[str, ...]
    catalog_entries: tuple[SourceCatalogEntry, ...]


def fetch_url(url: str, *, timeout_seconds: float = 60.0) -> HttpResponse:
    request = urllib.request.Request(url, headers={"User-Agent": "civitas-phase-s-source-verifier/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            raw_bytes = response.read()
            body = _decode_response_bytes(raw_bytes, response.headers.get("Content-Encoding"))
            return HttpResponse(status_code=int(response.getcode()), body=body)
    except Exception as exc:
        raise RuntimeError(f"Request failed for {url}: {exc}") from exc


def verify_phase_s_sources(
    *,
    spc_publication_slug: str,
    sen_publication_slug: str,
    release_slugs: Sequence[str],
    lookback_years: int,
    fetcher: Callable[[str], HttpResponse] = fetch_url,
) -> VerificationOutcome:
    issues: list[str] = []
    catalog_entries: list[SourceCatalogEntry] = []

    selected_release_slugs = tuple(dict.fromkeys(slug.strip() for slug in release_slugs if slug.strip()))[
        -lookback_years:
    ]
    if not selected_release_slugs:
        return VerificationOutcome(
            ok=False,
            issues=("No release slugs configured for demographics source verification.",),
            catalog_entries=(),
        )

    families = (
        (DemographicsSourceFamily.SPC, spc_publication_slug, REQUIRED_SPC_COLUMNS),
        (DemographicsSourceFamily.SEN, sen_publication_slug, REQUIRED_SEN_COLUMNS),
    )

    for family, publication_slug, required_columns in families:
        for release_slug in selected_release_slugs:
            page_url = build_release_page_url(
                publication_slug=publication_slug,
                release_slug=release_slug,
            )
            page_response = fetcher(page_url)
            if page_response.status_code != 200:
                issues.append(
                    f"{family.value}:{release_slug} release page returned "
                    f"{page_response.status_code}: {page_url}"
                )
                continue

            try:
                release_version = parse_release_version_from_page(page_response.body)
            except ValueError as exc:
                issues.append(f"{family.value}:{release_slug} invalid release page payload: {exc}")
                continue

            release_version_id = _as_non_empty_str(release_version.get("id"))
            if release_version_id is None:
                issues.append(f"{family.value}:{release_slug} missing release version id")
                continue

            download_files = release_version.get("downloadFiles")
            if not isinstance(download_files, list):
                issues.append(f"{family.value}:{release_slug} missing downloadFiles list")
                continue

            selected_file = select_school_level_file(download_files)
            if selected_file is None:
                issues.append(
                    f"{family.value}:{release_slug} missing school-level underlying data file"
                )
                continue

            file_id = _as_non_empty_str(selected_file.get("id"))
            file_name = _as_non_empty_str(selected_file.get("name"))
            if file_id is None or file_name is None:
                issues.append(f"{family.value}:{release_slug} selected file missing id or name")
                continue

            csv_url = (
                "https://content.explore-education-statistics.service.gov.uk/api/releases/"
                f"{release_version_id}/files/{file_id}"
            )
            csv_response = fetcher(csv_url)
            if csv_response.status_code != 200:
                issues.append(
                    f"{family.value}:{release_slug} file download returned "
                    f"{csv_response.status_code}: {csv_url}"
                )
                continue

            try:
                headers = parse_csv_headers(csv_response.body)
            except ValueError as exc:
                issues.append(f"{family.value}:{release_slug} CSV parse error: {exc}")
                continue

            missing_columns = _missing_columns(
                required_columns=required_columns,
                headers=headers,
            )
            if family == DemographicsSourceFamily.SPC:
                if not any(_normalize_header(header) == "urn" for header in headers):
                    missing_columns.append("urn|URN")

            if missing_columns:
                issues.append(
                    f"{family.value}:{release_slug} missing required columns: "
                    + ", ".join(sorted(missing_columns))
                )
                continue

            catalog_entries.append(
                SourceCatalogEntry(
                    family=family.value,
                    publication_slug=publication_slug,
                    release_slug=release_slug,
                    release_version_id=release_version_id,
                    file_id=file_id,
                    file_name=file_name,
                )
            )

    catalog_entries = sorted(
        catalog_entries,
        key=lambda item: (item.family, item.release_slug, item.file_id),
    )
    return VerificationOutcome(
        ok=len(issues) == 0,
        issues=tuple(issues),
        catalog_entries=tuple(catalog_entries),
    )


def parse_csv_headers(csv_text: str) -> tuple[str, ...]:
    reader = csv.reader(io.StringIO(csv_text, newline=""))
    header_row = next(reader, None)
    if header_row is None:
        raise ValueError("CSV response was empty")

    cleaned = [header.lstrip("\ufeff").strip() for header in header_row]
    return tuple(cleaned)


def write_source_catalog(
    *,
    output_path: Path,
    outcome: VerificationOutcome,
) -> None:
    lines = [
        "# Phase 4 Source Catalog",
        "",
        f"Generated from `tools/scripts/verify_phase_s_sources.py`.",
        "",
        "| Family | Publication slug | Release slug | Release version id | File id | File name |",
        "|---|---|---|---|---|---|",
    ]
    for item in outcome.catalog_entries:
        lines.append(
            "| "
            + " | ".join(
                [
                    item.family,
                    item.publication_slug,
                    item.release_slug,
                    item.release_version_id,
                    item.file_id,
                    item.file_name.replace("|", "\\|"),
                ]
            )
            + " |"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    settings = AppSettings()
    pipeline_settings = settings.pipeline
    outcome = verify_phase_s_sources(
        spc_publication_slug=pipeline_settings.demographics_spc_publication_slug,
        sen_publication_slug=pipeline_settings.demographics_sen_publication_slug,
        release_slugs=pipeline_settings.demographics_release_slugs,
        lookback_years=int(pipeline_settings.demographics_lookback_years),
    )

    catalog_path = Path(
        ".planning/phases/phase-4-source-stabilization/"
        "source-catalog-2026-03-04.md"
    )
    write_source_catalog(output_path=catalog_path, outcome=outcome)

    if outcome.ok:
        print("PASS: Phase 4 source contracts verified")
        print(f"Catalog: {catalog_path}")
        return 0

    print("FAIL: Phase 4 source contract verification failed")
    print(f"Catalog: {catalog_path}")
    for issue in outcome.issues:
        print(f"- {issue}")
    return 1


def _decode_response_bytes(raw_bytes: bytes, content_encoding: str | None) -> str:
    encoding_value = (content_encoding or "").casefold()
    should_try_gzip = "gzip" in encoding_value or raw_bytes.startswith(b"\x1f\x8b")
    if should_try_gzip:
        try:
            raw_bytes = gzip.decompress(raw_bytes)
        except OSError:
            pass
    return raw_bytes.decode("utf-8-sig", errors="replace")


def _missing_columns(*, required_columns: Sequence[str], headers: Sequence[str]) -> list[str]:
    header_lookup = {_normalize_header(header): header for header in headers}
    missing: list[str] = []
    for column in required_columns:
        if _normalize_header(column) not in header_lookup:
            missing.append(column)
    return missing


def _normalize_header(value: str) -> str:
    return value.lstrip("\ufeff").strip().casefold()


def _as_non_empty_str(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized if normalized else None


if __name__ == "__main__":
    raise SystemExit(main())
