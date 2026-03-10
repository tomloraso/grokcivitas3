from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile

from civitas.infrastructure.pipelines.dfe_workforce import (
    _count_asset_rows,
    _is_school_level_row,
    _iter_manifest_asset_rows,
    _minimum_selected_academic_year_start,
    _should_stage_raw_row,
)


def test_support_staff_zip_helpers_accept_cp1252_entries(tmp_path: Path) -> None:
    zip_path = tmp_path / "support_staff.zip"
    csv_payload = (
        "time_period,time_identifier,geographic_level,school_urn,school_laestab,school_name,"
        "school_type,post,sex,ethnicity_major,full_time_equivalent,headcount\n"
        "202021,November,School,100001,123/4567,Saint John\u2019s Academy,Community school,"
        "Teaching assistants,Total,Total,1,2\n"
    ).encode("cp1252")

    with ZipFile(zip_path, "w") as archive:
        archive.writestr(
            "workforce_support_staff_characteristics_school_202021.csv",
            csv_payload,
        )

    assert (
        _count_asset_rows(
            zip_path,
            file_format="zip",
            zip_entries=["workforce_support_staff_characteristics_school_202021.csv"],
        )
        == 1
    )

    rows = list(
        _iter_manifest_asset_rows(
            zip_path,
            file_format="zip",
            zip_entries=["workforce_support_staff_characteristics_school_202021.csv"],
        )
    )
    assert rows == [
        {
            "time_period": "202021",
            "time_identifier": "November",
            "geographic_level": "School",
            "school_urn": "100001",
            "school_laestab": "123/4567",
            "school_name": "Saint John\u2019s Academy",
            "school_type": "Community school",
            "post": "Teaching assistants",
            "sex": "Total",
            "ethnicity_major": "Total",
            "full_time_equivalent": "1",
            "headcount": "2",
        }
    ]
    assert _is_school_level_row(rows[0], asset_kind="support_staff_characteristics") is True


def test_should_stage_raw_row_filters_out_school_rows_older_than_selected_window() -> None:
    minimum_start_year = _minimum_selected_academic_year_start(
        release_slugs=("2022", "2023", "2024"),
        lookback_years=3,
    )

    assert minimum_start_year == 2022
    assert (
        _should_stage_raw_row(
            {
                "time_period": "202021",
                "time_identifier": "Academic year",
                "geographic_level": "School",
                "school_urn": "100001",
            },
            asset_kind="teacher_characteristics",
            release_slug="2024",
            minimum_academic_year_start=minimum_start_year,
        )
        is False
    )
    assert (
        _should_stage_raw_row(
            {
                "time_period": "202425",
                "time_identifier": "Academic year",
                "geographic_level": "School",
                "school_urn": "100001",
            },
            asset_kind="teacher_characteristics",
            release_slug="2024",
            minimum_academic_year_start=minimum_start_year,
        )
        is True
    )
    assert (
        _should_stage_raw_row(
            {
                "time_period": "bad-year",
                "time_identifier": "Academic year",
                "geographic_level": "School",
                "school_urn": "100001",
            },
            asset_kind="teacher_characteristics",
            release_slug="2024",
            minimum_academic_year_start=minimum_start_year,
        )
        is True
    )
