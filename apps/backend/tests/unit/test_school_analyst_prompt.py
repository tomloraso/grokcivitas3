from civitas.domain.school_summaries.models import (
    MetricTrendPoint,
    SchoolAnalystContext,
    SummaryGenerationFeedback,
)
from civitas.infrastructure.ai.prompt_templates import school_analyst


def test_school_analyst_prompt_renders_context_and_feedback() -> None:
    system_prompt, user_prompt = school_analyst.render(
        _context(),
        feedback=SummaryGenerationFeedback(
            reason_codes=("word_count_too_short",),
            previous_text="Too short.",
        ),
    )

    assert school_analyst.VERSION == "analyst.v4"
    assert school_analyst.TEMPERATURE == 0.2
    assert "You are Grok." in system_prompt
    assert "Performance trend summary" in user_prompt
    assert "URN:" not in user_prompt
    assert "Validation reason codes: word_count_too_short" in user_prompt


def _context() -> SchoolAnalystContext:
    return SchoolAnalystContext(
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
        inspection_date=None,
        imd_decile=7,
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
