from datetime import date, datetime, timezone
from uuid import UUID

from civitas.domain.school_summaries.models import (
    MetricTrendPoint,
    SchoolAnalystContext,
    SchoolOverviewContext,
    SchoolSummary,
    SummaryGenerationFeedback,
    SummaryGenerationRun,
    SummaryGenerationRunItem,
)


def test_school_summary_models_capture_overview_state() -> None:
    generated_at = datetime(2026, 3, 6, 12, 0, tzinfo=timezone.utc)
    context = SchoolOverviewContext(
        urn="100001",
        name="Test School",
        phase="Secondary",
        school_type="Academy",
        status="Open",
        postcode="SW1A 1AA",
        website="https://example.test",
        telephone="020 7946 0999",
        head_name="Alex Smith",
        head_job_title="Headteacher",
        statutory_low_age=11,
        statutory_high_age=16,
        gender="Mixed",
        religious_character=None,
        admissions_policy="Not applicable",
        sixth_form="Does not have a sixth form",
        trust_name="Example Trust",
        la_name="Westminster",
        urban_rural="Urban city and town",
        pupil_count=900,
        capacity=1000,
        number_of_boys=450,
        number_of_girls=450,
        fsm_pct=18.2,
        eal_pct=22.4,
        sen_pct=14.0,
        ehcp_pct=3.1,
        progress_8=0.31,
        attainment_8=51.2,
        ks2_reading_met=None,
        ks2_maths_met=None,
        overall_effectiveness="Good",
        inspection_date=date(2024, 1, 10),
        imd_decile=7,
    )
    analyst_context = SchoolAnalystContext(
        **context.__dict__,
        fsm_pct_trend=(MetricTrendPoint(year="2024/25", value=18.2),),
        eal_pct_trend=(MetricTrendPoint(year="2024/25", value=22.4),),
        sen_pct_trend=(MetricTrendPoint(year="2024/25", value=14.0),),
        progress_8_trend=(MetricTrendPoint(year="2024/25", value=0.31),),
        attainment_8_trend=(MetricTrendPoint(year="2024/25", value=51.2),),
        quality_of_education="Good",
        behaviour_and_attitudes="Good",
        personal_development="Good",
        leadership_and_management="Good",
        imd_rank=4825,
        idaci_decile=2,
        total_incidents_12m=486,
    )
    summary = SchoolSummary(
        urn="100001",
        summary_kind="overview",
        text="A stored overview.",
        data_version_hash="hash-1",
        prompt_version="overview.v1",
        model_id="gpt-test",
        generated_at=generated_at,
        generation_duration_ms=120,
    )
    feedback = SummaryGenerationFeedback(
        reason_codes=("word_count_too_short",),
        previous_text="Too short.",
    )
    run = SummaryGenerationRun(
        id=UUID("6f3f1a49-ecfb-4889-9efd-2913f6f821cc"),
        summary_kind="overview",
        trigger="manual",
        requested_count=1,
        succeeded_count=1,
        generation_failed_count=0,
        validation_failed_count=0,
        started_at=generated_at,
        completed_at=generated_at,
        status="succeeded",
    )
    item = SummaryGenerationRunItem(
        run_id=run.id,
        urn="100001",
        status="succeeded",
        attempt_count=2,
        failure_reason_codes=(),
        completed_at=generated_at,
    )

    assert context.name == "Test School"
    assert analyst_context.total_incidents_12m == 486
    assert summary.model_id == "gpt-test"
    assert summary.summary_kind == "overview"
    assert feedback.reason_codes == ("word_count_too_short",)
    assert run.summary_kind == "overview"
    assert run.status == "succeeded"
    assert item.attempt_count == 2
