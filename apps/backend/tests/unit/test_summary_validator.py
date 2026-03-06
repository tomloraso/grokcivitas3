from dataclasses import replace
from datetime import date

from civitas.domain.school_summaries.models import (
    MetricTrendPoint,
    SchoolAnalystContext,
    SchoolOverviewContext,
)
from civitas.domain.school_summaries.services import (
    validate_analyst_summary,
    validate_generated_summary,
)


def test_validate_generated_summary_accepts_grounded_overview() -> None:
    result = validate_generated_summary(_valid_text(), _context())

    assert result.is_valid is True
    assert result.reason_codes == ()


def test_validate_generated_summary_rejects_unpublished_progress_8_claim() -> None:
    text = (
        "Test School is a primary school in Westminster serving a diverse intake in an urban setting. "
        "Published pupil indicators include free school meals at 18.2%, English as an additional "
        "language at 22.4%, special educational needs at 14.0%, and EHCP at 3.1%. The latest "
        "summary states that Progress 8 is 0.31 even though that measure is not published for this "
        "school context. Ofsted rated the school Good after an inspection on 2024-01-10, and the "
        "school is part of Example Trust in an area with IMD decile 7."
    )

    result = validate_generated_summary(text, _primary_context_without_secondary_metrics())

    assert result.is_valid is False
    assert "references_missing_progress_8" in result.reason_codes


def test_validate_generated_summary_allows_month_year_date_phrase() -> None:
    text = (
        "Test School is an open secondary academy in Westminster for pupils aged 11 to 16. "
        "It operates in an urban city and town setting and has about 900 pupils on roll against "
        "reported capacity of 1,000, with an even split between boys and girls. Published pupil "
        "indicators show free school meals at 18.2%, English as an additional language at 22.4%, "
        "special educational needs at 14.0%, and EHCP at 3.1%. The latest published performance "
        "figures show Progress 8 at 0.31 and Attainment 8 at 51.2. Ofsted rated the school Good "
        "in January 2024. The school is part of Example Trust, does not have a sixth form, and "
        "sits in an area with IMD decile 7 according to the available context used to generate "
        "this overview."
    )

    result = validate_generated_summary(text, _context())

    assert result.is_valid is True
    assert result.reason_codes == ()


def test_validate_generated_summary_allows_explicit_metric_absence_disclosure() -> None:
    text = (
        "Test School is a primary school in Westminster serving pupils aged 5 to 11 in an urban "
        "setting. It has about 420 pupils on roll, with free school meals at 18.2%, English as "
        "an additional language at 22.4%, special educational needs at 14.0%, and EHCP at 3.1%. "
        "Progress 8 is not published for this school context, so the clearest published outcome "
        "signals are Key Stage 2 reading at 79% and maths at 83%. Ofsted rated the school Good "
        "in January 2024, and it is part of Example Trust in an area with IMD decile 7."
    )

    result = validate_generated_summary(text, _primary_context_without_secondary_metrics())

    assert result.is_valid is True
    assert result.reason_codes == ()


def test_validate_generated_summary_rejects_unpublished_ofsted_claim() -> None:
    text = (
        "Test School is a 16 plus provider serving students in an urban setting. It remains open "
        "and offers post-16 education in Westminster. Ofsted rated the college Good in May 2024, "
        "and the latest inspection highlighted positive leadership and student support. Published "
        "performance data includes Attainment 8 at 12.1, while capacity and leadership details are "
        "not fully included in the current context."
    )

    result = validate_generated_summary(text, _post_16_context_without_ofsted())

    assert result.is_valid is False
    assert "references_missing_ofsted" in result.reason_codes


def test_validate_analyst_summary_accepts_grounded_analysis() -> None:
    result = validate_analyst_summary(_valid_analyst_text(), _analyst_context())

    assert result.is_valid is True
    assert result.reason_codes == ()


def test_validate_analyst_summary_rejects_recommendation_language() -> None:
    result = validate_analyst_summary(
        (
            "Test School shows a broadly steady published profile with Progress 8 at 0.31 and "
            "Attainment 8 at 51.2, while Ofsted rated the school Good on 2024-01-10. Published "
            "pupil indicators show FSM at 18.2%, EAL at 22.4%, SEN at 14.0%, and EHCP at 3.1%. "
            "The latest data suggests a balanced urban intake and a school operating below stated "
            "capacity, with no obvious single risk flag dominating the profile. Because the "
            "published indicators look relatively stable and the inspection signal is positive, "
            "parents should treat this as a strong all-round option in Westminster and should "
            "consider it ahead of many alternatives when comparing local schools."
        ),
        _analyst_context(),
    )

    assert result.is_valid is False
    assert "banned_phrase_detected" in result.reason_codes


def test_validate_analyst_summary_allows_unpublished_progress_8_statement() -> None:
    text = (
        "Test School has improved its inspection profile from Requires Improvement in 2018 to "
        "Good in June 2022, with strong judgements across quality of education, behaviour, "
        "personal development, and leadership. Progress 8 remains unpublished for this school, "
        "so the clearest published secondary outcome signal is Attainment 8 at 34.9 alongside "
        "rising FSM from 24.9% to 31.0% and SEN from 11.1% to 16.7% over the recent published "
        "years. Local crime context remains elevated, but the inspection and intake trends point "
        "to a school that has stabilised despite tougher pressures. Capacity remains well above "
        "current roll, which adds a further signal of operating challenge, but the published "
        "inspection evidence still points to a school with a more secure quality baseline than "
        "its earlier rating suggested."
    )

    result = validate_analyst_summary(text, _analyst_context_without_progress_8())

    assert result.is_valid is True
    assert result.reason_codes == ()


def test_validate_analyst_summary_allows_full_date_phrase() -> None:
    text = (
        "Test School presents a broadly steady published profile rather than a sharply uneven one. "
        "The latest secondary performance figures show Progress 8 at 0.31 and Attainment 8 at "
        "51.2, and the available trend points indicate both measures have moved up over the recent "
        "published years rather than slipping back. Ofsted rated the school Good on 10 January "
        "2024, while the current sub-judgements for quality of education, behaviour and attitudes, "
        "personal development, and leadership and management are also Good, which gives a "
        "consistent inspection signal. Published pupil indicators show FSM at 18.2%, EAL at "
        "22.4%, SEN at 14.0%, and EHCP at 3.1%, suggesting a mixed intake with a moderate level of "
        "additional need in the available data. The school operates in an urban Westminster "
        "setting, is part of Example Trust, and sits in IMD decile 7 with 486 incidents recorded "
        "across the latest 12 months of local crime context. Overall, the current dataset points "
        "to a balanced school profile with credible strengths and no single dominant warning signal "
        "in the published evidence."
    )

    result = validate_analyst_summary(text, _analyst_context())

    assert result.is_valid is True
    assert result.reason_codes == ()


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
        inspection_date=date(2024, 1, 10),
        imd_decile=7,
    )


def _valid_text() -> str:
    return (
        "Test School is an open secondary academy in Westminster for pupils aged 11 to 16. "
        "It operates in an urban city and town setting and has about 900 pupils on roll against "
        "reported capacity of 1,000, with an even split between boys and girls. Published pupil "
        "indicators show free school meals at 18.2%, English as an additional language at 22.4%, "
        "special educational needs at 14.0%, and EHCP at 3.1%. The latest published performance "
        "figures show Progress 8 at 0.31 and Attainment 8 at 51.2. Ofsted rated the school Good "
        "following an inspection on 2024-01-10. The school is part of Example Trust, does not "
        "have a sixth form, and sits in an area with IMD decile 7 according to the available "
        "context used to generate this overview."
    )


def _primary_context_without_secondary_metrics() -> SchoolOverviewContext:
    return replace(
        _context(),
        phase="Primary",
        statutory_low_age=5,
        statutory_high_age=11,
        progress_8=None,
        attainment_8=None,
        ks2_reading_met=79.0,
        ks2_maths_met=83.0,
    )


def _post_16_context_without_ofsted() -> SchoolOverviewContext:
    return replace(
        _context(),
        phase="16 plus",
        school_type="Further education",
        statutory_low_age=16,
        statutory_high_age=None,
        progress_8=None,
        overall_effectiveness=None,
        inspection_date=None,
    )


def _analyst_context() -> SchoolAnalystContext:
    return SchoolAnalystContext(
        **_context().__dict__,
        fsm_pct_trend=(
            MetricTrendPoint(year="2022/23", value=19.1),
            MetricTrendPoint(year="2023/24", value=18.7),
            MetricTrendPoint(year="2024/25", value=18.2),
        ),
        eal_pct_trend=(
            MetricTrendPoint(year="2022/23", value=21.8),
            MetricTrendPoint(year="2023/24", value=22.0),
            MetricTrendPoint(year="2024/25", value=22.4),
        ),
        sen_pct_trend=(
            MetricTrendPoint(year="2022/23", value=13.3),
            MetricTrendPoint(year="2023/24", value=13.7),
            MetricTrendPoint(year="2024/25", value=14.0),
        ),
        progress_8_trend=(
            MetricTrendPoint(year="2022/23", value=0.12),
            MetricTrendPoint(year="2023/24", value=0.21),
            MetricTrendPoint(year="2024/25", value=0.31),
        ),
        attainment_8_trend=(
            MetricTrendPoint(year="2022/23", value=49.6),
            MetricTrendPoint(year="2023/24", value=50.5),
            MetricTrendPoint(year="2024/25", value=51.2),
        ),
        quality_of_education="Good",
        behaviour_and_attitudes="Good",
        personal_development="Good",
        leadership_and_management="Good",
        imd_rank=4825,
        idaci_decile=2,
        total_incidents_12m=486,
    )


def _analyst_context_without_progress_8() -> SchoolAnalystContext:
    return replace(
        _analyst_context(),
        progress_8=None,
        progress_8_trend=(),
        attainment_8=34.9,
        attainment_8_trend=(
            MetricTrendPoint(year="2022/23", value=33.5),
            MetricTrendPoint(year="2023/24", value=34.2),
            MetricTrendPoint(year="2024/25", value=34.9),
        ),
        inspection_date=date(2022, 6, 10),
    )


def _valid_analyst_text() -> str:
    return (
        "Test School presents a broadly steady published profile rather than a sharply uneven one. "
        "The latest secondary performance figures show Progress 8 at 0.31 and Attainment 8 at "
        "51.2, and the available trend points indicate both measures have moved up over the recent "
        "published years rather than slipping back. Ofsted rated the school Good following an "
        "inspection on 2024-01-10, while the current sub-judgements for quality of education, "
        "behaviour and attitudes, personal development, and leadership and management are also "
        "Good, which gives a consistent inspection signal. Published pupil indicators show FSM at "
        "18.2%, EAL at 22.4%, SEN at 14.0%, and EHCP at 3.1%, suggesting a mixed intake with a "
        "moderate level of additional need in the available data. The school operates in an urban "
        "Westminster setting, is part of Example Trust, and sits in IMD decile 7 with 486 incidents "
        "recorded across the latest 12 months of local crime context. Overall, the current dataset "
        "points to a balanced school profile with credible strengths and no single dominant warning "
        "signal in the published evidence."
    )
