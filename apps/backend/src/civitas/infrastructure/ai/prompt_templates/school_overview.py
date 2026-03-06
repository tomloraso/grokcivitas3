from __future__ import annotations

from civitas.domain.school_summaries.models import (
    SchoolOverviewContext,
    SummaryGenerationFeedback,
)

VERSION = "overview.v5"
CONTEXT_TYPE = SchoolOverviewContext
TEMPERATURE = 0.1

SYSTEM_PROMPT = """You write neutral, factual 'About the school' overviews for Civitas parents.

Rules:
- Write 140-180 words in a single flowing paragraph.
- Use only the facts supplied in the user message.
- Include school type, religious character if any, age range, pupil numbers and capacity,
  postcode context, published leadership, admissions policy if published, Ofsted rating and
  date, and key demographics such as FSM, EAL, and SEN where available.
- Write in calm, welcoming, plain UK English.
- Do not analyse performance, trends, strengths, weaknesses, or compare with other schools.
- Never mention the URN or any internal identifier.
- Do not recommend, advise, speculate, or describe suitability.
- If a fact is not published in the input, omit it rather than saying it is not published or unavailable.
- Do not mention performance or inspection measures that are not published for this school.
- Output a single paragraph only.
"""


def render(
    context: SchoolOverviewContext,
    feedback: SummaryGenerationFeedback | None = None,
) -> tuple[str, str]:
    lines = [
        "School context:",
        f"- Name: {context.name}",
        f"- Phase: {_display(context.phase)}",
        f"- Type: {_display(context.school_type)}",
        f"- Status: {_display(context.status)}",
        f"- Postcode: {_display(context.postcode)}",
        f"- Headteacher / leader: {_display(context.head_name)}",
        f"- Head job title: {_display(context.head_job_title)}",
        f"- Age range: {_format_age_range(context.statutory_low_age, context.statutory_high_age)}",
        f"- Gender intake: {_display(context.gender)}",
        f"- Religious character: {_display(context.religious_character)}",
        f"- Admissions policy: {_display(context.admissions_policy)}",
        f"- Sixth form: {_display(context.sixth_form)}",
        f"- Trust / MAT: {_display(context.trust_name)}",
        f"- Local authority: {_display(context.la_name)}",
        f"- Settlement context: {_display(context.urban_rural)}",
        f"- Capacity: {_display_number(context.capacity)}",
        f"- Pupil count: {_display_number(context.pupil_count)}",
        f"- Boys on roll: {_display_number(context.number_of_boys)}",
        f"- Girls on roll: {_display_number(context.number_of_girls)}",
        f"- FSM percentage: {_display_pct(context.fsm_pct)}",
        f"- EAL percentage: {_display_pct(context.eal_pct)}",
        f"- SEN percentage: {_display_pct(context.sen_pct)}",
        f"- EHCP percentage: {_display_pct(context.ehcp_pct)}",
        f"- Progress 8: {_display_score(context.progress_8)}",
        f"- Attainment 8: {_display_score(context.attainment_8)}",
        f"- KS2 reading expected: {_display_pct(context.ks2_reading_met)}",
        f"- KS2 maths expected: {_display_pct(context.ks2_maths_met)}",
        f"- Ofsted overall effectiveness: {_display(context.overall_effectiveness)}",
        f"- Latest inspection date: {_display_date(context.inspection_date)}",
        f"- IMD decile: {_display_number(context.imd_decile)}",
        "",
        "Write a natural, factual 'About the school' paragraph that gives parents a clear picture",
        "of what the school is like.",
    ]

    if feedback is not None:
        lines.extend(
            [
                "",
                "The previous draft failed validation.",
                f"- Validation reason codes: {', '.join(feedback.reason_codes)}",
                f"- Previous invalid draft: {feedback.previous_text.strip()}",
                "Rewrite the summary so it fixes every validation issue.",
            ]
        )

    return SYSTEM_PROMPT, "\n".join(lines)


def _display(value: str | None) -> str:
    if value is None or not value.strip():
        return "Not published"
    return value.strip()


def _display_number(value: int | None) -> str:
    return "Not published" if value is None else f"{value:,}"


def _display_pct(value: float | None) -> str:
    return "Not published" if value is None else f"{value:.1f}%"


def _display_score(value: float | None) -> str:
    return "Not published" if value is None else f"{value:.2f}"


def _display_date(value: object) -> str:
    if value is None:
        return "Not published"
    return str(value)


def _format_age_range(low: int | None, high: int | None) -> str:
    if low is None and high is None:
        return "Not published"
    if low is None:
        return f"Up to age {high}"
    if high is None:
        return f"From age {low}"
    return f"Ages {low}-{high}"
