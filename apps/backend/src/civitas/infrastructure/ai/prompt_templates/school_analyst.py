from __future__ import annotations

from civitas.domain.school_summaries.models import (
    CrimeCategoryCount,
    InspectionHistoryPoint,
    MetricTrendPoint,
    SchoolAnalystContext,
    SummaryGenerationFeedback,
)

VERSION = "analyst.v6"
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
- If Progress 8, Attainment 8, or Ofsted measures are not present in the user message, do not
  mention them or infer them.
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
    include_ofsted_context = _should_include_ofsted_context(context)
    lines = ["School metrics only (do not use any other information):"]
    lines.extend(
        filter(
            None,
            (
                _line("Name", context.name),
                _line_number("Pupil count", context.pupil_count),
                _line_number("Capacity", context.capacity),
                _line_pct("FSM percentage", context.fsm_pct),
                _line_pct("EAL percentage", context.eal_pct),
                _line_pct("SEN percentage", context.sen_pct),
                _line_pct("EHCP percentage", context.ehcp_pct),
                _line_score("Progress 8", context.progress_8),
                _line_score("Attainment 8", context.attainment_8),
                _line(
                    "Ofsted overall effectiveness",
                    context.overall_effectiveness if include_ofsted_context else None,
                ),
                _line_date(
                    "Latest inspection date",
                    context.inspection_date if include_ofsted_context else None,
                ),
                _line(
                    "Quality of education",
                    context.quality_of_education if include_ofsted_context else None,
                ),
                _line(
                    "Behaviour and attitudes",
                    context.behaviour_and_attitudes if include_ofsted_context else None,
                ),
                _line(
                    "Personal development",
                    context.personal_development if include_ofsted_context else None,
                ),
                _line(
                    "Leadership and management",
                    context.leadership_and_management if include_ofsted_context else None,
                ),
                _line_number("IMD decile", context.imd_decile),
                _line_number("IMD rank", context.imd_rank),
                _line_number("IDACI decile", context.idaci_decile),
                _line_number("Total incidents in latest 12 months", context.total_incidents_12m),
            ),
        )
    )
    lines.extend(
        filter(
            None,
            (
                "",
                _line_trend("Performance trend summary", context.progress_8_trend, "Progress 8"),
                _line_trend(
                    "Attainment trend summary",
                    context.attainment_8_trend,
                    "Attainment 8",
                ),
                _line("Demographic trend summary", _format_demographic_trends(context)),
                _line(
                    "Inspection history",
                    _format_inspection_history(context.inspection_history)
                    if include_ofsted_context
                    else None,
                ),
                _line(
                    "Top crime categories", _format_crime_categories(context.top_crime_categories)
                ),
                "",
                "Give Grok's honest take on how this school is performing based purely on the data.",
            ),
        )
    )

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


def _should_include_ofsted_context(context: SchoolAnalystContext) -> bool:
    return context.overall_effectiveness is not None or context.inspection_date is not None


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


def _line(label: str, value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    normalized = value.strip()
    if normalized == "Not published":
        return None
    return f"- {label}: {normalized}"


def _line_number(label: str, value: int | None) -> str | None:
    if value is None:
        return None
    return f"- {label}: {_display_number(value)}"


def _line_pct(label: str, value: float | None) -> str | None:
    if value is None:
        return None
    return f"- {label}: {_display_pct(value)}"


def _line_score(label: str, value: float | None) -> str | None:
    if value is None:
        return None
    return f"- {label}: {_display_score(value)}"


def _line_date(label: str, value: object) -> str | None:
    if value is None:
        return None
    return f"- {label}: {_display_date(value)}"


def _line_trend(label: str, points: tuple[MetricTrendPoint, ...], metric_label: str) -> str | None:
    if not points:
        return None
    return f"{label}: {_format_trend(points, metric_label)}"


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
