import pytest

from civitas.api.contract_checks import validate_school_profile_response_contract


def _openapi_with_profile_properties(properties: dict[str, object]) -> dict[str, object]:
    return {
        "openapi": "3.1.0",
        "components": {
            "schemas": {
                "SchoolProfileResponse": {
                    "type": "object",
                    "properties": properties,
                }
            }
        },
    }


def test_validate_school_profile_response_contract_accepts_required_properties() -> None:
    openapi_schema = _openapi_with_profile_properties(
        {
            "school": {},
            "overview_text": {},
            "analyst_text": {},
            "demographics_latest": {},
            "attendance_latest": {},
            "behaviour_latest": {},
            "workforce_latest": {},
            "leadership_snapshot": {},
            "performance": {},
            "ofsted_latest": {},
            "ofsted_timeline": {},
            "area_context": {},
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
            "analyst_text": {},
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
            "area_context, attendance_latest, behaviour_latest, leadership_snapshot, "
            "ofsted_timeline, performance, workforce_latest"
        ),
    ):
        validate_school_profile_response_contract(openapi_schema)


def test_validate_school_profile_response_contract_rejects_missing_schema() -> None:
    openapi_schema = {"openapi": "3.1.0", "components": {"schemas": {}}}

    with pytest.raises(
        RuntimeError,
        match="SchoolProfileResponse schema is missing",
    ):
        validate_school_profile_response_contract(openapi_schema)
