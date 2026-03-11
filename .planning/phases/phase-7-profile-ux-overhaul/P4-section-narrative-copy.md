# P4 - Section Narrative Copy

## Status

Completed — 2026-03-07 (extended scope)

## Goal

Replace DfE-internal category names with parent-language headings and rewrite section descriptions to be immediately meaningful to someone without education sector knowledge.

## Files Changed

- `apps/web/src/features/school-profile/components/AcademicPerformanceSection.tsx`
- `apps/web/src/features/school-profile/components/AttendanceBehaviourSection.tsx`
- `apps/web/src/features/school-profile/components/WorkforceLeadershipSection.tsx`

## Copy Changes

| Section | Old heading | New heading | Old description | New description |
|---------|------------|-------------|-----------------|-----------------|
| Academic performance | Academic Performance | Results & Progress | *(none)* | *(none — year range shown instead)* |
| Attendance & behaviour | Attendance and Behaviour | Day-to-Day at School | "Latest published attendance, persistent absence, suspensions and exclusions." | "How regularly pupils come to school, and how the school manages behaviour." |
| Workforce | Workforce and Leadership | Teachers & Staff | "Staffing ratios, teacher profile measures and leadership metadata." | "Classroom staffing ratios, teacher experience, and who leads the school." |
| Finance | *(new section)* | School Finance | "Latest Totals", "Funding Sources", "Where the Money Goes", "Per-Pupil & Benchmarked" | "Published academy finance data and per-pupil benchmarks." |

## Aria IDs Updated

Heading `id` attributes and `aria-labelledby` attributes updated to match new headings:

| Component | Old id | New id |
|-----------|--------|--------|
| AcademicPerformanceSection | `performance-heading` | `results-progress-heading` |
| AttendanceBehaviourSection | `attendance-behaviour-heading` | `day-to-day-heading` |
| WorkforceLeadershipSection | `workforce-heading` | `teachers-staff-heading` |

## Design Rationale

Parents do not think in DfE category names. "Workforce and Leadership" signals nothing to someone choosing a school for their child. "Teachers & Staff" answers the implied question: *who works here and are they stable?*

The subsection labels within each section (e.g. "Attendance", "Behaviour", "Workforce", "Leadership") are retained — they are short and self-explanatory at that level of detail.

## Acceptance Criteria

- [x] Three section headings updated to parent-language copy.
- [x] Two section descriptions rewritten.
- [x] Aria heading IDs and labelledby attributes kept in sync.
- [x] No accessibility regression (heading hierarchy unchanged).
- [x] Lint passes.

**Extended scope (beyond original P4):**

Metric label renames in `metricCatalog.ts`:
- `FSM6` → `Ever Eligible for Free Meals`
- `SEN Support` → `Additional Needs Support`
- `EHCP` → `Education Health & Care Plan`
- `EAL` → `English as Additional Language`
- `First Language Unclassified` → `Language Unrecorded`
- `Supply Staff %` → `Supply Staff`
- `Teachers 3+ Years Experience` → `Experienced Teachers`
- `Qualified Teacher Status` → `Qualified Teachers`
- `Level 6+ Qualifications` → `Degree-Level Staff`
- `Suspensions Rate` / `Permanent Exclusions Rate` → singular forms
- All `KS2 ...` → `Year 6 ...`
- EBacc terminology clarified: "EBacc Entered", "EBacc Strong Pass", "EBacc Standard Pass"
- `Progress 8 Disadvantaged Gap` → `Disadvantage Progress Gap`

Plain-English `description` field added to every `MetricCatalogEntry` — surfaced on StatCard via ⓘ toggle.

Neighbourhood section (NeighbourhoodSection.tsx):
- Area Deprivation: replaced IMD decile number with plain-English sentence contextualising the area's position nationally (e.g. "This area is in the bottom 30% of areas in England for deprivation").
- District name shown as "District: [name]".
- Domain tiles: colour-coded dot (danger/warning/amber/emerald/success) + "Decile X / 10".
- House Prices sparkline: year range label derived from first/last trend point (e.g. "2020 – 2024").

## Rollback

```
git checkout -- \
  apps/web/src/features/school-profile/components/AcademicPerformanceSection.tsx \
  apps/web/src/features/school-profile/components/AttendanceBehaviourSection.tsx \
  apps/web/src/features/school-profile/components/WorkforceLeadershipSection.tsx
```
