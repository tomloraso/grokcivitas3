from __future__ import annotations

import pytest

from civitas.application.school_trends.use_cases import MaterializeSchoolBenchmarksUseCase


class FakeSchoolBenchmarkMaterializer:
    def __init__(self, *, result: int = 0, error: Exception | None = None) -> None:
        self._result = result
        self._error = error
        self.calls: list[tuple[str, tuple[str, ...] | None]] = []

    def materialize_all_metric_benchmarks(self) -> int:
        self.calls.append(("all", None))
        if self._error is not None:
            raise self._error
        return self._result

    def materialize_metric_benchmarks_for_urns(self, urns: tuple[str, ...]) -> int:
        self.calls.append(("urns", urns))
        if self._error is not None:
            raise self._error
        return self._result


class FakeSchoolProfileCacheInvalidator:
    def __init__(self) -> None:
        self.calls = 0

    def invalidate_school_profile_cache(self) -> None:
        self.calls += 1


def test_materialize_school_benchmarks_invalidates_profile_cache_after_full_rebuild() -> None:
    materializer = FakeSchoolBenchmarkMaterializer(result=42)
    invalidator = FakeSchoolProfileCacheInvalidator()
    use_case = MaterializeSchoolBenchmarksUseCase(
        school_benchmark_materializer=materializer,
        school_profile_cache_invalidator=invalidator,
    )

    result = use_case.execute()

    assert result == 42
    assert materializer.calls == [("all", None)]
    assert invalidator.calls == 1


def test_materialize_school_benchmarks_invalidates_profile_cache_after_targeted_rebuild() -> None:
    materializer = FakeSchoolBenchmarkMaterializer(result=3)
    invalidator = FakeSchoolProfileCacheInvalidator()
    use_case = MaterializeSchoolBenchmarksUseCase(
        school_benchmark_materializer=materializer,
        school_profile_cache_invalidator=invalidator,
    )

    result = use_case.execute(urns=(" 100001 ", "200002", "100001", "", "  "))

    assert result == 3
    assert materializer.calls == [("urns", ("100001", "200002"))]
    assert invalidator.calls == 1


def test_materialize_school_benchmarks_does_not_invalidate_profile_cache_on_failure() -> None:
    materializer = FakeSchoolBenchmarkMaterializer(error=RuntimeError("boom"))
    invalidator = FakeSchoolProfileCacheInvalidator()
    use_case = MaterializeSchoolBenchmarksUseCase(
        school_benchmark_materializer=materializer,
        school_profile_cache_invalidator=invalidator,
    )

    with pytest.raises(RuntimeError, match="boom"):
        use_case.execute()

    assert materializer.calls == [("all", None)]
    assert invalidator.calls == 0
