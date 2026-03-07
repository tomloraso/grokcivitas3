from fastapi.testclient import TestClient

from civitas.api.dependencies import get_school_compare_use_case
from civitas.api.main import app
from civitas.application.school_compare.dto import (
    SchoolCompareBenchmarkDto,
    SchoolCompareCellDto,
    SchoolCompareResponseDto,
    SchoolCompareRowDto,
    SchoolCompareSchoolDto,
    SchoolCompareSectionDto,
)
from civitas.application.school_compare.errors import (
    InvalidSchoolCompareParametersError,
    SchoolCompareDataUnavailableError,
    SchoolCompareNotFoundError,
)

client = TestClient(app)


class FakeGetSchoolCompareUseCase:
    def __init__(
        self,
        result: SchoolCompareResponseDto | None = None,
        error: Exception | None = None,
    ) -> None:
        self._result = result
        self._error = error
        self.calls: list[str] = []

    def execute(self, *, urns: str) -> SchoolCompareResponseDto:
        self.calls.append(urns)
        if self._error is not None:
            raise self._error
        if self._result is None:
            raise AssertionError("FakeGetSchoolCompareUseCase configured without result or error")
        return self._result


def setup_function() -> None:
    app.dependency_overrides.clear()


def teardown_function() -> None:
    app.dependency_overrides.clear()


def test_get_school_compare_returns_expected_contract() -> None:
    fake_use_case = FakeGetSchoolCompareUseCase(
        result=SchoolCompareResponseDto(
            schools=(
                SchoolCompareSchoolDto(
                    urn="100001",
                    name="Primary Example",
                    postcode="SW1A 1AA",
                    phase="Primary",
                    school_type="Community school",
                    age_range_label="Ages 4-11",
                ),
                SchoolCompareSchoolDto(
                    urn="200002",
                    name="Secondary Example",
                    postcode="SW1A 1AA",
                    phase="Secondary",
                    school_type="Community school",
                    age_range_label="Ages 11-18",
                ),
            ),
            sections=(
                SchoolCompareSectionDto(
                    key="inspection",
                    label="Inspection",
                    rows=(
                        SchoolCompareRowDto(
                            metric_key="ofsted_overall_effectiveness",
                            label="Latest Ofsted",
                            unit="text",
                            cells=(
                                SchoolCompareCellDto(
                                    urn="100001",
                                    value_text="Good",
                                    value_numeric=None,
                                    year_label=None,
                                    snapshot_date=None,
                                    availability="available",
                                    completeness_status="available",
                                    completeness_reason_code=None,
                                    benchmark=None,
                                ),
                                SchoolCompareCellDto(
                                    urn="200002",
                                    value_text="Has taken effective action",
                                    value_numeric=None,
                                    year_label=None,
                                    snapshot_date=None,
                                    availability="available",
                                    completeness_status="available",
                                    completeness_reason_code=None,
                                    benchmark=None,
                                ),
                            ),
                        ),
                    ),
                ),
                SchoolCompareSectionDto(
                    key="demographics",
                    label="Demographics",
                    rows=(
                        SchoolCompareRowDto(
                            metric_key="fsm_pct",
                            label="Free School Meals",
                            unit="percent",
                            cells=(
                                SchoolCompareCellDto(
                                    urn="100001",
                                    value_text="20.1%",
                                    value_numeric=20.1,
                                    year_label="2024/25",
                                    snapshot_date=None,
                                    availability="available",
                                    completeness_status="available",
                                    completeness_reason_code=None,
                                    benchmark=SchoolCompareBenchmarkDto(
                                        academic_year="2024/25",
                                        school_value=20.1,
                                        national_value=18.0,
                                        local_value=19.2,
                                        school_vs_national_delta=2.1,
                                        school_vs_local_delta=0.9,
                                        local_scope="local_authority_district",
                                        local_area_code="E09000033",
                                        local_area_label="Westminster",
                                    ),
                                ),
                                SchoolCompareCellDto(
                                    urn="200002",
                                    value_text="16.9%",
                                    value_numeric=16.9,
                                    year_label="2024/25",
                                    snapshot_date=None,
                                    availability="available",
                                    completeness_status="available",
                                    completeness_reason_code=None,
                                    benchmark=None,
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        )
    )
    app.dependency_overrides[get_school_compare_use_case] = lambda: fake_use_case

    response = client.get("/api/v1/schools/compare?urns=100001,200002")

    assert response.status_code == 200
    assert response.json() == {
        "schools": [
            {
                "urn": "100001",
                "name": "Primary Example",
                "postcode": "SW1A 1AA",
                "phase": "Primary",
                "type": "Community school",
                "age_range_label": "Ages 4-11",
            },
            {
                "urn": "200002",
                "name": "Secondary Example",
                "postcode": "SW1A 1AA",
                "phase": "Secondary",
                "type": "Community school",
                "age_range_label": "Ages 11-18",
            },
        ],
        "sections": [
            {
                "key": "inspection",
                "label": "Inspection",
                "rows": [
                    {
                        "metric_key": "ofsted_overall_effectiveness",
                        "label": "Latest Ofsted",
                        "unit": "text",
                        "cells": [
                            {
                                "urn": "100001",
                                "value_text": "Good",
                                "value_numeric": None,
                                "year_label": None,
                                "snapshot_date": None,
                                "availability": "available",
                                "completeness_status": "available",
                                "completeness_reason_code": None,
                                "benchmark": None,
                            },
                            {
                                "urn": "200002",
                                "value_text": "Has taken effective action",
                                "value_numeric": None,
                                "year_label": None,
                                "snapshot_date": None,
                                "availability": "available",
                                "completeness_status": "available",
                                "completeness_reason_code": None,
                                "benchmark": None,
                            },
                        ],
                    }
                ],
            },
            {
                "key": "demographics",
                "label": "Demographics",
                "rows": [
                    {
                        "metric_key": "fsm_pct",
                        "label": "Free School Meals",
                        "unit": "percent",
                        "cells": [
                            {
                                "urn": "100001",
                                "value_text": "20.1%",
                                "value_numeric": 20.1,
                                "year_label": "2024/25",
                                "snapshot_date": None,
                                "availability": "available",
                                "completeness_status": "available",
                                "completeness_reason_code": None,
                                "benchmark": {
                                    "academic_year": "2024/25",
                                    "school_value": 20.1,
                                    "national_value": 18.0,
                                    "local_value": 19.2,
                                    "school_vs_national_delta": 2.1,
                                    "school_vs_local_delta": 0.9,
                                    "local_scope": "local_authority_district",
                                    "local_area_code": "E09000033",
                                    "local_area_label": "Westminster",
                                },
                            },
                            {
                                "urn": "200002",
                                "value_text": "16.9%",
                                "value_numeric": 16.9,
                                "year_label": "2024/25",
                                "snapshot_date": None,
                                "availability": "available",
                                "completeness_status": "available",
                                "completeness_reason_code": None,
                                "benchmark": None,
                            },
                        ],
                    }
                ],
            },
        ],
    }
    assert fake_use_case.calls == ["100001,200002"]


def test_get_school_compare_returns_400_for_invalid_parameters() -> None:
    fake_use_case = FakeGetSchoolCompareUseCase(
        error=InvalidSchoolCompareParametersError("Compare requires unique URNs.")
    )
    app.dependency_overrides[get_school_compare_use_case] = lambda: fake_use_case

    response = client.get("/api/v1/schools/compare?urns=100001,100001")

    assert response.status_code == 400
    assert response.json() == {"detail": "Compare requires unique URNs."}


def test_get_school_compare_returns_404_for_unknown_urns() -> None:
    fake_use_case = FakeGetSchoolCompareUseCase(error=SchoolCompareNotFoundError(("999999",)))
    app.dependency_overrides[get_school_compare_use_case] = lambda: fake_use_case

    response = client.get("/api/v1/schools/compare?urns=100001,999999")

    assert response.status_code == 404
    assert response.json() == {"detail": "School with URN '999999' was not found."}


def test_get_school_compare_returns_503_when_datastore_is_unavailable() -> None:
    fake_use_case = FakeGetSchoolCompareUseCase(
        error=SchoolCompareDataUnavailableError("School compare datastore is unavailable.")
    )
    app.dependency_overrides[get_school_compare_use_case] = lambda: fake_use_case

    response = client.get("/api/v1/schools/compare?urns=100001,200002")

    assert response.status_code == 503
    assert response.json() == {"detail": "School compare datastore is unavailable."}
