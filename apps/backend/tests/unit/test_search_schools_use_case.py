from __future__ import annotations

from civitas.application.schools.dto import (
    PostcodeSchoolSearchAcademicMetricDto,
    PostcodeSchoolSearchItemDto,
    PostcodeSchoolSearchLatestOfstedDto,
    SchoolNameSearchItemDto,
)
from civitas.application.schools.errors import InvalidSchoolSearchParametersError
from civitas.application.schools.use_cases import (
    DEFAULT_RADIUS_MILES,
    DEFAULT_SORT,
    SearchSchoolsByPostcodeUseCase,
)
from civitas.domain.schools.models import PostcodeCoordinates


class FakePostcodeResolver:
    def __init__(self, coordinates: PostcodeCoordinates) -> None:
        self._coordinates = coordinates
        self.received_postcodes: list[str] = []

    def resolve(self, postcode: str) -> PostcodeCoordinates:
        self.received_postcodes.append(postcode)
        return self._coordinates


class FakeSchoolSearchRepository:
    def __init__(
        self,
        postcode_results: list[PostcodeSchoolSearchItemDto] | None = None,
        name_results: list[SchoolNameSearchItemDto] | None = None,
    ) -> None:
        self._postcode_results = postcode_results or []
        self._name_results = name_results or []
        self.search_requests: list[tuple[float, float, float, tuple[str, ...], str]] = []

    def search_within_radius(
        self,
        *,
        center_lat: float,
        center_lng: float,
        radius_miles: float,
        phase_filters: tuple[str, ...],
        sort: str,
    ) -> list[PostcodeSchoolSearchItemDto]:
        self.search_requests.append((center_lat, center_lng, radius_miles, phase_filters, sort))
        return list(self._postcode_results)

    def search_by_name(
        self,
        *,
        name: str,
        limit: int,
    ) -> list[SchoolNameSearchItemDto]:
        return list(self._name_results)


def test_search_schools_uses_default_radius_and_normalized_postcode() -> None:
    resolver = FakePostcodeResolver(
        PostcodeCoordinates(
            postcode="SW1A 1AA",
            lat=51.501009,
            lng=-0.141588,
            lsoa_code="E01004736",
            lsoa="Westminster 018B",
            admin_district="Westminster",
        )
    )
    repository = FakeSchoolSearchRepository()
    use_case = SearchSchoolsByPostcodeUseCase(
        school_search_repository=repository,
        postcode_resolver=resolver,
    )

    result = use_case.execute(postcode=" sw1a1aa ")

    assert result.query.postcode == "SW1A 1AA"
    assert result.query.radius_miles == DEFAULT_RADIUS_MILES
    assert result.query.phases == ()
    assert result.query.sort == DEFAULT_SORT
    assert resolver.received_postcodes == ["SW1A 1AA"]
    assert repository.search_requests == [
        (51.501009, -0.141588, DEFAULT_RADIUS_MILES, (), DEFAULT_SORT)
    ]


def test_search_schools_rejects_invalid_radius() -> None:
    resolver = FakePostcodeResolver(
        PostcodeCoordinates(
            postcode="SW1A 1AA",
            lat=51.501009,
            lng=-0.141588,
            lsoa_code=None,
            lsoa=None,
            admin_district=None,
        )
    )
    repository = FakeSchoolSearchRepository()
    use_case = SearchSchoolsByPostcodeUseCase(
        school_search_repository=repository,
        postcode_resolver=resolver,
    )

    for radius in (0.0, -1.0, 25.1):
        try:
            use_case.execute(postcode="SW1A 1AA", radius_miles=radius)
        except InvalidSchoolSearchParametersError:
            continue
        raise AssertionError(
            f"Expected radius={radius} to raise InvalidSchoolSearchParametersError"
        )


def test_search_schools_rejects_academic_sort_without_single_phase_family() -> None:
    resolver = FakePostcodeResolver(
        PostcodeCoordinates(
            postcode="SW1A 1AA",
            lat=51.501009,
            lng=-0.141588,
            lsoa_code=None,
            lsoa=None,
            admin_district=None,
        )
    )
    repository = FakeSchoolSearchRepository()
    use_case = SearchSchoolsByPostcodeUseCase(
        school_search_repository=repository,
        postcode_resolver=resolver,
    )

    for phases in (None, ["primary", "secondary"]):
        try:
            use_case.execute(
                postcode="SW1A 1AA",
                radius_miles=5.0,
                phases=phases,
                sort="academic",
            )
        except InvalidSchoolSearchParametersError:
            continue
        raise AssertionError(
            "Expected academic sort without a single effective phase family to fail"
        )


def test_search_schools_normalizes_phase_filters_and_preserves_repository_order() -> None:
    resolver = FakePostcodeResolver(
        PostcodeCoordinates(
            postcode="SW1A 1AA",
            lat=51.501009,
            lng=-0.141588,
            lsoa_code=None,
            lsoa=None,
            admin_district=None,
        )
    )
    repository = FakeSchoolSearchRepository(
        postcode_results=[
            PostcodeSchoolSearchItemDto(
                urn="300003",
                name="Top Ranked Primary",
                school_type="Community school",
                phase="Primary",
                postcode="SW1A 1AA",
                lat=51.5,
                lng=-0.142,
                distance_miles=0.3,
                pupil_count=300,
                latest_ofsted=PostcodeSchoolSearchLatestOfstedDto(
                    label="Good",
                    sort_rank=2,
                    availability="published",
                ),
                academic_metric=PostcodeSchoolSearchAcademicMetricDto(
                    metric_key="ks2_combined_expected_pct",
                    label="KS2 expected standard",
                    display_value="68%",
                    sort_value=68.0,
                    availability="published",
                ),
            ),
            PostcodeSchoolSearchItemDto(
                urn="300001",
                name="Lower Ranked Primary",
                school_type="Community school",
                phase="Primary",
                postcode="SW1A 1AA",
                lat=51.5011,
                lng=-0.1416,
                distance_miles=0.1,
                pupil_count=250,
                latest_ofsted=PostcodeSchoolSearchLatestOfstedDto(
                    label="Outstanding",
                    sort_rank=1,
                    availability="published",
                ),
                academic_metric=PostcodeSchoolSearchAcademicMetricDto(
                    metric_key="ks2_combined_expected_pct",
                    label="KS2 expected standard",
                    display_value="61%",
                    sort_value=61.0,
                    availability="published",
                ),
            ),
        ]
    )
    use_case = SearchSchoolsByPostcodeUseCase(
        school_search_repository=repository,
        postcode_resolver=resolver,
    )

    result = use_case.execute(
        postcode="SW1A 1AA",
        radius_miles=5.0,
        phases=["PRIMARY", "primary"],
        sort="academic",
    )

    assert result.query.phases == ("primary",)
    assert result.query.sort == "academic"
    assert repository.search_requests == [(51.501009, -0.141588, 5.0, ("primary",), "academic")]
    assert [school.urn for school in result.schools] == ["300003", "300001"]
