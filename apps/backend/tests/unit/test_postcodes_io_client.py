from __future__ import annotations

from civitas.infrastructure.http.postcodes_io_client import _parse_lookup_payload


def test_parse_lookup_payload_maps_lsoa_code_from_codes_object() -> None:
    payload = {
        "status": 200,
        "result": {
            "postcode": "SW1A 1AA",
            "latitude": 51.501,
            "longitude": -0.1416,
            "lsoa": "Westminster 018C",
            "admin_district": "Westminster",
            "codes": {
                "lsoa": "E01004736",
            },
        },
    }

    result = _parse_lookup_payload(postcode="SW1A 1AA", payload=payload)

    assert result.postcode == "SW1A 1AA"
    assert result.lsoa == "Westminster 018C"
    assert result.lsoa_code == "E01004736"
    assert result.admin_district == "Westminster"


def test_parse_lookup_payload_handles_missing_lsoa_code() -> None:
    payload = {
        "status": 200,
        "result": {
            "postcode": "SW1A 1AA",
            "latitude": 51.501,
            "longitude": -0.1416,
            "lsoa": "Westminster 018C",
            "admin_district": "Westminster",
        },
    }

    result = _parse_lookup_payload(postcode="SW1A 1AA", payload=payload)

    assert result.lsoa == "Westminster 018C"
    assert result.lsoa_code is None
