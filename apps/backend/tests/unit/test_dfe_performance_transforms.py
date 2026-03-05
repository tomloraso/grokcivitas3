from __future__ import annotations

from urllib.parse import parse_qs, urlsplit

import pytest

from civitas.infrastructure.pipelines.dfe_performance import (
    _normalize_result_key,
    _school_location_urn_lookup,
    _validate_school_location_lookup,
    _with_dataset_version,
)


def test_school_location_lookup_supports_grouped_locations_with_school_urns() -> None:
    meta_payload = {
        "locations": [
            {
                "level": {"code": "NAT", "label": "National"},
                "options": [{"id": "nat", "code": "E92000001", "label": "England"}],
            },
            {
                "level": {"code": "SCH", "label": "School"},
                "options": [
                    {"id": "school-a", "urn": "123456", "label": "School A"},
                    {"id": "school-b", "urn": "invalid", "label": "School B"},
                ],
            },
        ]
    }

    assert _school_location_urn_lookup(meta_payload) == {"school-a": "123456"}


def test_school_location_lookup_supports_legacy_locations_object_shape() -> None:
    meta_payload = {
        "locations": {
            "options": [
                {"id": "legacy-a", "code": "100001", "label": "School A"},
                {"id": "legacy-b", "code": "E92000001", "label": "England"},
            ]
        }
    }

    assert _school_location_urn_lookup(meta_payload) == {"legacy-a": "100001"}


def test_normalize_result_key_uses_school_location_level_code() -> None:
    result_payload = {
        "timePeriod": {"period": "2023/2024"},
        "locations": {"NAT": "nat", "SCH": "school-a"},
    }

    key, rejection = _normalize_result_key(
        result_payload,
        urn_lookup={"school-a": "123456"},
    )

    assert rejection is None
    assert key == ("123456", "2023/24")


def test_normalize_result_key_falls_back_for_legacy_location_payload() -> None:
    result_payload = {
        "timePeriod": {"period": "2023/2024"},
        "locations": {"legacy": "100001"},
    }

    key, rejection = _normalize_result_key(
        result_payload,
        urn_lookup={},
    )

    assert rejection is None
    assert key == ("100001", "2023/24")


def test_validate_school_location_lookup_raises_when_mapping_is_empty() -> None:
    with pytest.raises(ValueError, match="ks2"):
        _validate_school_location_lookup(lookup={}, dataset_key="ks2")


def test_with_dataset_version_appends_version_query_parameter() -> None:
    url = _with_dataset_version(
        "https://api.education.gov.uk/statistics/v1/data-sets/example/query?page=2",
        dataset_version="1.0.1",
    )

    query = parse_qs(urlsplit(url).query)
    assert query["page"] == ["2"]
    assert query["dataSetVersion"] == ["1.0.1"]


def test_with_dataset_version_preserves_existing_parameter() -> None:
    url = _with_dataset_version(
        "https://api.education.gov.uk/statistics/v1/data-sets/example/query?dataSetVersion=0.9&page=2",
        dataset_version="1.0.1",
    )

    query = parse_qs(urlsplit(url).query)
    assert query["dataSetVersion"] == ["0.9"]
    assert query["page"] == ["2"]
