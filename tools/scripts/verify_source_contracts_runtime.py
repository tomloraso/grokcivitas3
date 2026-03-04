"""Verify runtime source normalization contracts against local sample assets.

Run from repo root:
  uv run --project apps/backend python tools/scripts/verify_source_contracts_runtime.py
"""

from __future__ import annotations

import csv
import sys
from dataclasses import dataclass
from pathlib import Path

from civitas.infrastructure.pipelines.contracts import (
    dfe as dfe_contract,
    gias as gias_contract,
    ofsted_latest as ofsted_latest_contract,
    ofsted_timeline as ofsted_timeline_contract,
    ons_imd as ons_imd_contract,
    police as police_contract,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES_ROOT = REPO_ROOT / "apps" / "backend" / "tests" / "fixtures"


@dataclass(frozen=True)
class VerificationOutcome:
    ok: bool
    issues: list[str]


def _load_csv_rows(
    path: Path,
    *,
    encoding: str = "utf-8-sig",
    skip_rows: int = 0,
) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        raise FileNotFoundError(f"Fixture not found: {path}")

    with path.open("r", encoding=encoding, newline="") as handle:
        reader = csv.reader(handle)
        header_row: list[str] | None = None
        for _ in range(skip_rows + 1):
            header_row = next(reader, None)
        if header_row is None:
            raise ValueError(f"No header row found in {path}")

        cleaned_headers = [value.strip() for value in header_row]
        if cleaned_headers:
            cleaned_headers[0] = cleaned_headers[0].lstrip("\ufeff")

        dict_reader = csv.DictReader(handle, fieldnames=cleaned_headers)
        rows = [dict(row) for row in dict_reader]
    return cleaned_headers, rows


def _expect(condition: bool, message: str, *, issues: list[str]) -> None:
    if not condition:
        issues.append(message)


def verify_source_contracts_runtime() -> VerificationOutcome:
    issues: list[str] = []

    # DfE
    dfe_headers, dfe_rows = _load_csv_rows(
        FIXTURES_ROOT / "dfe_characteristics" / "school_characteristics_valid.csv"
    )
    try:
        dfe_contract.validate_headers(dfe_headers)
    except ValueError as exc:
        issues.append(f"DfE header contract failed: {exc}")
    _expect(bool(dfe_rows), "DfE fixture has no data rows", issues=issues)
    if dfe_rows:
        normalized, rejection = dfe_contract.normalize_row(
            dfe_rows[0],
            source_dataset_id="runtime-contract-check",
        )
        _expect(rejection is None, f"DfE valid row rejected: {rejection}", issues=issues)
        _expect(normalized is not None, "DfE valid row did not normalize", issues=issues)

        compact_variant = dict(dfe_rows[0])
        compact_variant["time_period"] = "202425"
        compact_normalized, compact_rejection = dfe_contract.normalize_row(
            compact_variant,
            source_dataset_id="runtime-contract-check",
        )
        _expect(
            compact_rejection is None,
            f"DfE compact year token was rejected: {compact_rejection}",
            issues=issues,
        )
        _expect(
            compact_normalized is not None and compact_normalized["academic_year"] == "2024/25",
            "DfE compact year token did not canonicalize to 2024/25",
            issues=issues,
        )

    # GIAS
    gias_headers, gias_rows = _load_csv_rows(
        FIXTURES_ROOT / "gias" / "edubasealldata_valid.csv",
        encoding="cp1252",
    )
    try:
        gias_contract.validate_headers(gias_headers)
    except ValueError as exc:
        issues.append(f"GIAS header contract failed: {exc}")
    _expect(bool(gias_rows), "GIAS fixture has no data rows", issues=issues)
    if gias_rows:
        normalized, rejection = gias_contract.normalize_row(gias_rows[0])
        _expect(rejection is None, f"GIAS valid row rejected: {rejection}", issues=issues)
        _expect(normalized is not None, "GIAS valid row did not normalize", issues=issues)

    # Ofsted latest
    ofsted_latest_headers, ofsted_latest_rows = _load_csv_rows(
        FIXTURES_ROOT / "ofsted_latest" / "latest_inspections_valid.csv"
    )
    try:
        ofsted_latest_contract.validate_headers(ofsted_latest_headers)
    except ValueError as exc:
        issues.append(f"Ofsted latest header contract failed: {exc}")
    _expect(bool(ofsted_latest_rows), "Ofsted latest fixture has no data rows", issues=issues)
    if ofsted_latest_rows:
        baseline = dict(ofsted_latest_rows[0])
        normalized, rejection = ofsted_latest_contract.normalize_row(
            baseline,
            source_asset_url="fixture://ofsted-latest",
            source_asset_month="2026-01",
        )
        _expect(
            rejection is None,
            f"Ofsted latest valid row rejected: {rejection}",
            issues=issues,
        )
        _expect(
            normalized is not None,
            "Ofsted latest valid row did not normalize",
            issues=issues,
        )

        null_variant = dict(baseline)
        null_variant["Latest OEIF overall effectiveness"] = "NULL"
        null_normalized, null_rejection = ofsted_latest_contract.normalize_row(
            null_variant,
            source_asset_url="fixture://ofsted-latest",
            source_asset_month="2026-01",
        )
        _expect(
            null_rejection is None,
            f"Ofsted latest NULL effectiveness rejected: {null_rejection}",
            issues=issues,
        )
        _expect(
            null_normalized is not None and null_normalized["overall_effectiveness_code"] is None,
            "Ofsted latest NULL effectiveness was not treated as missing",
            issues=issues,
        )

        code9_variant = dict(baseline)
        code9_variant["Latest OEIF overall effectiveness"] = "9"
        code9_normalized, code9_rejection = ofsted_latest_contract.normalize_row(
            code9_variant,
            source_asset_url="fixture://ofsted-latest",
            source_asset_month="2026-01",
        )
        _expect(
            code9_rejection is None,
            f"Ofsted latest code 9 rejected: {code9_rejection}",
            issues=issues,
        )
        _expect(
            code9_normalized is not None
            and code9_normalized["overall_effectiveness_code"] == "Not judged",
            "Ofsted latest code 9 did not map to Not judged",
            issues=issues,
        )

    # Ofsted timeline (YTD + historical)
    ofsted_ytd_headers, ofsted_ytd_rows = _load_csv_rows(
        FIXTURES_ROOT / "ofsted_timeline" / "all_inspections_ytd_mixed.csv"
    )
    try:
        ofsted_timeline_contract.validate_headers(
            ofsted_ytd_headers,
            schema_version=ofsted_timeline_contract.SCHEMA_VERSION_YTD,
        )
    except ValueError as exc:
        issues.append(f"Ofsted timeline YTD header contract failed: {exc}")
    _expect(bool(ofsted_ytd_rows), "Ofsted timeline YTD fixture has no data rows", issues=issues)
    if ofsted_ytd_rows:
        baseline = dict(ofsted_ytd_rows[0])
        normalized, rejection = ofsted_timeline_contract.normalize_row(
            baseline,
            source_schema_version=ofsted_timeline_contract.SCHEMA_VERSION_YTD,
            source_asset_url="fixture://ofsted-timeline-ytd",
            source_asset_month="2026-01",
        )
        _expect(
            rejection is None,
            f"Ofsted timeline YTD valid row rejected: {rejection}",
            issues=issues,
        )
        _expect(
            normalized is not None,
            "Ofsted timeline YTD valid row did not normalize",
            issues=issues,
        )

        null_variant = dict(baseline)
        null_variant["Latest OEIF overall effectiveness"] = "NULL"
        null_normalized, null_rejection = ofsted_timeline_contract.normalize_row(
            null_variant,
            source_schema_version=ofsted_timeline_contract.SCHEMA_VERSION_YTD,
            source_asset_url="fixture://ofsted-timeline-ytd",
            source_asset_month="2026-01",
        )
        _expect(
            null_rejection is None,
            f"Ofsted timeline NULL effectiveness rejected: {null_rejection}",
            issues=issues,
        )
        _expect(
            null_normalized is not None and null_normalized["overall_effectiveness_code"] is None,
            "Ofsted timeline NULL effectiveness was not treated as missing",
            issues=issues,
        )

        code9_variant = dict(baseline)
        code9_variant["Latest OEIF overall effectiveness"] = "9"
        code9_normalized, code9_rejection = ofsted_timeline_contract.normalize_row(
            code9_variant,
            source_schema_version=ofsted_timeline_contract.SCHEMA_VERSION_YTD,
            source_asset_url="fixture://ofsted-timeline-ytd",
            source_asset_month="2026-01",
        )
        _expect(
            code9_rejection is None,
            f"Ofsted timeline code 9 rejected: {code9_rejection}",
            issues=issues,
        )
        _expect(
            code9_normalized is not None
            and code9_normalized["overall_effectiveness_code"] == "Not judged",
            "Ofsted timeline code 9 did not map to Not judged",
            issues=issues,
        )

    ofsted_historical_headers, ofsted_historical_rows = _load_csv_rows(
        FIXTURES_ROOT / "ofsted_timeline" / "all_inspections_historical_2015_2019_mixed.csv",
        skip_rows=1,
    )
    try:
        ofsted_timeline_contract.validate_headers(
            ofsted_historical_headers,
            schema_version=ofsted_timeline_contract.SCHEMA_VERSION_HISTORICAL_2015_2019,
        )
    except ValueError as exc:
        issues.append(f"Ofsted timeline historical header contract failed: {exc}")
    _expect(
        bool(ofsted_historical_rows),
        "Ofsted timeline historical fixture has no data rows",
        issues=issues,
    )
    if ofsted_historical_rows:
        normalized, rejection = ofsted_timeline_contract.normalize_row(
            ofsted_historical_rows[0],
            source_schema_version=ofsted_timeline_contract.SCHEMA_VERSION_HISTORICAL_2015_2019,
            source_asset_url="fixture://ofsted-timeline-historical",
            source_asset_month=None,
        )
        _expect(
            rejection is None,
            f"Ofsted timeline historical valid row rejected: {rejection}",
            issues=issues,
        )
        _expect(
            normalized is not None,
            "Ofsted timeline historical valid row did not normalize",
            issues=issues,
        )

    # ONS IMD 2025 + 2019
    ons_2025_headers, ons_2025_rows = _load_csv_rows(
        FIXTURES_ROOT / "ons_imd" / "file_7_valid_2025.csv"
    )
    try:
        ons_imd_contract.validate_headers(
            ons_2025_headers,
            source_release=ons_imd_contract.IMD_RELEASE_IOD2025,
        )
    except ValueError as exc:
        issues.append(f"ONS IMD 2025 header contract failed: {exc}")
    _expect(bool(ons_2025_rows), "ONS IMD 2025 fixture has no data rows", issues=issues)
    if ons_2025_rows:
        normalized, rejection = ons_imd_contract.normalize_row(
            ons_2025_rows[0],
            source_release=ons_imd_contract.IMD_RELEASE_IOD2025,
            source_file_url="fixture://ons-imd-2025",
        )
        _expect(rejection is None, f"ONS IMD 2025 valid row rejected: {rejection}", issues=issues)
        _expect(normalized is not None, "ONS IMD 2025 valid row did not normalize", issues=issues)

    ons_2019_sample_row = {
        "LSOA code (2011)": "E01000003",
        "LSOA name (2011)": "Beta 001A",
        "Local Authority District code (2019)": "E09000002",
        "Local Authority District name (2019)": "Beta District",
        ons_imd_contract.IMD_SCORE_HEADER: "19.8",
        ons_imd_contract.IMD_RANK_HEADER: "540",
        ons_imd_contract.IMD_DECILE_HEADER: "2",
        ons_imd_contract.IDACI_SCORE_HEADER: "0.31",
        ons_imd_contract.IDACI_RANK_HEADER: "700",
        ons_imd_contract.IDACI_DECILE_HEADER: "2",
    }
    try:
        ons_imd_contract.validate_headers(
            list(ons_2019_sample_row.keys()),
            source_release=ons_imd_contract.IMD_RELEASE_IOD2019,
        )
    except ValueError as exc:
        issues.append(f"ONS IMD 2019 header contract failed: {exc}")
    normalized, rejection = ons_imd_contract.normalize_row(
        ons_2019_sample_row,
        source_release=ons_imd_contract.IMD_RELEASE_IOD2019,
        source_file_url="fixture://ons-imd-2019",
    )
    _expect(rejection is None, f"ONS IMD 2019 valid row rejected: {rejection}", issues=issues)
    _expect(normalized is not None, "ONS IMD 2019 valid row did not normalize", issues=issues)

    # Police
    police_headers, police_rows = _load_csv_rows(
        FIXTURES_ROOT / "police_crime_context" / "2026-01-example-street.csv"
    )
    try:
        police_contract.validate_headers(police_headers)
    except ValueError as exc:
        issues.append(f"Police header contract failed: {exc}")
    _expect(bool(police_rows), "Police fixture has no data rows", issues=issues)
    if police_rows:
        normalized, rejection = police_contract.normalize_row(police_rows[0])
        _expect(rejection is None, f"Police valid row rejected: {rejection}", issues=issues)
        _expect(normalized is not None, "Police valid row did not normalize", issues=issues)

    return VerificationOutcome(ok=not issues, issues=issues)


def main() -> int:
    try:
        outcome = verify_source_contracts_runtime()
    except (FileNotFoundError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    if outcome.ok:
        print("PASS: Runtime source normalization contracts verified")
        return 0

    print("FAIL: Runtime source normalization contract verification failed")
    for issue in outcome.issues:
        print(f"- {issue}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
