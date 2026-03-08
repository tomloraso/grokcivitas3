from typing import Protocol


class SchoolSearchSummaryMaterializer(Protocol):
    def materialize_all_search_summaries(self) -> int: ...
