from datetime import datetime, timezone
from uuid import UUID

import pytest
from typer.testing import CliRunner

from civitas.application.school_summaries.dto import SchoolSummaryDto, SummaryGenerationResultDto
from civitas.cli.main import app


class FakeGetSchoolSummaryUseCase:
    def __init__(self, result: SchoolSummaryDto | None) -> None:
        self.result = result
        self.calls: list[str] = []

    def execute(self, *, urn: str) -> SchoolSummaryDto | None:
        self.calls.append(urn)
        return self.result


class FakeGenerateSchoolSummariesUseCase:
    def __init__(self, result: SummaryGenerationResultDto | Exception) -> None:
        self.result = result
        self.calls: list[dict[str, object]] = []

    def execute(self, **kwargs: object) -> SummaryGenerationResultDto:
        self.calls.append(kwargs)
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


class FakePollSchoolSummaryBatchesUseCase:
    def __init__(self, results: tuple[SummaryGenerationResultDto, ...] | Exception) -> None:
        self.results = results
        self.calls: list[dict[str, object]] = []

    def execute(self, **kwargs: object) -> tuple[SummaryGenerationResultDto, ...]:
        self.calls.append(kwargs)
        if isinstance(self.results, Exception):
            raise self.results
        return self.results


def test_show_summary_prints_overview(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_use_case = FakeGetSchoolSummaryUseCase(
        SchoolSummaryDto(
            urn="100001",
            summary_kind="overview",
            text="Stored overview.",
            data_version_hash="hash-1",
            prompt_version="overview.v1",
            model_id="test-model",
            generated_at=datetime(2026, 3, 6, 12, 0, tzinfo=timezone.utc),
            generation_duration_ms=120,
        )
    )
    monkeypatch.setattr("civitas.cli.main.get_school_overview_use_case", lambda: fake_use_case)

    result = CliRunner().invoke(app, ["show-summary", "--urn", "100001"])

    assert result.exit_code == 0
    assert fake_use_case.calls == ["100001"]
    assert "overview | urn=100001" in result.stdout
    assert "Stored overview." in result.stdout


def test_show_summary_prints_analyst(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_use_case = FakeGetSchoolSummaryUseCase(
        SchoolSummaryDto(
            urn="100001",
            summary_kind="analyst",
            text="Stored analyst summary.",
            data_version_hash="hash-2",
            prompt_version="analyst.v1",
            model_id="test-model",
            generated_at=datetime(2026, 3, 6, 12, 5, tzinfo=timezone.utc),
            generation_duration_ms=150,
        )
    )
    monkeypatch.setattr("civitas.cli.main.get_school_analyst_use_case", lambda: fake_use_case)

    result = CliRunner().invoke(app, ["show-summary", "--type", "analyst", "--urn", "100001"])

    assert result.exit_code == 0
    assert fake_use_case.calls == ["100001"]
    assert "analyst | urn=100001" in result.stdout
    assert "Stored analyst summary." in result.stdout


def test_generate_summaries_runs_all_types_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_overview = FakeGenerateSchoolSummariesUseCase(
        SummaryGenerationResultDto(
            run_id=UUID("6f3f1a49-ecfb-4889-9efd-2913f6f821cc"),
            requested_count=1,
            pending_count=1,
            succeeded_count=1,
            generation_failed_count=0,
            validation_failed_count=0,
            skipped_current_count=0,
            status="running",
        )
    )
    fake_analyst = FakeGenerateSchoolSummariesUseCase(
        SummaryGenerationResultDto(
            run_id=UUID("3aa1d071-9312-43fd-a592-4a7d2cbe5d69"),
            requested_count=1,
            pending_count=1,
            succeeded_count=1,
            generation_failed_count=0,
            validation_failed_count=0,
            skipped_current_count=0,
            status="running",
        )
    )
    monkeypatch.setattr(
        "civitas.cli.main.submit_school_overview_batches_use_case",
        lambda: fake_overview,
    )
    monkeypatch.setattr(
        "civitas.cli.main.submit_school_analyst_batches_use_case",
        lambda: fake_analyst,
    )
    monkeypatch.setattr(
        "civitas.cli.main.app_settings",
        lambda: type("Settings", (), {"ai": type("Ai", (), {"enabled": True})()})(),
    )

    result = CliRunner().invoke(app, ["generate-summaries", "--urn", "100001"])

    assert result.exit_code == 0
    assert fake_overview.calls == [
        {
            "urns": ["100001"],
            "trigger": "manual",
            "force": False,
            "resume_run_id": None,
        }
    ]
    assert fake_analyst.calls == [
        {
            "urns": ["100001"],
            "trigger": "manual",
            "force": False,
            "resume_run_id": None,
        }
    ]
    assert "overview: run_id=" in result.stdout
    assert "analyst: run_id=" in result.stdout
    assert "pending=1" in result.stdout


def test_poll_summary_batches_prints_results(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_overview = FakePollSchoolSummaryBatchesUseCase(
        (
            SummaryGenerationResultDto(
                run_id=UUID("6f3f1a49-ecfb-4889-9efd-2913f6f821cc"),
                requested_count=2,
                pending_count=0,
                succeeded_count=2,
                generation_failed_count=0,
                validation_failed_count=0,
                skipped_current_count=0,
                status="succeeded",
            ),
        )
    )
    fake_analyst = FakePollSchoolSummaryBatchesUseCase(
        (
            SummaryGenerationResultDto(
                run_id=UUID("3aa1d071-9312-43fd-a592-4a7d2cbe5d69"),
                requested_count=2,
                pending_count=0,
                succeeded_count=2,
                generation_failed_count=0,
                validation_failed_count=0,
                skipped_current_count=0,
                status="succeeded",
            ),
        )
    )
    monkeypatch.setattr(
        "civitas.cli.main.poll_school_overview_batches_use_case",
        lambda: fake_overview,
    )
    monkeypatch.setattr(
        "civitas.cli.main.poll_school_analyst_batches_use_case",
        lambda: fake_analyst,
    )

    result = CliRunner().invoke(app, ["poll-summary-batches"])

    assert result.exit_code == 0
    assert fake_overview.calls == [{"run_id": None}]
    assert fake_analyst.calls == [{"run_id": None}]
    assert "pending=0" in result.stdout
    assert "overview: run_id=" in result.stdout
    assert "analyst: run_id=" in result.stdout


def test_generate_summaries_prints_runtime_error_without_traceback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_overview = FakeGenerateSchoolSummariesUseCase(
        RuntimeError("Grok batch API request failed: credits exhausted.")
    )
    monkeypatch.setattr(
        "civitas.cli.main.submit_school_overview_batches_use_case",
        lambda: fake_overview,
    )
    monkeypatch.setattr(
        "civitas.cli.main.app_settings",
        lambda: type("Settings", (), {"ai": type("Ai", (), {"enabled": True})()})(),
    )

    result = CliRunner().invoke(app, ["generate-summaries", "--type", "overview"])

    assert result.exit_code == 1
    assert "credits exhausted" in result.stdout
    assert "Traceback" not in result.stdout


def test_poll_summary_batches_prints_runtime_error_without_traceback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_overview = FakePollSchoolSummaryBatchesUseCase(
        RuntimeError("Grok batch API request failed: credits exhausted.")
    )
    monkeypatch.setattr(
        "civitas.cli.main.poll_school_overview_batches_use_case",
        lambda: fake_overview,
    )

    result = CliRunner().invoke(app, ["poll-summary-batches", "--type", "overview"])

    assert result.exit_code == 1
    assert "credits exhausted" in result.stdout
    assert "Traceback" not in result.stdout
