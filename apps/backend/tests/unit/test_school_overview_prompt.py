from civitas.domain.school_summaries.models import SchoolOverviewContext, SummaryGenerationFeedback
from civitas.infrastructure.ai.prompt_templates import school_overview


def test_school_overview_prompt_renders_context_and_feedback() -> None:
    system_prompt, user_prompt = school_overview.render(
        _context(),
        feedback=SummaryGenerationFeedback(
            reason_codes=("word_count_too_short",),
            previous_text="Too short.",
        ),
    )

    assert school_overview.VERSION == "overview.v6"
    assert school_overview.TEMPERATURE == 0.1
    assert "neutral, factual 'About the school' overviews" in system_prompt
    assert "Anything shorter than 140 words is invalid." in system_prompt
    assert "Name: Test School" in user_prompt
    assert "URN:" not in user_prompt
    assert "Validation reason codes: word_count_too_short" in user_prompt


def _context() -> SchoolOverviewContext:
    return SchoolOverviewContext(
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
    )
