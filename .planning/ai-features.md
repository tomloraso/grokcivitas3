# AI Features

This document defines AI-powered features in Civitas, focused on clear, decision-grade school intelligence grounded in published data.

## Core AI Features

### 1. School Overview (Free tier)
- A neutral, factual summary of the school.
- 120-180 words.
- Covers basic facts only: school type, size, location, pupil numbers, key characteristics, and recent published changes.
- No opinions, no interpretation beyond provided context, no advice.
- Shown to every user.

### 2. Grok's Take (Premium tier)
- Balanced AI analysis of the school's published metrics.
- 150-220 words.
- Covers available metrics such as Attainment 8/Progress 8, Ofsted history, FSM, ethnicity, SEND, gender, attendance, exclusions, crime, IMD, and other delivered metric domains.
- Highlights strengths, concerns, and trend signals grounded in provided data context.
- Must not provide recommendations, rankings, or suitability guidance.
- Must not introduce facts that are not present in assembled Civitas context.

## Generation Process
- Both summaries are pre-generated (never generated live during profile requests).
- Generation runs as a post-pipeline operation after Bronze -> Silver -> Gold refresh succeeds.
- Summaries are stored in `school_ai_summaries` keyed by `(urn, summary_type)`.
- User-facing requests read cached summary text for fast responses.

## Model Choice
- Primary model: Grok 4.1 Fast Reasoning (configurable via settings).
- Model choice is infrastructure configuration, not domain/application logic.

## Refresh Strategy
- Each summary stores a `data_version_hash` derived from the assembled context.
- Hash changes mark summaries stale and eligible for regeneration.
- Full refresh can be forced as an operational safety run.
- Summary history retention is implemented in `AI-4` via `school_ai_summary_history`.

## Entitlement And Access
- Premium visibility is backend-enforced.
- Client tier hints are not trusted as entitlement source.

## Implementation Notes
- Prompt templates are version-controlled in backend code.
- LLM access is port-based and swappable behind infrastructure adapters.
- Prompt and model provenance are stored with each summary for auditability.

## Legal And Disclaimer
- A clear disclaimer must appear above each AI-generated summary.
- Mandatory Grok's Take disclaimer:
  "Grok's Take is AI-generated analysis based on public government data. It is not official advice. Parents should always read the latest Ofsted report and visit the school in person."

## Future Enhancements
- Premium custom angles (for example: focus on SEN).
- AI-generated comparison insights between multiple schools.
- Plain-English trend interpretation helpers.
