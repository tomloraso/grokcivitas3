from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Protocol, TypeVar
from uuid import UUID


class PipelineSource(str, Enum):
    GIAS = "gias"
    DFE_CHARACTERISTICS = "dfe_characteristics"
    DFE_ATTENDANCE = "dfe_attendance"
    DFE_BEHAVIOUR = "dfe_behaviour"
    DFE_WORKFORCE = "dfe_workforce"
    DFE_PERFORMANCE = "dfe_performance"
    SCHOOL_ADMISSIONS = "school_admissions"
    SCHOOL_FINANCIAL_BENCHMARKS = "school_financial_benchmarks"
    OFSTED_LATEST = "ofsted_latest"
    OFSTED_TIMELINE = "ofsted_timeline"
    ONS_IMD = "ons_imd"
    UK_HOUSE_PRICES = "uk_house_prices"
    POLICE_CRIME_CONTEXT = "police_crime_context"


class PipelineRunStatus(str, Enum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    SKIPPED_NO_CHANGE = "skipped_no_change"
    FAILED_SOURCE_UNAVAILABLE = "failed_source_unavailable"
    FAILED_QUALITY_GATE = "failed_quality_gate"
    FAILED = "failed"

    def is_hard_failure(self) -> bool:
        return self in {
            PipelineRunStatus.FAILED_SOURCE_UNAVAILABLE,
            PipelineRunStatus.FAILED_QUALITY_GATE,
            PipelineRunStatus.FAILED,
        }


@dataclass(frozen=True)
class StageResult:
    staged_rows: int
    rejected_rows: int = 0
    contract_version: str | None = None


class PipelineStep(str, Enum):
    DOWNLOAD = "download"
    STAGE = "stage"
    PROMOTE = "promote"


class PipelineCheckpointStatus(str, Enum):
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class PipelineCheckpoint:
    run_id: UUID
    source: PipelineSource
    step: PipelineStep
    status: PipelineCheckpointStatus
    attempts: int
    retryable: bool
    payload: dict[str, Any]
    error_message: str | None = None


@dataclass(frozen=True)
class PipelineQualityConfig:
    max_reject_ratio: float = 1.0

    def __post_init__(self) -> None:
        if self.max_reject_ratio < 0.0 or self.max_reject_ratio > 1.0:
            raise ValueError("max_reject_ratio must be between 0.0 and 1.0.")


@dataclass(frozen=True)
class PipelineRunContext:
    run_id: UUID
    source: PipelineSource
    started_at: datetime
    bronze_root: Path
    stage_chunk_size: int = 1000
    promote_chunk_size: int = 1000
    http_timeout_seconds: float = 60.0

    @property
    def bronze_source_path(self) -> Path:
        return self.bronze_root / self.source.value / self.started_at.date().isoformat()

    def __post_init__(self) -> None:
        if self.stage_chunk_size <= 0:
            raise ValueError("stage_chunk_size must be greater than 0.")
        if self.promote_chunk_size <= 0:
            raise ValueError("promote_chunk_size must be greater than 0.")
        if self.http_timeout_seconds <= 0:
            raise ValueError("http_timeout_seconds must be greater than 0.")


@dataclass(frozen=True)
class PipelineResult:
    status: PipelineRunStatus
    downloaded_rows: int = 0
    staged_rows: int = 0
    promoted_rows: int = 0
    rejected_rows: int = 0
    contract_version: str | None = None
    error_message: str | None = None


class Pipeline(Protocol):
    source: PipelineSource

    def download(self, context: PipelineRunContext) -> int: ...

    def stage(self, context: PipelineRunContext) -> StageResult: ...

    def promote(self, context: PipelineRunContext) -> int: ...


class PipelineSourceLock(Protocol):
    def acquire(self, *, source: PipelineSource, run_id: UUID) -> bool: ...

    def release(self, *, source: PipelineSource, run_id: UUID) -> None: ...


@dataclass(frozen=True)
class PipelineRetryPolicy:
    max_retries: int = 0
    backoff_seconds: float = 0.5
    jitter_factor: float = 0.2

    def __post_init__(self) -> None:
        if self.max_retries < 0:
            raise ValueError("max_retries must be >= 0.")
        if self.backoff_seconds <= 0:
            raise ValueError("backoff_seconds must be > 0.")
        if self.jitter_factor < 0:
            raise ValueError("jitter_factor must be >= 0.")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


_T = TypeVar("_T")


def chunked(items: list[_T], chunk_size: int) -> list[list[_T]]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0.")
    return [items[index : index + chunk_size] for index in range(0, len(items), chunk_size)]
