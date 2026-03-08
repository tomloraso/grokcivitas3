import pytest
from typer.testing import CliRunner

from civitas.application.school_summaries.dto import SummaryGenerationResultDto
from civitas.cli.main import app
from civitas.infrastructure.pipelines.base import PipelineResult, PipelineRunStatus, PipelineSource


class FakePipelineRunner:
    def __init__(self, result: PipelineResult) -> None:
        self._result = result
        self.ran_source: str | None = None
        self.ran_source_resume = False
        self.ran_source_force_refresh = False
        self.ran_run_id: str | None = None
        self.ran_all = False
        self.ran_all_force_refresh = False

    def run_source(
        self,
        source: str,
        *,
        resume: bool = False,
        force_refresh: bool = False,
        run_id: str | None = None,
    ) -> PipelineResult:
        self.ran_source = source
        self.ran_source_resume = resume
        self.ran_source_force_refresh = force_refresh
        self.ran_run_id = run_id
        return self._result

    def available_sources(self) -> tuple[str, ...]:
        return (
            "gias",
            "dfe_characteristics",
            "dfe_attendance",
            "dfe_behaviour",
            "dfe_workforce",
            "dfe_performance",
            "ofsted_latest",
            "ofsted_timeline",
            "ons_imd",
            "police_crime_context",
        )

    def run_all(self, *, force_refresh: bool = False) -> dict[PipelineSource, PipelineResult]:
        self.ran_all = True
        self.ran_all_force_refresh = force_refresh
        return {PipelineSource.GIAS: self._result}

    def resume_run(self, run_id: str) -> tuple[PipelineSource, PipelineResult]:
        self.ran_run_id = run_id
        return PipelineSource.GIAS, self._result


class FakeGenerateSchoolSummariesUseCase:
    def __init__(self, result: SummaryGenerationResultDto) -> None:
        self._result = result
        self.calls: list[dict[str, object]] = []

    def execute(self, **kwargs: object) -> SummaryGenerationResultDto:
        self.calls.append(kwargs)
        return self._result


class FakeMaterializeSchoolBenchmarksUseCase:
    def __init__(self, result: int = 0) -> None:
        self._result = result
        self.calls: list[dict[str, object]] = []

    def execute(self, **kwargs: object) -> int:
        self.calls.append(kwargs)
        return self._result


def _result(status: PipelineRunStatus, error_message: str | None = None) -> PipelineResult:
    return PipelineResult(
        status=status,
        downloaded_rows=1,
        staged_rows=1,
        promoted_rows=1,
        rejected_rows=0,
        error_message=error_message,
    )


def test_pipeline_run_source_success(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_runner = FakePipelineRunner(result=_result(PipelineRunStatus.SUCCEEDED))
    monkeypatch.setattr("civitas.cli.main.pipeline_runner", lambda: fake_runner)

    runner = CliRunner()
    result = runner.invoke(app, ["pipeline", "run", "--source", "gias"])

    assert result.exit_code == 0
    assert fake_runner.ran_source == "gias"
    assert fake_runner.ran_source_resume is False
    assert fake_runner.ran_source_force_refresh is False
    assert "gias: succeeded" in result.stdout.lower()


def test_pipeline_run_source_is_case_insensitive(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_runner = FakePipelineRunner(result=_result(PipelineRunStatus.SUCCEEDED))
    monkeypatch.setattr("civitas.cli.main.pipeline_runner", lambda: fake_runner)

    runner = CliRunner()
    result = runner.invoke(app, ["pipeline", "run", "--source", "GIAS"])

    assert result.exit_code == 0
    assert fake_runner.ran_source == "gias"
    assert "gias: succeeded" in result.stdout.lower()


def test_pipeline_run_source_failure_returns_nonzero_exit_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_runner = FakePipelineRunner(
        result=_result(PipelineRunStatus.FAILED_QUALITY_GATE, error_message="stage failed")
    )
    monkeypatch.setattr("civitas.cli.main.pipeline_runner", lambda: fake_runner)

    runner = CliRunner()
    result = runner.invoke(app, ["pipeline", "run", "--source", "gias"])

    assert result.exit_code == 1
    assert "stage failed" in result.stdout.lower()


def test_pipeline_run_source_unavailable_returns_nonzero_exit_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_runner = FakePipelineRunner(
        result=_result(
            PipelineRunStatus.FAILED_SOURCE_UNAVAILABLE,
            error_message="gate_id=download_nonzero downloaded_rows=0",
        )
    )
    monkeypatch.setattr("civitas.cli.main.pipeline_runner", lambda: fake_runner)

    runner = CliRunner()
    result = runner.invoke(app, ["pipeline", "run", "--source", "gias"])

    assert result.exit_code == 1
    assert "failed_source_unavailable" in result.stdout.lower()


def test_pipeline_run_source_skipped_no_change_returns_zero_exit_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_runner = FakePipelineRunner(result=_result(PipelineRunStatus.SKIPPED_NO_CHANGE))
    monkeypatch.setattr("civitas.cli.main.pipeline_runner", lambda: fake_runner)

    runner = CliRunner()
    result = runner.invoke(app, ["pipeline", "run", "--source", "gias"])

    assert result.exit_code == 0
    assert "skipped_no_change" in result.stdout.lower()


def test_pipeline_run_dfe_source_success(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_runner = FakePipelineRunner(result=_result(PipelineRunStatus.SUCCEEDED))
    monkeypatch.setattr("civitas.cli.main.pipeline_runner", lambda: fake_runner)

    runner = CliRunner()
    result = runner.invoke(app, ["pipeline", "run", "--source", "dfe_characteristics"])

    assert result.exit_code == 0
    assert fake_runner.ran_source == "dfe_characteristics"
    assert "dfe_characteristics: succeeded" in result.stdout.lower()


def test_pipeline_run_ofsted_source_success(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_runner = FakePipelineRunner(result=_result(PipelineRunStatus.SUCCEEDED))
    monkeypatch.setattr("civitas.cli.main.pipeline_runner", lambda: fake_runner)

    runner = CliRunner()
    result = runner.invoke(app, ["pipeline", "run", "--source", "ofsted_latest"])

    assert result.exit_code == 0
    assert fake_runner.ran_source == "ofsted_latest"
    assert "ofsted_latest: succeeded" in result.stdout.lower()


def test_pipeline_run_dfe_attendance_source_success(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_runner = FakePipelineRunner(result=_result(PipelineRunStatus.SUCCEEDED))
    monkeypatch.setattr("civitas.cli.main.pipeline_runner", lambda: fake_runner)

    runner = CliRunner()
    result = runner.invoke(app, ["pipeline", "run", "--source", "dfe_attendance"])

    assert result.exit_code == 0
    assert fake_runner.ran_source == "dfe_attendance"
    assert "dfe_attendance: succeeded" in result.stdout.lower()


def test_pipeline_run_dfe_behaviour_source_success(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_runner = FakePipelineRunner(result=_result(PipelineRunStatus.SUCCEEDED))
    monkeypatch.setattr("civitas.cli.main.pipeline_runner", lambda: fake_runner)

    runner = CliRunner()
    result = runner.invoke(app, ["pipeline", "run", "--source", "dfe_behaviour"])

    assert result.exit_code == 0
    assert fake_runner.ran_source == "dfe_behaviour"
    assert "dfe_behaviour: succeeded" in result.stdout.lower()


def test_pipeline_run_dfe_workforce_source_success(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_runner = FakePipelineRunner(result=_result(PipelineRunStatus.SUCCEEDED))
    monkeypatch.setattr("civitas.cli.main.pipeline_runner", lambda: fake_runner)

    runner = CliRunner()
    result = runner.invoke(app, ["pipeline", "run", "--source", "dfe_workforce"])

    assert result.exit_code == 0
    assert fake_runner.ran_source == "dfe_workforce"
    assert "dfe_workforce: succeeded" in result.stdout.lower()


def test_pipeline_run_dfe_performance_source_success(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_runner = FakePipelineRunner(result=_result(PipelineRunStatus.SUCCEEDED))
    monkeypatch.setattr("civitas.cli.main.pipeline_runner", lambda: fake_runner)

    runner = CliRunner()
    result = runner.invoke(app, ["pipeline", "run", "--source", "dfe_performance"])

    assert result.exit_code == 0
    assert fake_runner.ran_source == "dfe_performance"
    assert "dfe_performance: succeeded" in result.stdout.lower()


def test_pipeline_run_ofsted_timeline_source_success(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_runner = FakePipelineRunner(result=_result(PipelineRunStatus.SUCCEEDED))
    monkeypatch.setattr("civitas.cli.main.pipeline_runner", lambda: fake_runner)

    runner = CliRunner()
    result = runner.invoke(app, ["pipeline", "run", "--source", "ofsted_timeline"])

    assert result.exit_code == 0
    assert fake_runner.ran_source == "ofsted_timeline"
    assert "ofsted_timeline: succeeded" in result.stdout.lower()


def test_pipeline_run_ons_imd_source_success(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_runner = FakePipelineRunner(result=_result(PipelineRunStatus.SUCCEEDED))
    monkeypatch.setattr("civitas.cli.main.pipeline_runner", lambda: fake_runner)

    runner = CliRunner()
    result = runner.invoke(app, ["pipeline", "run", "--source", "ons_imd"])

    assert result.exit_code == 0
    assert fake_runner.ran_source == "ons_imd"
    assert "ons_imd: succeeded" in result.stdout.lower()


def test_pipeline_run_police_crime_context_source_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_runner = FakePipelineRunner(result=_result(PipelineRunStatus.SUCCEEDED))
    monkeypatch.setattr("civitas.cli.main.pipeline_runner", lambda: fake_runner)

    runner = CliRunner()
    result = runner.invoke(app, ["pipeline", "run", "--source", "police_crime_context"])

    assert result.exit_code == 0
    assert fake_runner.ran_source == "police_crime_context"
    assert "police_crime_context: succeeded" in result.stdout.lower()


def test_pipeline_run_all(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_runner = FakePipelineRunner(result=_result(PipelineRunStatus.SUCCEEDED))
    monkeypatch.setattr("civitas.cli.main.pipeline_runner", lambda: fake_runner)
    monkeypatch.setattr(
        "civitas.cli.main.app_settings",
        lambda: type("Settings", (), {"ai": type("Ai", (), {"enabled": False})()})(),
    )

    runner = CliRunner()
    result = runner.invoke(app, ["pipeline", "run", "--all"])

    assert result.exit_code == 0
    assert fake_runner.ran_all is True
    assert fake_runner.ran_all_force_refresh is False
    assert "gias: succeeded" in result.stdout.lower()


def test_pipeline_run_source_resume(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_runner = FakePipelineRunner(result=_result(PipelineRunStatus.SUCCEEDED))
    monkeypatch.setattr("civitas.cli.main.pipeline_runner", lambda: fake_runner)

    runner = CliRunner()
    result = runner.invoke(app, ["pipeline", "run", "--source", "gias", "--resume"])

    assert result.exit_code == 0
    assert fake_runner.ran_source == "gias"
    assert fake_runner.ran_source_resume is True


def test_pipeline_run_source_force_refresh(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_runner = FakePipelineRunner(result=_result(PipelineRunStatus.SUCCEEDED))
    monkeypatch.setattr("civitas.cli.main.pipeline_runner", lambda: fake_runner)

    runner = CliRunner()
    result = runner.invoke(app, ["pipeline", "run", "--source", "gias", "--force-refresh"])

    assert result.exit_code == 0
    assert fake_runner.ran_source == "gias"
    assert fake_runner.ran_source_force_refresh is True


def test_pipeline_run_all_force_refresh(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_runner = FakePipelineRunner(result=_result(PipelineRunStatus.SUCCEEDED))
    monkeypatch.setattr("civitas.cli.main.pipeline_runner", lambda: fake_runner)
    monkeypatch.setattr(
        "civitas.cli.main.app_settings",
        lambda: type("Settings", (), {"ai": type("Ai", (), {"enabled": False})()})(),
    )

    runner = CliRunner()
    result = runner.invoke(app, ["pipeline", "run", "--all", "--force-refresh"])

    assert result.exit_code == 0
    assert fake_runner.ran_all is True
    assert fake_runner.ran_all_force_refresh is True


def test_pipeline_run_resume_rejects_force_refresh(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_runner = FakePipelineRunner(result=_result(PipelineRunStatus.SUCCEEDED))
    monkeypatch.setattr("civitas.cli.main.pipeline_runner", lambda: fake_runner)

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["pipeline", "run", "--source", "gias", "--resume", "--force-refresh"],
    )

    assert result.exit_code == 2
    assert fake_runner.ran_source is None


def test_pipeline_resume_command(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_runner = FakePipelineRunner(result=_result(PipelineRunStatus.SUCCEEDED))
    monkeypatch.setattr("civitas.cli.main.pipeline_runner", lambda: fake_runner)

    runner = CliRunner()
    run_id = "6f3f1a49-ecfb-4889-9efd-2913f6f821cc"
    result = runner.invoke(app, ["pipeline", "resume", "--run-id", run_id])

    assert result.exit_code == 0
    assert fake_runner.ran_run_id == run_id
    assert "gias: succeeded" in result.stdout.lower()


def test_pipeline_materialize_benchmarks_for_all(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_use_case = FakeMaterializeSchoolBenchmarksUseCase(result=225)
    monkeypatch.setattr(
        "civitas.cli.main.materialize_school_benchmarks_use_case",
        lambda: fake_use_case,
    )

    result = CliRunner().invoke(app, ["pipeline", "materialize-benchmarks", "--all"])

    assert result.exit_code == 0
    assert fake_use_case.calls == [{}]
    assert "materialized 225 benchmark rows" in result.stdout.lower()


def test_pipeline_materialize_benchmarks_for_specific_urns(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_use_case = FakeMaterializeSchoolBenchmarksUseCase(result=450)
    monkeypatch.setattr(
        "civitas.cli.main.materialize_school_benchmarks_use_case",
        lambda: fake_use_case,
    )

    result = CliRunner().invoke(
        app,
        [
            "pipeline",
            "materialize-benchmarks",
            "--urn",
            "100001",
            "--urn",
            "200002",
        ],
    )

    assert result.exit_code == 0
    assert fake_use_case.calls == [{"urns": ["100001", "200002"]}]
    assert "materialized 450 benchmark rows" in result.stdout.lower()


def test_pipeline_materialize_benchmarks_requires_scope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_use_case = FakeMaterializeSchoolBenchmarksUseCase(result=0)
    monkeypatch.setattr(
        "civitas.cli.main.materialize_school_benchmarks_use_case",
        lambda: fake_use_case,
    )

    result = CliRunner().invoke(app, ["pipeline", "materialize-benchmarks"])

    assert result.exit_code == 2
    assert fake_use_case.calls == []


def test_pipeline_run_all_triggers_ai_generation_when_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_runner = FakePipelineRunner(result=_result(PipelineRunStatus.SUCCEEDED))
    fake_overview = FakeGenerateSchoolSummariesUseCase(result=_summary_generation_result())
    fake_analyst = FakeGenerateSchoolSummariesUseCase(result=_summary_generation_result())
    monkeypatch.setattr("civitas.cli.main.pipeline_runner", lambda: fake_runner)
    monkeypatch.setattr(
        "civitas.cli.main.app_settings",
        lambda: type("Settings", (), {"ai": type("Ai", (), {"enabled": True})()})(),
    )
    monkeypatch.setattr(
        "civitas.cli.main.submit_school_overview_batches_use_case",
        lambda: fake_overview,
    )
    monkeypatch.setattr(
        "civitas.cli.main.submit_school_analyst_batches_use_case",
        lambda: fake_analyst,
    )

    result = CliRunner().invoke(app, ["pipeline", "run", "--all"])

    assert result.exit_code == 0
    assert fake_overview.calls == [{"trigger": "pipeline"}]
    assert fake_analyst.calls == [{"trigger": "pipeline"}]
    assert "ai[overview]" in result.stdout
    assert "ai[analyst]" in result.stdout


def test_pipeline_run_source_does_not_trigger_ai_generation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_runner = FakePipelineRunner(result=_result(PipelineRunStatus.SUCCEEDED))
    fake_overview = FakeGenerateSchoolSummariesUseCase(result=_summary_generation_result())
    fake_analyst = FakeGenerateSchoolSummariesUseCase(result=_summary_generation_result())
    monkeypatch.setattr("civitas.cli.main.pipeline_runner", lambda: fake_runner)
    monkeypatch.setattr(
        "civitas.cli.main.app_settings",
        lambda: type("Settings", (), {"ai": type("Ai", (), {"enabled": True})()})(),
    )
    monkeypatch.setattr(
        "civitas.cli.main.submit_school_overview_batches_use_case",
        lambda: fake_overview,
    )
    monkeypatch.setattr(
        "civitas.cli.main.submit_school_analyst_batches_use_case",
        lambda: fake_analyst,
    )

    result = CliRunner().invoke(app, ["pipeline", "run", "--source", "gias"])

    assert result.exit_code == 0
    assert fake_overview.calls == []
    assert fake_analyst.calls == []


def test_pipeline_run_all_returns_nonzero_when_ai_generation_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_runner = FakePipelineRunner(result=_result(PipelineRunStatus.SUCCEEDED))
    fake_overview = FakeGenerateSchoolSummariesUseCase(
        result=_summary_generation_result(validation_failed_count=1, status="partial")
    )
    fake_analyst = FakeGenerateSchoolSummariesUseCase(result=_summary_generation_result())
    monkeypatch.setattr("civitas.cli.main.pipeline_runner", lambda: fake_runner)
    monkeypatch.setattr(
        "civitas.cli.main.app_settings",
        lambda: type("Settings", (), {"ai": type("Ai", (), {"enabled": True})()})(),
    )
    monkeypatch.setattr(
        "civitas.cli.main.submit_school_overview_batches_use_case",
        lambda: fake_overview,
    )
    monkeypatch.setattr(
        "civitas.cli.main.submit_school_analyst_batches_use_case",
        lambda: fake_analyst,
    )

    result = CliRunner().invoke(app, ["pipeline", "run", "--all"])

    assert result.exit_code == 1
    assert "validation_failed=1" in result.stdout


def _summary_generation_result(
    *,
    validation_failed_count: int = 0,
    status: str = "succeeded",
) -> SummaryGenerationResultDto:
    from uuid import UUID

    return SummaryGenerationResultDto(
        run_id=UUID("6f3f1a49-ecfb-4889-9efd-2913f6f821cc"),
        requested_count=1,
        pending_count=1 if validation_failed_count == 0 and status == "running" else 0,
        succeeded_count=1 if validation_failed_count == 0 else 0,
        generation_failed_count=0,
        validation_failed_count=validation_failed_count,
        skipped_current_count=0,
        status=status,
    )
