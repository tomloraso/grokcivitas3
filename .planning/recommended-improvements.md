# Recommended Improvements

Raised by: Tom
Assigned to: Liam
Last updated: 2026-03-09

Items below are sequenced by priority. Each item includes the current state, what is being asked for, the recommended approach, and completion status.

---

## Status key

- `[ ]` Not started
- `[~]` In progress
- `[x]` Complete

---

## 1. Ofsted report URL — move to backend

**Status:** `[~]`

**Current state:**
The "View report" link UI is in place on the latest inspection card (opens in a new tab). The "View on Ofsted" header link has been removed. The frontend no longer constructs any URL — `OfstedProfileSection` accepts an `ofstedReportUrl: string | null` prop and only renders the link when the value is non-null. Currently `SchoolProfileFeature` passes `null`, so the link is hidden until the backend supplies the URL.

**What is being asked for:**
~~1. **New "View report" link on the latest inspection card.**~~ ✓ Done — the latest inspection card now shows a "View report" link opening in a new tab to the Ofsted search results for that school. Header link removed.

2. **Move URL construction to the backend.** Remove the URL construction from the frontend entirely. The backend should supply a computed `ofsted_report_url` field on the school profile response. The frontend just renders it as an external link — no URL logic on the client.

**Why:**
The project architecture states the backend owns business logic and decision rules; the frontend renders data and sends intent. The correct Ofsted URL is not purely mechanical — it depends on school type. For example, `/provider/21/{urn}` only resolves correctly for certain school types (verified: returns 404 for independent schools). The backend has the full school record including type and can produce the most precise link. If Ofsted change their URL structure, the fix is in one place.

**Recommended approach:**

1. Add `ofsted_report_url: str | None` to `SchoolProfileIdentityResponse` in `apps/backend/src/civitas/api/schemas/school_profiles.py`.

2. Compute the value in the school profile use case or mapper. For now the safe fallback is the search URL:
   ```python
   f"https://reports.ofsted.gov.uk/search?q={urn}"
   ```
   Optionally, map known GIAS school types to their Ofsted provider type codes and use the direct `/provider/{type}/{urn}` URL where reliable.

3. Regenerate frontend types:
   ```bash
   cd apps/web && npm run generate:types
   ```

4. Update `SchoolIdentityVM` in `apps/web/src/features/school-profile/types.ts` to include `ofstedReportUrl: string | null`.

5. Update the profile mapper to pass the field through.

6. In `SchoolProfileFeature.tsx`, replace `ofstedReportUrl={null}` with `ofstedReportUrl={profile.school.ofstedReportUrl}` (or wherever the mapper surfaces it). No changes needed in `OfstedProfileSection.tsx` — it already accepts the prop and renders the link only when the value is non-null.

**Files to touch:**
- `apps/backend/src/civitas/api/schemas/school_profiles.py`
- `apps/backend/src/civitas/application/schools/use_cases.py` (or relevant mapper)
- `apps/web/src/api/generated-types.ts` (regenerated)
- `apps/web/src/features/school-profile/types.ts`
- `apps/web/src/features/school-profile/mappers/profileMapper.ts`
- `apps/web/src/features/school-profile/components/OfstedProfileSection.tsx`
- `apps/web/src/features/school-profile/SchoolProfileFeature.tsx`

---
