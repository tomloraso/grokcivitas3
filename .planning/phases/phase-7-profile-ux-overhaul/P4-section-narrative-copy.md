# P4 - Section Narrative Copy

## Status

Not started

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

- [ ] Three section headings updated to parent-language copy.
- [ ] Two section descriptions rewritten.
- [ ] Aria heading IDs and labelledby attributes kept in sync.
- [ ] No accessibility regression (heading hierarchy unchanged).
- [ ] Lint passes.

## Rollback

```
git checkout -- \
  apps/web/src/features/school-profile/components/AcademicPerformanceSection.tsx \
  apps/web/src/features/school-profile/components/AttendanceBehaviourSection.tsx \
  apps/web/src/features/school-profile/components/WorkforceLeadershipSection.tsx
```
