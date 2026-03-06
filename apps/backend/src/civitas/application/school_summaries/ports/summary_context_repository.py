from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from civitas.domain.school_summaries.models import SchoolAnalystContext, SchoolOverviewContext


class SummaryContextRepository(Protocol):
    def list_overview_contexts(
        self,
        urns: Sequence[str] | None = None,
    ) -> list[SchoolOverviewContext]: ...

    def list_analyst_contexts(
        self,
        urns: Sequence[str] | None = None,
    ) -> list[SchoolAnalystContext]: ...
