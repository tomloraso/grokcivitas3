import pytest
from typer.testing import CliRunner

from civitas.cli.main import app
from civitas.infrastructure.pipelines.base import PipelineResult, PipelineRunStatus, PipelineSource


class FakePipelineRunner:
    def __init__(self, result: PipelineResult) -> None:
        self._result = result
        self.ran_source: str | None = None
        self.ran_source_resume = False
        self.ran_run_id: str | None = None
        self.ran_all = False

    def run_source(
        self,
        source: str,
        *,
        resume: bool = False,
        run_id: str | None = None,
    ) -> PipelineResult:
        self.ran_source = source
        self.ran_source_resume = resume
        self.ran_run_id = run_id
        return self._result

    def available_sources(self) -> tuple[str, ...]:
        return (
            "gias",
            "dfe_characteristics",
            "ofsted_latest",
            "ofsted_timeline",
            "ons_imd",
            "police_crime_context",
        )

    def run_all(self) -> dict[PipelineSource, PipelineResult]:
        self.ran_all = True
        return {PipelineSource.GIAS: self._result}

    def resume_run(self, run_id: str) -> tuple[PipelineSource, PipelineResult]:
        self.ran_run_id = run_id
        return PipelineSource.GIAS, self._result


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

    runner = CliRunner()
    result = runner.invoke(app, ["pipeline", "run", "--all"])

    assert result.exit_code == 0
    assert fake_runner.ran_all is True
    assert "gias: succeeded" in result.stdout.lower()


def test_pipeline_run_source_resume(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_runner = FakePipelineRunner(result=_result(PipelineRunStatus.SUCCEEDED))
    monkeypatch.setattr("civitas.cli.main.pipeline_runner", lambda: fake_runner)

    runner = CliRunner()
    result = runner.invoke(app, ["pipeline", "run", "--source", "gias", "--resume"])

    assert result.exit_code == 0
    assert fake_runner.ran_source == "gias"
    assert fake_runner.ran_source_resume is True


def test_pipeline_resume_command(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_runner = FakePipelineRunner(result=_result(PipelineRunStatus.SUCCEEDED))
    monkeypatch.setattr("civitas.cli.main.pipeline_runner", lambda: fake_runner)

    runner = CliRunner()
    run_id = "6f3f1a49-ecfb-4889-9efd-2913f6f821cc"
    result = runner.invoke(app, ["pipeline", "resume", "--run-id", run_id])

    assert result.exit_code == 0
    assert fake_runner.ran_run_id == run_id
    assert "gias: succeeded" in result.stdout.lower()
