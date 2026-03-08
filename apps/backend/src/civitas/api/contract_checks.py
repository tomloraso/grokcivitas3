from collections.abc import Mapping

from fastapi import FastAPI

REQUIRED_SCHOOL_PROFILE_PROPERTIES = frozenset(
    {
        "school",
        "overview_text",
        "analyst_text",
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
REQUIRED_SCHOOL_COMPARE_PROPERTIES = frozenset({"schools", "sections"})
REQUIRED_SCHOOL_COMPARE_SECTION_PROPERTIES = frozenset({"key", "label", "rows"})
REQUIRED_SCHOOL_COMPARE_ROW_PROPERTIES = frozenset({"metric_key", "label", "unit", "cells"})
REQUIRED_SCHOOLS_SEARCH_PROPERTIES = frozenset({"query", "center", "count", "schools"})
REQUIRED_SCHOOLS_SEARCH_QUERY_PROPERTIES = frozenset({"postcode", "radius_miles", "phases", "sort"})
REQUIRED_POSTCODE_SEARCH_ITEM_PROPERTIES = frozenset(
    {
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
    }
)
REQUIRED_SEARCH_OFSTED_PROPERTIES = frozenset({"label", "sort_rank", "availability"})
REQUIRED_SEARCH_ACADEMIC_METRIC_PROPERTIES = frozenset(
    {"metric_key", "label", "display_value", "sort_value", "availability"}
)


def validate_app_contracts(app: FastAPI) -> None:
    openapi_schema = app.openapi()
    validate_school_profile_response_contract(openapi_schema)
    validate_school_compare_response_contract(openapi_schema)
    validate_schools_search_response_contract(openapi_schema)


def validate_school_profile_response_contract(openapi_schema: Mapping[str, object]) -> None:
    _validate_required_properties(
        openapi_schema,
        schema_name="SchoolProfileResponse",
        required_properties=REQUIRED_SCHOOL_PROFILE_PROPERTIES,
        validate_required_list=False,
    )


def validate_school_compare_response_contract(openapi_schema: Mapping[str, object]) -> None:
    _validate_required_properties(
        openapi_schema,
        schema_name="SchoolCompareResponse",
        required_properties=REQUIRED_SCHOOL_COMPARE_PROPERTIES,
        validate_required_list=True,
    )
    _validate_required_properties(
        openapi_schema,
        schema_name="SchoolCompareSectionResponse",
        required_properties=REQUIRED_SCHOOL_COMPARE_SECTION_PROPERTIES,
        validate_required_list=True,
    )
    _validate_required_properties(
        openapi_schema,
        schema_name="SchoolCompareRowResponse",
        required_properties=REQUIRED_SCHOOL_COMPARE_ROW_PROPERTIES,
        validate_required_list=True,
    )


def validate_schools_search_response_contract(openapi_schema: Mapping[str, object]) -> None:
    _validate_required_properties(
        openapi_schema,
        schema_name="SchoolsSearchResponse",
        required_properties=REQUIRED_SCHOOLS_SEARCH_PROPERTIES,
        validate_required_list=True,
    )
    _validate_required_properties(
        openapi_schema,
        schema_name="SchoolsSearchQueryResponse",
        required_properties=REQUIRED_SCHOOLS_SEARCH_QUERY_PROPERTIES,
        validate_required_list=True,
    )
    _validate_required_properties(
        openapi_schema,
        schema_name="PostcodeSchoolSearchItemResponse",
        required_properties=REQUIRED_POSTCODE_SEARCH_ITEM_PROPERTIES,
        validate_required_list=True,
    )
    _validate_required_properties(
        openapi_schema,
        schema_name="SchoolSearchLatestOfstedResponse",
        required_properties=REQUIRED_SEARCH_OFSTED_PROPERTIES,
        validate_required_list=True,
    )
    _validate_required_properties(
        openapi_schema,
        schema_name="SchoolSearchAcademicMetricResponse",
        required_properties=REQUIRED_SEARCH_ACADEMIC_METRIC_PROPERTIES,
        validate_required_list=True,
    )


def _validate_required_properties(
    openapi_schema: Mapping[str, object],
    *,
    schema_name: str,
    required_properties: frozenset[str],
    validate_required_list: bool,
) -> None:
    schema = _schema_by_name(openapi_schema, schema_name)
    properties = schema.get("properties")
    if not isinstance(properties, Mapping):
        raise RuntimeError(
            f"API contract check failed: {schema_name} properties are missing.",
        )

    property_names = {str(name) for name in properties}
    missing = sorted(required_properties - property_names)
    if missing:
        missing_text = ", ".join(missing)
        raise RuntimeError(
            f"API contract check failed: {schema_name} missing required properties: "
            f"{missing_text}.",
        )

    if validate_required_list:
        required = schema.get("required")
        if not isinstance(required, list):
            raise RuntimeError(
                f"API contract check failed: {schema_name} required properties are missing.",
            )

        required_names = {str(name) for name in required}
        missing_required = sorted(required_properties - required_names)
        if missing_required:
            missing_required_text = ", ".join(missing_required)
            raise RuntimeError(
                f"API contract check failed: {schema_name} required list is missing properties: "
                f"{missing_required_text}.",
            )


def _schema_by_name(
    openapi_schema: Mapping[str, object],
    schema_name: str,
) -> Mapping[str, object]:
    components = openapi_schema.get("components")
    if not isinstance(components, Mapping):
        raise RuntimeError("API contract check failed: OpenAPI components are missing.")

    schemas = components.get("schemas")
    if not isinstance(schemas, Mapping):
        raise RuntimeError("API contract check failed: OpenAPI schemas are missing.")

    schema = schemas.get(schema_name)
    if not isinstance(schema, Mapping):
        raise RuntimeError(
            f"API contract check failed: {schema_name} schema is missing.",
        )

    return schema
