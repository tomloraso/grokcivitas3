import type { BenchmarkSlot } from "../../components/ui/stat-card";
import {
  formatMetricDelta,
  formatMetricValue,
  getMetricCatalogEntry,
} from "./metricCatalog";
import type { BenchmarkContextVM, BenchmarkMetricVM } from "./types";

function benchmarkDecimals(metric: BenchmarkMetricVM): number {
  const catalog = getMetricCatalogEntry(metric.metricKey);
  if (typeof catalog?.decimals === "number") {
    return catalog.decimals;
  }
  if (metric.unit === "count" || metric.unit === "currency") {
    return 0;
  }
  if (metric.unit === "ratio") {
    return 1;
  }
  return 2;
}

function findSimilarSchoolContext(contexts: BenchmarkContextVM[]): BenchmarkContextVM | null {
  return contexts.find((context) => context.scope === "similar_school") ?? null;
}

export function buildBenchmarkSlot(metric: BenchmarkMetricVM): BenchmarkSlot {
  const displayDecimals = benchmarkDecimals(metric);
  const similarSchool = findSimilarSchoolContext(metric.contexts);

  return {
    localLabel: metric.localAreaLabel,
    schoolRaw: metric.schoolValue,
    localRaw: metric.localValue,
    nationalRaw: metric.nationalValue,
    isPercent: metric.unit === "percent",
    displayDecimals,
    schoolValueFormatted: formatMetricValue(metric.schoolValue, metric.unit, displayDecimals),
    localValueFormatted: formatMetricValue(metric.localValue, metric.unit, displayDecimals),
    nationalValueFormatted: formatMetricValue(metric.nationalValue, metric.unit, displayDecimals),
    schoolVsLocalDelta: metric.schoolVsLocalDelta,
    schoolVsNationalDelta: metric.schoolVsNationalDelta,
    schoolVsLocalDeltaFormatted: formatMetricDelta(metric.schoolVsLocalDelta, metric.unit),
    schoolVsNationalDeltaFormatted: formatMetricDelta(metric.schoolVsNationalDelta, metric.unit),
    similarSchool: similarSchool
      ? {
          label: similarSchool.label,
          valueFormatted: formatMetricValue(similarSchool.value, metric.unit, displayDecimals),
          percentileRank: similarSchool.percentileRank,
          schoolCount: similarSchool.schoolCount,
        }
      : null,
  };
}
