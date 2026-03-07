# Phase AI-3 Design - Grok's Take Premium Analysis

## Document Control

- Status: Proposed
- Last updated: 2026-03-05
- Depends on:
  - `.planning/phases/phase-ai/AI-2-school-overview-summary.md`
  - `.planning/ai-features.md`
  - `.planning/phased-delivery.md`
  - `docs/architecture/backend-conventions.md`

## Objective

Introduce a premium-tier "Grok's Take" analysis (150-220 words) that provides honest, balanced AI commentary on every key metric for a school. This deliverable covers generation, storage, and operator QA workflows only. Public API/UI exposure is deferred until Phase 10 authentication and feature-tier premium access controls exist.

## Scope

### In scope

- New prompt template for premium analysis with metric-by-metric commentary.
- Storage in existing `school_ai_summaries` table with `summary_type = 'groks_take'`.
- Batch generation alongside overviews.
- Operator-facing preview workflow for QA and sign-off.
- Disclaimer copy prepared for later authenticated UI exposure.

### Out of scope

- Payment/subscription system implementation.
- Public profile/API exposure of premium AI text.
- Frontend premium card / upgrade CTA.
- Live generation.
- Custom user-requested angles (deferred to `AI-4`).

## Design Decisions

1. **Same infrastructure, different prompt.** Reuses `SummaryGenerator` port, provider adapters, `PostgresSummaryRepository`, and batch generation patterns from `AI-2`. Only the prompt template and data assembly differ.
2. **Full metric coverage.** The prompt receives every available metric (Attainment 8, Progress 8, Ofsted history, FSM, ethnicity, SEND, gender, attendance where available, exclusions, crime context, IMD, staffing where available).
3. **No open-web or model-memory facts.** Premium text must be grounded only in assembled Civitas context. No notable alumni or other external-knowledge claims in `AI-3`.
4. **Public exposure is blocked on Phase 10.** `groks_take` text is not added to public profile responses in `AI-3`. Phase 10 provides authenticated identity, backend premium capability checks, and any premium endpoint wiring.
5. **Operator review path first.** `AI-3` adds CLI-supported preview/review access for generated premium summaries so prompt quality can be assessed before any user-facing rollout.
6. **Word count 150-220.** Longer than overview to accommodate per-metric commentary.
7. **The same validator/quarantine policy from `AI-2` applies.** Premium outputs must pass deterministic checks for word count, banned recommendations/suitability phrasing, prohibited comparative language, and non-context references before they are stored as ready for future exposure.

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

Premium contexts are assembled through the same application-side context repository pattern introduced in `AI-2`; generation use cases do not query Gold tables directly.

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

3. `apps/backend/src/civitas/application/school_summaries/ports/summary_context_repository.py`
   - Extend `SummaryContextRepository` with premium-context assembly methods.

4. `apps/backend/src/civitas/application/school_summaries/use_cases.py`
   - Add `GenerateGroksTakeUseCase` for batch premium generation.
   - Add `GetGroksTakePreviewUseCase` for operator/CLI retrieval only.

5. `apps/backend/src/civitas/infrastructure/ai/prompt_templates/groks_take.py` (new)
   - `SYSTEM_PROMPT`, `USER_TEMPLATE`, `VERSION`, `render()`.

6. `apps/backend/src/civitas/infrastructure/ai/providers/*.py`
   - Extend provider adapters with `generate_groks_take`.

7. `apps/backend/src/civitas/cli/main.py`
   - Extend `generate-summaries` command with `--type overview|groks_take|all`.
   - Add `show-summary --type groks_take --urn <urn>` or equivalent operator preview command.

8. `apps/backend/tests/unit/test_groks_take_prompt.py` (new)
   - Prompt renders valid messages.
   - Word count within range.

9. `apps/backend/tests/unit/test_generate_groks_take_use_case.py` (new)
   - Generates for stale schools only.
   - Applies the shared validator/quarantine policy.

10. `apps/backend/tests/integration/test_summary_repository.py`
   - `groks_take` entries store and retrieve correctly.

11. `apps/backend/tests/unit/test_summary_preview_cli.py` (new)
   - Operator preview command returns stored premium analysis for QA.

## Codex Execution Checklist

1. Add premium analysis context model.
2. Extend `SummaryGenerator` protocol with `generate_groks_take`.
3. Extend the existing context repository with premium-context assembly.
4. Implement premium prompt template with render tests.
5. Extend provider adapters and use case.
6. Reuse the shared validator/quarantine flow from `AI-2`.
7. Extend CLI commands for batch generation and operator preview.
8. Record Phase 10 handoff requirements for authenticated exposure.
9. Run `make lint` and `make test`.

## Required Commands

- `uv run --project apps/backend pytest apps/backend/tests/unit/test_groks_take_prompt.py -q`
- `uv run --project apps/backend pytest apps/backend/tests/unit/test_generate_groks_take_use_case.py -q`
- `uv run --project apps/backend pytest apps/backend/tests/unit/test_summary_preview_cli.py -q`
- `uv run --project apps/backend pytest apps/backend/tests/integration/test_summary_repository.py -q`
- `make lint`
- `make test`

## Acceptance Criteria

1. Premium prompt produces 150-220 word balanced analysis covering all available metrics.
2. `school_ai_summaries` stores validated `groks_take` entries with full provenance.
3. Premium output contains no recommendations, suitability advice, or non-context claims; invalid outputs are quarantined by the shared validator flow.
4. CLI can generate premium analyses independently or alongside overviews.
5. Operator preview tooling can retrieve generated premium analyses for QA.
6. Public profile/API exposure of `groks_take` is explicitly deferred to Phase 10 and is not implemented in `AI-3`.

## Legal And Disclaimer

Mandatory disclaimer above every Grok's Take:

> "Grok's Take is AI-generated analysis based on public government data. It is not official advice. Parents should always read the latest Ofsted report and visit the school in person."

## Phase 10 Handoff

When Phase 10 auth + premium access work starts, it will:

1. Add authenticated identity to the API boundary.
2. Add backend premium capability checks before exposing `groks_take`.
3. Introduce the premium UI card / upgrade CTA.
4. Keep the existing disclaimer and validator requirements unchanged.

## Risks And Mitigations

- Risk: Premium prompt drifts into subjective recommendations.
  - Mitigation: Prompt explicitly forbids recommendations/suitability language, and the shared validator rejects banned phrasing before persistence.
- Risk: Premium analysis appears biased toward or against certain school types.
  - Mitigation: Prompt enforces balanced tone with both strengths and concerns. Manual review of sample outputs before launch.
- Risk: Premium work is mistaken for public launch readiness.
  - Mitigation: `AI-3` limits scope to generation + operator QA. Public exposure is a separate Phase 10 handoff with auth and premium capability enforcement.
