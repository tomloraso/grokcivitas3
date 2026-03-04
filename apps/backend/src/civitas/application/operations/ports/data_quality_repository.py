from datetime import date, datetime
from typing import Protocol

from civitas.domain.operations.models import CoverageDrift, DataQualitySnapshot, PipelineRunHealth


class DataQualityRepository(Protocol):
    def collect_snapshots(
        self,
        *,
        snapshot_date: date,
        as_of: datetime,
    ) -> tuple[DataQualitySnapshot, ...]: ...

    def upsert_snapshots(self, snapshots: tuple[DataQualitySnapshot, ...]) -> None: ...

    def list_snapshots(self, *, snapshot_date: date) -> tuple[DataQualitySnapshot, ...]: ...

    def get_previous_snapshot(
        self,
        *,
        source: str,
        dataset: str,
        section: str,
        before_date: date,
    ) -> DataQualitySnapshot | None: ...

    def list_coverage_drifts(self, *, snapshot_date: date) -> tuple[CoverageDrift, ...]: ...

    def list_pipeline_run_health(self) -> tuple[PipelineRunHealth, ...]: ...
