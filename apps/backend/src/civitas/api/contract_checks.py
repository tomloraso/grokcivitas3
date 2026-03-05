from collections.abc import Mapping

from fastapi import FastAPI

REQUIRED_SCHOOL_PROFILE_PROPERTIES = frozenset(
    {
        "school",
        "demographics_latest",
        "attendance_latest",
        "behaviour_latest",
        "workforce_latest",
        "leadership_snapshot",
        "performance",
        "ofsted_latest",
        "ofsted_timeline",
        "area_context",
        "benchmarks",
        "completeness",
    }
)


def validate_app_contracts(app: FastAPI) -> None:
    validate_school_profile_response_contract(app.openapi())


def validate_school_profile_response_contract(openapi_schema: Mapping[str, object]) -> None:
    schema = _school_profile_response_schema(openapi_schema)
    properties = schema.get("properties")
    if not isinstance(properties, Mapping):
        raise RuntimeError(
            "API contract check failed: SchoolProfileResponse properties are missing.",
        )

    property_names = {str(name) for name in properties}
    missing = sorted(REQUIRED_SCHOOL_PROFILE_PROPERTIES - property_names)
    if missing:
        missing_text = ", ".join(missing)
        raise RuntimeError(
            "API contract check failed: SchoolProfileResponse missing required properties: "
            f"{missing_text}.",
        )


def _school_profile_response_schema(openapi_schema: Mapping[str, object]) -> Mapping[str, object]:
    components = openapi_schema.get("components")
    if not isinstance(components, Mapping):
        raise RuntimeError("API contract check failed: OpenAPI components are missing.")

    schemas = components.get("schemas")
    if not isinstance(schemas, Mapping):
        raise RuntimeError("API contract check failed: OpenAPI schemas are missing.")

    school_profile_schema = schemas.get("SchoolProfileResponse")
    if not isinstance(school_profile_schema, Mapping):
        raise RuntimeError(
            "API contract check failed: SchoolProfileResponse schema is missing.",
        )

    return school_profile_schema
