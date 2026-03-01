# AI Features

This document defines all AI-powered features in Civitas, focused on delivering clear, honest school intelligence.

## Core AI Features

### 1. School Overview (Free tier)
- A neutral, factual summary of the school.
- 120–180 words.
- Covers only basic facts: school type, size, location, pupil numbers, key characteristics, and any recent notable changes.
- No opinions, no interpretation of statistics, no advice.
- Shown to every user.

### 2. Grok’s Take (Premium tier)
- Honest, professional, non-nonsense AI analysis of the school.
- 150–220 words.
- Provides balanced feedback on **every key metric** (Attainment 8/Progress 8, Ofsted history, FSM, ethnicity, SEND, gender %, attendance, exclusions, crime, IMD, house prices, staffing, etc.).
- Highlights real strengths, any concerns, important trends, and who the school would suit best.
- Additionally attempts to identify and briefly mention **notable alumni** where reliable public information exists (e.g. famous former pupils in politics, sport, business, arts, science, etc.).
- Only includes alumni when the information is verifiable and confidence is high — never speculative.

## Generation Process
- Both summaries are pre-generated using Grok 4.1 Fast Reasoning.
- Run automatically during the regular data import pipeline.
- Stored directly in the database (two simple text fields per school: `overview_text` and `grok_take_text`).
- No live generation when a user visits a school page (instant loading + extremely low cost).

## Model Choice
- Primary model: Grok 4.1 Fast Reasoning.
- Chosen for best balance of cost, speed, large context window, and quality.
- Annual cost for all ~25,000 schools (even with two full refreshes per year): under £50.

## Refresh Strategy
- Automatic regeneration triggered by major data changes (new Ofsted report, significant shifts in attendance/results, etc.).
- Full refresh of every school every 6 months as a safety net.
- Last two versions of each summary are kept for history.

## Implementation Notes
- Exact prompts are stored in the backend and version-controlled.
- Notable alumni lookup will be handled during the LLM generation step using public sources (e.g. Wikipedia mentions or known school alumni lists).
- Fits cleanly into the existing Clean Architecture as a dedicated use-case.
- Grok’s Take explicitly analyses every metric defined in `metrics.md`.

## Legal & Disclaimer
- A clear disclaimer must appear above every Grok’s Take:
  “Grok’s Take is AI-generated analysis based on public government data. It is not official advice. Parents should always read the latest Ofsted report and visit the school in person.”

## Future Enhancements (Phase 1+)
- Allow premium users to request custom angles (“focus on SEN”, “compare to nearby schools”, etc.).
- AI-generated comparison insights between multiple schools.
- Simple trend explanation tool for any single metric.

This feature set keeps Civitas fast, cheap to run, and genuinely useful while giving premium users clear added value.