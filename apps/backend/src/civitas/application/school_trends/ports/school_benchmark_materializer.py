from collections.abc import Sequence
from typing import Protocol


class SchoolBenchmarkMaterializer(Protocol):
    def materialize_all_metric_benchmarks(self) -> int: ...

    def materialize_metric_benchmarks_for_urns(self, urns: Sequence[str]) -> int: ...
