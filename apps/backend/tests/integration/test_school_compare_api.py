from __future__ import annotations

from uuid import UUID

from fastapi.testclient import TestClient

from civitas.api.dependencies import get_current_session_use_case, get_school_compare_use_case
from civitas.api.main import app
from civitas.application.access.dto import SectionAccessDto
from civitas.application.identity.dto import CurrentSessionDto
from civitas.application.school_compare.dto import (
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


class FakeCurrentSessionUseCase:
    def execute(self, *, session_token: str | None) -> CurrentSessionDto:
        return CurrentSessionDto.anonymous(reason="missing")


class FakeGetSchoolCompareUseCase:
    def __init__(
        self,
        result: SchoolCompareResponseDto | None = None,
        error: Exception | None = None,
    ) -> None:
        self._result = result
        self._error = error
        self.calls: list[tuple[str, str | None]] = []

    def execute(
        self,
        *,
        urns: str,
        viewer_user_id: UUID | None = None,
    ) -> SchoolCompareResponseDto:
        self.calls.append((urns, viewer_user_id))
        if self._error is not None:
            raise self._error
        if self._result is None:
            raise AssertionError("FakeGetSchoolCompareUseCase configured without result or error")
        return self._result


def setup_function() -> None:
    app.dependency_overrides.clear()
    app.dependency_overrides[get_current_session_use_case] = lambda: FakeCurrentSessionUseCase()


def teardown_function() -> None:
    app.dependency_overrides.clear()


def test_get_school_compare_returns_expected_contract() -> None:
    fake_use_case = FakeGetSchoolCompareUseCase(
        result=SchoolCompareResponseDto(
            access=SectionAccessDto(
                state="locked",
                capability_key="premium_comparison",
                reason_code="anonymous_user",
                product_codes=("premium_launch",),
                requires_auth=True,
                requires_purchase=False,
            ),
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
    payload = response.json()
    assert payload["access"] == {
        "state": "locked",
        "capability_key": "premium_comparison",
        "reason_code": "anonymous_user",
        "product_codes": ["premium_launch"],
        "requires_auth": True,
        "requires_purchase": False,
        "school_name": None,
    }
    assert payload["schools"][0]["urn"] == "100001"
    assert payload["sections"][0]["rows"][0]["metric_key"] == "ofsted_overall_effectiveness"
    assert fake_use_case.calls == [("100001,200002", None)]


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
