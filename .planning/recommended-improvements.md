# Recommended Improvements

Raised by: Tom
Assigned to: Liam
Last updated: 2026-03-09

Items below are sequenced by priority. Each item includes the current state, what was asked for, the implemented approach, and completion status.

---

## Status key

- `[ ]` Not started
- `[~]` In progress
- `[x]` Complete

---

## 1. Ofsted provider page URL - source from backend Ofsted data

**Status:** `[x]`

**Current state:**
The latest inspection card now renders a "View report" link when the backend supplies an Ofsted provider page URL. The frontend does not construct any Ofsted URL locally.

**What was asked for:**
Move the Ofsted URL decision out of the frontend and have the backend provide the link as part of the school profile response.

**Validated source data:**
The Ofsted bronze source (`latest_inspections.csv`) already includes a per-row `Web Link (opens in new window)` value. That source link resolves to the correct provider route and is safer than synthesizing `/provider/{type}/{urn}` or falling back to search URLs. Validation on 2026-03-09 showed:

1. Bronze rows include a non-empty provider/report page link.
2. The legacy Ofsted source URLs redirect successfully to live `https://reports.ofsted.gov.uk/provider/{type}/{urn}` pages.
3. Provider type codes vary by record, so hardcoding `/provider/21/{urn}` is not reliable.
4. Search results pages are not a safe substitute for schools absent from the Ofsted latest dataset.

**Implemented approach:**

1. Added `provider_page_url` to the Ofsted latest pipeline contract and normalized it from the authoritative Ofsted source column onto a browser-safe `reports.ofsted.gov.uk` URL.
2. Validated and normalized accepted URLs in the backend contract layer before staging/promoting the data.
3. Persisted `provider_page_url` onto `school_ofsted_latest` and added an Alembic migration for the new column.
4. Exposed `provider_page_url` through the school profile domain model, application DTO, API schema, OpenAPI contract, and generated web types.
5. Mapped the field into the web `OfstedVM` and passed it through to `OfstedProfileSection`.
6. Kept the frontend rendering-only: if no authoritative Ofsted row exists, the link stays hidden.

**Best-practice decision:**
Use the Ofsted-published provider page URL as the source of truth. Do not generate fallback search URLs or guess provider type codes in the client.

**Files changed:**
- `apps/backend/alembic/versions/20260309_31_phase_m7_ofsted_provider_page_url.py`
- `apps/backend/src/civitas/api/routes.py`
- `apps/backend/src/civitas/api/schemas/school_profiles.py`
- `apps/backend/src/civitas/application/school_profiles/dto.py`
- `apps/backend/src/civitas/application/school_profiles/use_cases.py`
- `apps/backend/src/civitas/domain/school_profiles/models.py`
- `apps/backend/src/civitas/infrastructure/persistence/postgres_school_profile_repository.py`
- `apps/backend/src/civitas/infrastructure/pipelines/contracts/ofsted_latest.py`
- `apps/backend/src/civitas/infrastructure/pipelines/ofsted_latest.py`
- `apps/backend/tests/fixtures/ofsted_latest/latest_inspections_mixed.csv`
- `apps/backend/tests/fixtures/ofsted_latest/latest_inspections_valid.csv`
- `apps/backend/tests/integration/test_ofsted_latest_pipeline.py`
- `apps/backend/tests/integration/test_school_profile_api.py`
- `apps/backend/tests/integration/test_school_profile_repository.py`
- `apps/backend/tests/unit/test_get_school_profile_use_case.py`
- `apps/backend/tests/unit/test_ofsted_latest_transforms.py`
- `apps/web/src/api/generated-types.ts`
- `apps/web/src/api/openapi.json`
- `apps/web/src/features/school-profile/SchoolProfileFeature.tsx`
- `apps/web/src/features/school-profile/components/OfstedProfileSection.tsx`
- `apps/web/src/features/school-profile/mappers/profileMapper.test.ts`
- `apps/web/src/features/school-profile/mappers/profileMapper.ts`
- `apps/web/src/features/school-profile/testData.ts`
- `apps/web/src/features/school-profile/types.ts`

**Operational follow-up after merge/deploy:**

1. Apply the Ofsted migration revision with `uv run --project apps/backend alembic -c apps/backend/alembic.ini upgrade 2026030931`.
2. Rerun the Ofsted latest pipeline so existing records are backfilled with `provider_page_url`.

**Validation completed:**

1. Focused backend tests for contract normalization, pipeline persistence, repository mapping, use case mapping, and API serialization.
2. OpenAPI export and frontend type regeneration.
3. Focused frontend mapper tests, full web typecheck, full web lint, and production web build.
4. Repo-level `make test` was attempted. Backend tests passed; the web suite still has a pre-existing timeout in `src/features/schools-search/SchoolsSearchFeature.test.tsx`.

---
