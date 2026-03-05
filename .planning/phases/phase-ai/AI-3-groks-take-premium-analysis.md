# Phase AI-3 Design - Grok's Take Premium Analysis

## Document Control

- Status: Proposed
- Last updated: 2026-03-05
- Depends on:
  - `.planning/phases/phase-ai/AI-2-school-overview-summary.md`
  - `.planning/ai-features.md`
  - `docs/architecture/backend-conventions.md`

## Objective

Introduce a premium-tier "Grok's Take" analysis (150-220 words) that provides honest, balanced AI commentary on every key metric for a school. This builds on the AI infrastructure established in `AI-2` and adds a deeper prompt template with full metric coverage.

## Scope

### In scope

- New prompt template for premium analysis with metric-by-metric commentary.
- Premium visibility gating (API-level; frontend premium/free split).
- Storage in existing `school_ai_summaries` table with `summary_type = 'groks_take'`.
- Batch generation alongside overviews.
- Disclaimer display.

### Out of scope

- Payment/subscription system implementation (assumed external entitlement provider).
- Live generation.
- Custom user-requested angles (deferred to `AI-4`).

## Design Decisions

1. **Same infrastructure, different prompt.** Reuses `SummaryGenerator` port, `LlmSummaryGenerator` adapter, `PostgresSummaryRepository`, and batch generation use case from `AI-2`. Only the prompt template and data assembly differ.
2. **Full metric coverage.** The prompt receives every available metric (Attainment 8, Progress 8, Ofsted history, FSM, ethnicity, SEND, gender, attendance where available, exclusions, crime context, IMD, staffing where available).
3. **No open-web or model-memory facts.** Premium text must be grounded only in assembled Civitas context. No notable alumni or other external-knowledge claims in `AI-3`.
4. **Premium gating is backend entitlement-based.** The profile endpoint returns `groks_take_text` only when server-side entitlement checks pass (auth context + entitlement service), never from client-provided tier flags.
5. **Word count 150-220.** Longer than overview to accommodate per-metric commentary.

## Data Assembly

Extends `SchoolOverviewContext` from `AI-2` with additional fields:

```
SchoolPremiumAnalysisContext(SchoolOverviewContext):
  # Additional from school_demographics_yearly (all years)
  fsm_pct_trend: list[{year, value}]
  eal_pct_trend: list[{year, value}]
  sen_pct_trend: list[{year, value}]

  # From school_performance_yearly (all years)
  progress_8_trend: list[{year, value}]
  attainment_8_trend: list[{year, value}]

  # From school_ofsted_latest (sub-judgements)
  quality_of_education, behaviour_and_attitudes
  personal_development, leadership_and_management
  early_years_provision, sixth_form_provision

  # From ofsted_inspections (history)
  inspection_history: list[{date, overall_effectiveness}]

  # From area_deprivation (full)
  imd_decile, imd_rank, idaci_decile

  # From area_crime_context (summary)
  total_incidents_12m, top_crime_categories

  # From school_ethnicity_yearly (latest)
  ethnicity_breakdown: list[{group, percentage}]
```

## Prompt Template

`apps/backend/src/civitas/infrastructure/ai/prompt_templates/groks_take.py`

Prompt constraints:
- 150-220 words.
- Must address: academic performance, Ofsted trajectory, demographics context, area context, school character.
- Must highlight: genuine strengths, genuine concerns, notable trends.
- Must not: rank against specific other schools, provide suitability guidance, give recommendations, or use marketing language.
- Must not: introduce facts not present in the assembled context.
- Must: include balanced positive and critical observations.

## File-Oriented Implementation Plan

1. `apps/backend/src/civitas/domain/school_summaries/models.py`
   - Add `SchoolPremiumAnalysisContext` dataclass extending overview context.

2. `apps/backend/src/civitas/application/school_summaries/ports/summary_generator.py`
   - Extend `SummaryGenerator` protocol:
     ```python
     def generate_groks_take(self, context: SchoolPremiumAnalysisContext) -> GeneratedSummary: ...
     ```
3. `apps/backend/src/civitas/application/school_summaries/ports/premium_access_checker.py` (new)
   - Add `PremiumAccessChecker` protocol for backend entitlement checks.

4. `apps/backend/src/civitas/application/school_summaries/use_cases.py`
   - Add `GenerateGroksTakeUseCase` for batch premium generation.
   - Add `GetGroksTakeUseCase` for retrieval with premium-tier check.

5. `apps/backend/src/civitas/infrastructure/ai/prompt_templates/groks_take.py` (new)
   - `SYSTEM_PROMPT`, `USER_TEMPLATE`, `VERSION`, `render()`.

6. `apps/backend/src/civitas/infrastructure/ai/llm_client.py`
   - Add `generate_groks_take` method implementing the protocol extension.

7. `apps/backend/src/civitas/api/routes.py`
   - Extend profile response with `groks_take_text: str | None`.
   - Gate on backend entitlement check from auth context (client tier flags are ignored).

8. `apps/backend/src/civitas/cli/main.py`
   - Extend `generate-summaries` command with `--type overview|groks_take|all` option.

9. `apps/web/src/features/school-profile/`
   - Add "Grok's Take" card with premium badge and disclaimer.
   - Handle free-tier state (CTA to upgrade or placeholder).

10. `apps/backend/tests/unit/test_groks_take_prompt.py` (new)
   - Prompt renders valid messages.
   - Word count within range.

11. `apps/backend/tests/unit/test_generate_groks_take_use_case.py` (new)
   - Generates for stale schools only.
   - Skips when premium tier disabled.

12. `apps/backend/tests/integration/test_school_profile_api.py`
   - Premium tier request includes `groks_take_text`.
   - Non-premium request returns `null` for `groks_take_text`.

## Codex Execution Checklist

1. Add premium analysis context model.
2. Extend `SummaryGenerator` protocol with `generate_groks_take`.
3. Add `PremiumAccessChecker` port and infrastructure adapter.
4. Implement premium prompt template with render tests.
5. Extend LLM adapter and use case.
6. Add API premium gating logic.
7. Extend CLI command.
8. Add frontend premium card.
9. Run `make lint` and `make test`.

## Required Commands

- `uv run --project apps/backend pytest apps/backend/tests/unit/test_groks_take_prompt.py -q`
- `uv run --project apps/backend pytest apps/backend/tests/unit/test_generate_groks_take_use_case.py -q`
- `uv run --project apps/backend pytest apps/backend/tests/unit/test_premium_access_checker.py -q`
- `uv run --project apps/backend pytest apps/backend/tests/integration/test_school_profile_api.py -q`
- `make lint`
- `make test`

## Acceptance Criteria

1. Premium prompt produces 150-220 word balanced analysis covering all available metrics.
2. `school_ai_summaries` stores `groks_take` entries with full provenance.
3. Profile API returns `groks_take_text` only when backend entitlement checks pass.
4. Non-premium requests return `null` for `groks_take_text` (no error).
5. Premium output contains no recommendations, suitability advice, or non-context claims.
6. CLI can generate premium analyses independently or alongside overviews.
7. Frontend displays premium card with disclaimer.

## Legal And Disclaimer

Mandatory disclaimer above every Grok's Take:

> "Grok's Take is AI-generated analysis based on public government data. It is not official advice. Parents should always read the latest Ofsted report and visit the school in person."

## Risks And Mitigations

- Risk: Premium prompt drifts into subjective recommendations.
  - Mitigation: Prompt explicitly forbids recommendations/suitability language; add prompt tests for banned phrasing.
- Risk: Premium analysis appears biased toward or against certain school types.
  - Mitigation: Prompt enforces balanced tone with both strengths and concerns. Manual review of sample outputs before launch.
- Risk: Premium gating is bypassed by spoofed client input.
  - Mitigation: API-level enforcement uses backend entitlement checks from trusted auth context; client tier flags are ignored.
