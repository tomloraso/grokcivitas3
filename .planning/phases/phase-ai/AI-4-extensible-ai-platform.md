# Phase AI-4 Design - Extensible AI Platform

## Document Control

- Status: Proposed
- Last updated: 2026-03-05
- Depends on:
  - `.planning/phases/phase-ai/AI-3-groks-take-premium-analysis.md`
  - `docs/architecture/backend-conventions.md`

## Objective

Generalise the AI infrastructure established in `AI-2` and `AI-3` into a reusable platform that supports future AI features without per-feature infrastructure work. Define the extension points and document the pattern for adding new AI capabilities.

This deliverable is intentionally lighter than `AI-1` through `AI-3`. It captures the generalisation work that should happen after the first two concrete features validate the pattern, and scopes the next set of candidate features.

## Scope

### In scope

- Prompt template registry (add new summary types by adding a module).
- Generic batch generation pipeline step (configurable per summary type).
- Validation policy registry per summary type.
- Summary history table for version tracking.
- Extension point documentation for adding new AI features.
- Candidate feature specifications (not full implementation).

### Out of scope

- Full implementation of candidate features (each becomes its own deliverable).
- Real-time/streaming LLM responses.
- User-facing prompt customisation (future consideration).

## Platform Generalisation

### Prompt template registry

```python
# infrastructure/ai/prompt_templates/__init__.py
REGISTRY: dict[SummaryType, PromptTemplate] = {
    "overview": school_overview,
    "groks_take": groks_take,
    # Future types register here
}
```

Each template module exposes:
- `SYSTEM_PROMPT: str`
- `USER_TEMPLATE: str`
- `VERSION: str`
- `render(context: DataContext) -> tuple[str, str]`
- `CONTEXT_TYPE: type` - the dataclass expected as input

### Generic batch generation

`GenerateSummariesUseCase` becomes generic:

```python
class GenerateSummariesUseCase:
    def execute(self, summary_type: SummaryType, urns: list[str] | None = None) -> BatchResult:
        template = REGISTRY[summary_type]
        context_assembler = self._context_assemblers[summary_type]
        validation_policy = self._validation_policies[summary_type]
        # ... assemble, hash, generate, validate, store
```

Context assemblers are registered per summary type and responsible for querying Gold tables and building the appropriate context dataclass.

### Validation policy registry

```python
VALIDATION_POLICIES: dict[SummaryType, SummaryValidationPolicy] = {
    "overview": overview_validation_policy,
    "groks_take": groks_take_validation_policy,
}
```

Each policy defines:
- word-count bounds
- banned phrasing / recommendation rules
- context-reference checks
- corrective-retry behavior

### Summary history table

```sql
CREATE TABLE school_ai_summary_history (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    urn text NOT NULL,
    summary_type text NOT NULL,
    text text NOT NULL,
    data_version_hash text NOT NULL,
    prompt_version text NOT NULL,
    model_id text NOT NULL,
    generated_at timestamptz NOT NULL,
    superseded_at timestamptz NOT NULL DEFAULT timezone('utc', now())
);
CREATE INDEX ix_summary_history_urn_type
    ON school_ai_summary_history (urn, summary_type);
```

On each upsert to `school_ai_summaries`, the previous row is archived to `school_ai_summary_history`. This supports:
- Audit trail of what was shown to users.
- Prompt version impact analysis.
- Rollback capability.

## Candidate Future Features

### 1. Comparison narratives

- **Input:** Two or more URNs + comparison dimensions (demographics, performance, Ofsted).
- **Output:** 200-300 word comparative analysis highlighting differences and similarities.
- **Prompt type:** `comparison`
- **Context type:** `SchoolComparisonContext` (list of school contexts).
- **Storage:** Ephemeral cache (keyed by sorted URN set + hash), not permanent per-school storage.
- **Trigger:** On-demand when user compares schools (first candidate for live generation with cache).

### 2. Natural language search

- **Input:** Free text query ("schools near Manchester with good Ofsted and low FSM").
- **Output:** Structured search filters extracted by LLM.
- **Implementation:** LLM function-calling to convert NL query to existing API filter parameters.
- **Storage:** None (stateless transformation).
- **Note:** Does not require summary infrastructure; uses a separate `QueryParser` port.

### 3. Trend interpretation

- **Input:** A school's multi-year trend data for a specific metric.
- **Output:** 50-80 word plain-English interpretation of the trend.
- **Prompt type:** `trend_interpretation`
- **Context type:** `SchoolTrendContext` (metric name + year/value pairs).
- **Storage:** Cached per data-version hash (same pattern as overview).
- **Trigger:** Lazy generation on first request, then cached.

### 4. Data quality explanations

- **Input:** Completeness contract for a school (available/partial/unavailable sections with reason codes).
- **Output:** Plain-English explanation of why certain data is missing.
- **Implementation:** Template-based (no LLM needed). Rule engine mapping reason codes to user-facing text.
- **Note:** This is not an LLM feature; included here for completeness as it was discussed alongside AI features.

## File-Oriented Implementation Plan

1. `apps/backend/src/civitas/infrastructure/ai/prompt_templates/__init__.py`
   - Formalise `REGISTRY` dict and `PromptTemplate` protocol.

2. `apps/backend/src/civitas/application/school_summaries/use_cases.py`
   - Refactor `GenerateSchoolOverviewsUseCase` and `GenerateGroksTakeUseCase` into generic `GenerateSummariesUseCase`.

3. `apps/backend/src/civitas/application/school_summaries/context_assemblers.py` (new)
   - Formalise the context-assembly pattern already introduced in `AI-2` / `AI-3`.
   - `OverviewContextAssembler`, `PremiumContextAssembler` classes.
   - Registry pattern for future assemblers.

4. `apps/backend/src/civitas/domain/school_summaries/services.py`
   - Extract reusable validation policy objects by summary type.

5. `apps/backend/alembic/versions/YYYYMMDD_NN_phase_ai4_summary_history.py` (new)
   - Create `school_ai_summary_history` table.

6. `apps/backend/src/civitas/infrastructure/persistence/postgres_summary_repository.py`
   - Add history archival on upsert.

7. `docs/architecture/ai-extension-guide.md` (new)
   - Document the pattern: create context dataclass, create prompt template module, register in `REGISTRY`, add context assembler, define validation policy, run batch.

8. `apps/backend/tests/unit/test_prompt_registry.py` (new)
   - All registered templates have required attributes.
   - Render functions produce valid output.

9. `apps/backend/tests/unit/test_summary_history.py` (new)
   - Upsert archives previous version.
   - History is queryable by URN and type.

10. `apps/backend/tests/unit/test_summary_validation_policies.py` (new)
    - All registered summary types expose deterministic validation policies.

## Codex Execution Checklist

1. Refactor existing use cases into generic pattern.
2. Extract context assemblers.
3. Formalise prompt template registry.
4. Formalise validation policy registry.
5. Add summary history table and archival logic.
6. Write extension guide documentation.
7. Run full `make lint` and `make test` to verify zero regressions.

## Required Commands

- `uv run --project apps/backend pytest apps/backend/tests/unit/test_prompt_registry.py -q`
- `uv run --project apps/backend pytest apps/backend/tests/unit/test_summary_history.py -q`
- `uv run --project apps/backend pytest apps/backend/tests/unit/test_summary_validation_policies.py -q`
- `uv run --project apps/backend pytest apps/backend/tests/ -q`
- `make lint`
- `make test`

## Acceptance Criteria

1. New AI features can be added by creating a prompt template module and context assembler without modifying core AI infrastructure.
2. Summary history table retains previous versions on each regeneration.
3. Generic `GenerateSummariesUseCase` supports all registered summary types.
4. Validation policies are registered per summary type so new AI features inherit deterministic post-generation guardrails.
5. Extension guide in `docs/` explains the step-by-step process for adding a new AI capability.
6. All existing overview and premium generation continues to work after refactoring.

## Risks And Mitigations

- Risk: Premature generalisation before patterns are proven.
  - Mitigation: `AI-4` is sequenced after `AI-2` and `AI-3` are complete and validated. Generalise only what has been concretely implemented.
- Risk: Over-engineering the registry when only two types exist.
  - Mitigation: Registry is a simple dict, not a plugin framework. Complexity increases only when justified by real features.
