# P3 - Benchmark Wiring: Section Components

## Status

Not started

## Goal

Thread `BenchmarkDashboardVM` into the three metric section components so each `StatCard` receives an inline `BenchmarkSlot`. Remove the standalone `BenchmarkComparisonSection` from the profile render — that data is now inline.

## Files Changed

- `apps/web/src/features/school-profile/components/AcademicPerformanceSection.tsx`
- `apps/web/src/features/school-profile/components/AttendanceBehaviourSection.tsx`
- `apps/web/src/features/school-profile/components/WorkforceLeadershipSection.tsx`
- `apps/web/src/features/school-profile/SchoolProfileFeature.tsx`

## Pattern Per Section

Each section follows the same three-step pattern:

**1. Accept the new prop**
```ts
benchmarkDashboard: BenchmarkDashboardVM | null;
```

**2. Build the lookup map**
```ts
const benchmarkLookup = new Map<string, BenchmarkMetricVM>(
  benchmarkDashboard?.sections
    .flatMap((s) => s.metrics.map((m) => [m.metricKey, m] as const)) ?? []
);
```

**3. Convert at card-build time**
```ts
function toBenchmarkSlot(metric: BenchmarkMetricVM): BenchmarkSlot {
  return {
    localLabel: metric.localAreaLabel,
    schoolRaw: metric.schoolValue,
    localRaw: metric.localValue,
    nationalRaw: metric.nationalValue,
    isPercent: metric.unit === "percent",
    localValueFormatted: formatMetricValue(metric.localValue, metric.unit),
    nationalValueFormatted: formatMetricValue(metric.nationalValue, metric.unit),
    schoolVsLocalDelta: metric.schoolVsLocalDelta,
    schoolVsNationalDelta: metric.schoolVsNationalDelta,
    schoolVsLocalDeltaFormatted: formatMetricDelta(metric.schoolVsLocalDelta, metric.unit),
    schoolVsNationalDeltaFormatted: formatMetricDelta(metric.schoolVsNationalDelta, metric.unit),
  };
}
// …
const bm = benchmarkLookup.get(metricKey);
<StatCard … benchmark={bm ? toBenchmarkSlot(bm) : undefined} />
```

## Metric Key Alignment

`PERFORMANCE_METRICS[].key` values in `AcademicPerformanceSection` have been confirmed to match `BenchmarkMetricVM.metricKey` from the API — no mapping table required.

Attendance and behaviour metric keys from `ATTENDANCE_METRIC_KEYS` and `BEHAVIOUR_METRIC_KEYS` likewise align.

## SchoolProfileFeature Changes

- Pass `benchmarkDashboard={profile.benchmarkDashboard}` to all three sections.
- Remove `<BenchmarkComparisonSection benchmarkDashboard={profile.benchmarkDashboard} />` render and its import.
- `BenchmarkComparisonSection.tsx` file is **not deleted** — kept for potential future use (print view, compare modal).

## Acceptance Criteria

- [ ] Each of the three sections accepts `benchmarkDashboard` prop.
- [ ] Every stat card that has a matching `BenchmarkMetricVM` shows the benchmark block.
- [ ] Cards without a benchmark match show no benchmark block (not an error state).
- [ ] `BenchmarkComparisonSection` no longer rendered anywhere on the profile page.
- [ ] No duplicate data visible on the page.
- [ ] TypeScript strict — no errors.
- [ ] Lint passes.

## Rollback

```
git checkout -- \
  apps/web/src/features/school-profile/SchoolProfileFeature.tsx \
  apps/web/src/features/school-profile/components/AcademicPerformanceSection.tsx \
  apps/web/src/features/school-profile/components/AttendanceBehaviourSection.tsx \
  apps/web/src/features/school-profile/components/WorkforceLeadershipSection.tsx
```
