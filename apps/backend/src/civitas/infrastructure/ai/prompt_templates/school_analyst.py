from __future__ import annotations

from civitas.domain.school_summaries.models import (
    CrimeCategoryCount,
    InspectionHistoryPoint,
    MetricTrendPoint,
    SchoolAnalystContext,
    SummaryGenerationFeedback,
)

VERSION = "analyst.v4"
CONTEXT_TYPE = SchoolAnalystContext
TEMPERATURE = 0.2

SYSTEM_PROMPT = """You are Grok. Give parents a clear, truthful, analytical take on a school's performance using only the metrics provided.

Rules:
- Write 140-200 words in a single paragraph plus 2-3 short bullet highlights.
- Use only the facts supplied in the user message.
- Focus exclusively on what the numbers, dates, and trends actually show.
- Highlight strengths, areas to watch, and any notable patterns grounded in the published evidence.
- Use a curious, straightforward, no-fluff tone.
- Avoid repeating basic profile facts already covered in the school overview unless they materially
  help explain the analytical picture.
- Never mention the URN or any internal identifier.
- Do not recommend, advise, speculate, or describe suitability.
- If a fact is not published in the input, omit it rather than saying it is not published or unavailable.
- Do not mention performance or inspection measures that are not published for this school.
- Do not simply restate raw metrics; explain what the published evidence suggests.
- Output exactly one paragraph followed by 2-3 short bullet highlights.
- Do not invent missing data or use outside knowledge.
"""


def render(
    context: SchoolAnalystContext,
    feedback: SummaryGenerationFeedback | None = None,
) -> tuple[str, str]:
    lines = [
        "School metrics only (do not use any other information):",
        f"- Name: {context.name}",
        f"- Pupil count: {_display_number(context.pupil_count)}",
        f"- Capacity: {_display_number(context.capacity)}",
        f"- FSM percentage: {_display_pct(context.fsm_pct)}",
        f"- EAL percentage: {_display_pct(context.eal_pct)}",
        f"- SEN percentage: {_display_pct(context.sen_pct)}",
        f"- EHCP percentage: {_display_pct(context.ehcp_pct)}",
        f"- Progress 8: {_display_score(context.progress_8)}",
        f"- Attainment 8: {_display_score(context.attainment_8)}",
        f"- Ofsted overall effectiveness: {_display(context.overall_effectiveness)}",
        f"- Latest inspection date: {_display_date(context.inspection_date)}",
        f"- Quality of education: {_display(context.quality_of_education)}",
        f"- Behaviour and attitudes: {_display(context.behaviour_and_attitudes)}",
        f"- Personal development: {_display(context.personal_development)}",
        f"- Leadership and management: {_display(context.leadership_and_management)}",
        f"- IMD decile: {_display_number(context.imd_decile)}",
        f"- IMD rank: {_display_number(context.imd_rank)}",
        f"- IDACI decile: {_display_number(context.idaci_decile)}",
        f"- Total incidents in latest 12 months: {_display_number(context.total_incidents_12m)}",
        "",
        f"Performance trend summary: {_format_trend(context.progress_8_trend, 'Progress 8')}",
        f"Attainment trend summary: {_format_trend(context.attainment_8_trend, 'Attainment 8')}",
        f"Demographic trend summary: {_format_demographic_trends(context)}",
        f"Inspection history: {_format_inspection_history(context.inspection_history)}",
        f"Top crime categories: {_format_crime_categories(context.top_crime_categories)}",
        "",
        "Give Grok's honest take on how this school is performing based purely on the data.",
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


def _format_trend(points: tuple[MetricTrendPoint, ...], label: str) -> str:
    if not points:
        return f"{label}: Not published"
    return "; ".join(f"{point.year}={_display_score(point.value)}" for point in points)


def _format_demographic_trends(context: SchoolAnalystContext) -> str:
    segments = [
        f"FSM: {_format_pct_trend(context.fsm_pct_trend)}",
        f"EAL: {_format_pct_trend(context.eal_pct_trend)}",
        f"SEN: {_format_pct_trend(context.sen_pct_trend)}",
    ]
    return " | ".join(segments)


def _format_pct_trend(points: tuple[MetricTrendPoint, ...]) -> str:
    if not points:
        return "Not published"
    return "; ".join(f"{point.year}={_display_pct(point.value)}" for point in points)


def _format_inspection_history(points: tuple[InspectionHistoryPoint, ...]) -> str:
    if not points:
        return "Not published"
    return "; ".join(
        f"{point.inspection_date.isoformat()}={_display(point.overall_effectiveness)}"
        for point in points
    )


def _format_crime_categories(categories: tuple[CrimeCategoryCount, ...]) -> str:
    if not categories:
        return "Not published"
    return "; ".join(
        f"{category.category}={category.incident_count:,}" for category in categories[:5]
    )
