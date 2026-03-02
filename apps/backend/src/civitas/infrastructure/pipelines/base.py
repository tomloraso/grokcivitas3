from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Protocol
from uuid import UUID


class PipelineSource(str, Enum):
    GIAS = "gias"
    DFE_CHARACTERISTICS = "dfe_characteristics"
    OFSTED_LATEST = "ofsted_latest"


class PipelineRunStatus(str, Enum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass(frozen=True)
class StageResult:
    staged_rows: int
    rejected_rows: int = 0


@dataclass(frozen=True)
class PipelineRunContext:
    run_id: UUID
    source: PipelineSource
    started_at: datetime
    bronze_root: Path

    @property
    def bronze_source_path(self) -> Path:
        return self.bronze_root / self.source.value / self.started_at.date().isoformat()


@dataclass(frozen=True)
class PipelineResult:
    status: PipelineRunStatus
    downloaded_rows: int = 0
    staged_rows: int = 0
    promoted_rows: int = 0
    rejected_rows: int = 0
    error_message: str | None = None


class Pipeline(Protocol):
    source: PipelineSource

    def download(self, context: PipelineRunContext) -> int: ...

    def stage(self, context: PipelineRunContext) -> StageResult: ...

    def promote(self, context: PipelineRunContext) -> int: ...


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
