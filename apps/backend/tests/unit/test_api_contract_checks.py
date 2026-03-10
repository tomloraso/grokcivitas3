import pytest

from civitas.api.contract_checks import (
    validate_school_compare_response_contract,
    validate_school_profile_response_contract,
    validate_schools_search_response_contract,
)


def _openapi_with_profile_properties(properties: dict[str, object]) -> dict[str, object]:
    return {
        "openapi": "3.1.0",
        "components": {
            "schemas": {
                "SchoolProfileResponse": {
                    "type": "object",
                    "properties": properties,
                    "required": list(properties),
                }
            }
        },
    }


def _openapi_with_compare_properties(properties: dict[str, object]) -> dict[str, object]:
    return {
        "openapi": "3.1.0",
        "components": {
            "schemas": {
                "SchoolCompareResponse": {
                    "type": "object",
                    "properties": properties,
                    "required": list(properties),
                },
                "SchoolCompareSectionResponse": {
                    "type": "object",
                    "properties": {
                        "key": {},
                        "label": {},
                        "rows": {},
                    },
                    "required": ["key", "label", "rows"],
                },
                "SchoolCompareRowResponse": {
                    "type": "object",
                    "properties": {
                        "metric_key": {},
                        "label": {},
                        "unit": {},
                        "cells": {},
                    },
                    "required": ["metric_key", "label", "unit", "cells"],
                },
            }
        },
    }


def _openapi_with_search_properties(properties: dict[str, object]) -> dict[str, object]:
    return {
        "openapi": "3.1.0",
        "components": {
            "schemas": {
                "SchoolsSearchResponse": {
                    "type": "object",
                    "properties": properties,
                    "required": list(properties),
                },
                "SchoolsSearchQueryResponse": {
                    "type": "object",
                    "properties": {
                        "postcode": {},
                        "radius_miles": {},
                        "phases": {},
                        "sort": {},
                    },
                    "required": ["postcode", "radius_miles", "phases", "sort"],
                },
                "PostcodeSchoolSearchItemResponse": {
                    "type": "object",
                    "properties": {
                        "urn": {},
                        "name": {},
                        "type": {},
                        "phase": {},
                        "postcode": {},
                        "lat": {},
                        "lng": {},
                        "distance_miles": {},
                        "pupil_count": {},
                        "latest_ofsted": {},
                        "academic_metric": {},
                    },
                    "required": [
                        "urn",
                        "name",
                        "type",
                        "phase",
                        "postcode",
                        "lat",
                        "lng",
                        "distance_miles",
                        "pupil_count",
                        "latest_ofsted",
                        "academic_metric",
                    ],
                },
                "SchoolSearchLatestOfstedResponse": {
                    "type": "object",
                    "properties": {
                        "label": {},
                        "sort_rank": {},
                        "availability": {},
                    },
                    "required": ["label", "sort_rank", "availability"],
                },
                "SchoolSearchAcademicMetricResponse": {
                    "type": "object",
                    "properties": {
                        "metric_key": {},
                        "label": {},
                        "display_value": {},
                        "sort_value": {},
                        "availability": {},
                    },
                    "required": [
                        "metric_key",
                        "label",
                        "display_value",
                        "sort_value",
                        "availability",
                    ],
                },
            }
        },
    }


def test_validate_school_profile_response_contract_accepts_required_properties() -> None:
    openapi_schema = _openapi_with_profile_properties(
        {
            "school": {},
            "overview_text": {},
            "analyst": {},
            "demographics_latest": {},
            "attendance_latest": {},
            "behaviour_latest": {},
            "workforce_latest": {},
            "leadership_snapshot": {},
            "performance": {},
            "ofsted_latest": {},
            "ofsted_timeline": {},
            "neighbourhood": {},
            "benchmarks": {},
            "completeness": {},
        }
    )

    validate_school_profile_response_contract(openapi_schema)


def test_validate_school_profile_response_contract_rejects_missing_properties() -> None:
    openapi_schema = _openapi_with_profile_properties(
        {
            "school": {},
            "overview_text": {},
            "analyst": {},
            "demographics_latest": {},
            "ofsted_latest": {},
            "benchmarks": {},
            "completeness": {},
        }
    )

    with pytest.raises(
        RuntimeError,
        match=(
            "SchoolProfileResponse missing required properties: "
            "attendance_latest, behaviour_latest, leadership_snapshot, "
            "neighbourhood, "
            "ofsted_timeline, performance, workforce_latest"
        ),
    ):
        validate_school_profile_response_contract(openapi_schema)


def test_validate_school_profile_response_contract_does_not_require_required_list() -> None:
    openapi_schema = _openapi_with_profile_properties(
        {
            "school": {},
            "overview_text": {},
            "analyst": {},
            "demographics_latest": {},
            "attendance_latest": {},
            "behaviour_latest": {},
            "workforce_latest": {},
            "leadership_snapshot": {},
            "performance": {},
            "ofsted_latest": {},
            "ofsted_timeline": {},
            "neighbourhood": {},
            "benchmarks": {},
            "completeness": {},
        }
    )
    del openapi_schema["components"]["schemas"]["SchoolProfileResponse"]["required"]

    validate_school_profile_response_contract(openapi_schema)


def test_validate_school_profile_response_contract_rejects_missing_schema() -> None:
    openapi_schema = {"openapi": "3.1.0", "components": {"schemas": {}}}

    with pytest.raises(
        RuntimeError,
        match="SchoolProfileResponse schema is missing",
    ):
        validate_school_profile_response_contract(openapi_schema)


def test_validate_school_compare_response_contract_accepts_required_properties() -> None:
    openapi_schema = _openapi_with_compare_properties(
        {
            "access": {},
            "schools": {},
            "sections": {},
        }
    )

    validate_school_compare_response_contract(openapi_schema)


def test_validate_school_compare_response_contract_rejects_missing_properties() -> None:
    openapi_schema = _openapi_with_compare_properties(
        {
            "access": {},
            "schools": {},
        }
    )

    with pytest.raises(
        RuntimeError,
        match="SchoolCompareResponse missing required properties: sections",
    ):
        validate_school_compare_response_contract(openapi_schema)


def test_validate_school_compare_response_contract_rejects_missing_required_list_entries() -> None:
    openapi_schema = _openapi_with_compare_properties(
        {
            "access": {},
            "schools": {},
            "sections": {},
        }
    )
    openapi_schema["components"]["schemas"]["SchoolCompareResponse"]["required"] = [
        "access",
        "schools",
    ]

    with pytest.raises(
        RuntimeError,
        match="SchoolCompareResponse required list is missing properties: sections",
    ):
        validate_school_compare_response_contract(openapi_schema)


def test_validate_school_compare_response_contract_rejects_missing_schema() -> None:
    openapi_schema = {"openapi": "3.1.0", "components": {"schemas": {}}}

    with pytest.raises(
        RuntimeError,
        match="SchoolCompareResponse schema is missing",
    ):
        validate_school_compare_response_contract(openapi_schema)


def test_validate_schools_search_response_contract_accepts_required_properties() -> None:
    openapi_schema = _openapi_with_search_properties(
        {
            "query": {},
            "center": {},
            "count": {},
            "schools": {},
        }
    )

    validate_schools_search_response_contract(openapi_schema)


def test_validate_schools_search_response_contract_rejects_missing_properties() -> None:
    openapi_schema = _openapi_with_search_properties(
        {
            "query": {},
            "count": {},
            "schools": {},
        }
    )

    with pytest.raises(
        RuntimeError,
        match="SchoolsSearchResponse missing required properties: center",
    ):
        validate_schools_search_response_contract(openapi_schema)
