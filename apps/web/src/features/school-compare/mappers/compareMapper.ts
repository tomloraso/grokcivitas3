import type {
  SchoolCompareBenchmark,
  SchoolCompareCell,
  SchoolCompareResponse,
  SchoolCompareSchool
} from "../../../api/types";
import { formatCompletenessReasonCopy } from "../../../shared/completeness";
import type { CompareSelectionItem } from "../../../shared/context/CompareSelectionContext";
import { paths } from "../../../shared/routing/paths";
import { mapSectionAccess } from "../../premium-access/mappers";
import type {
  CompareCellVM,
  ComparePageVM,
  CompareSchoolColumnVM
} from "../types";

const dateFormatter = new Intl.DateTimeFormat("en-GB", {
  day: "numeric",
  month: "short",
  year: "numeric",
  timeZone: "UTC"
});

export function mapCompareToVM(
  response: SchoolCompareResponse,
  selectionByUrn: Map<string, CompareSelectionItem>,
  compareHref: string
): ComparePageVM {
  return {
    access: mapSectionAccess(response.access),
    schools: (response.schools ?? []).map((school) =>
      mapSchoolColumnToVM(school, selectionByUrn.get(school.urn), compareHref)
    ),
    sections: (response.sections ?? []).map((section) => ({
      key: section.key,
      label: section.label,
      rows: (section.rows ?? []).map((row) => ({
        metricKey: row.metric_key,
        label: row.label,
        unit: row.unit,
        cells: (row.cells ?? []).map((cell) => mapCellToVM(cell, row.unit))
      }))
    }))
  };
}

function mapSchoolColumnToVM(
  school: SchoolCompareSchool,
  selectionItem: CompareSelectionItem | undefined,
  compareHref: string
): CompareSchoolColumnVM {
  return {
    urn: school.urn,
    name: school.name,
    phase: school.phase ?? "Unknown",
    type: school.type ?? "Unknown",
    postcode: school.postcode ?? "Not published",
    ageRangeLabel: school.age_range_label || null,
    distanceLabel:
      selectionItem?.distanceMiles !== undefined
        ? `${selectionItem.distanceMiles.toFixed(2)} mi`
        : null,
    profileHref: paths.schoolProfile(school.urn),
    profileState: {
      fromCompare: {
        href: compareHref
      }
    }
  };
}

function mapCellToVM(cell: SchoolCompareCell, unit: string): CompareCellVM {
  const displayValue =
    formatDisplayValue(cell, unit) ?? availabilityText(cell.availability);
  const metaLabel =
    unit === "date" ? null : cell.year_label ?? formatSnapshotDate(cell.snapshot_date);
  const detailLabel = buildCompletenessLabel(cell);

  return {
    urn: cell.urn,
    displayValue,
    availability: cell.availability,
    metaLabel,
    detailLabel,
    benchmarkLabel: buildBenchmarkLabel(cell.benchmark, unit),
    isMuted: cell.availability !== "available"
  };
}

function formatDisplayValue(cell: SchoolCompareCell, unit: string): string | null {
  if (unit === "date") {
    return formatSnapshotDate(cell.snapshot_date) ?? cell.value_text;
  }

  if (!cell.value_text) {
    return null;
  }
  return cell.value_text;
}

function availabilityText(
  availability: SchoolCompareCell["availability"]
): string {
  switch (availability) {
    case "unsupported":
      return "Not applicable";
    case "suppressed":
      return "Suppressed";
    case "unavailable":
      return "Unavailable";
    default:
      return "Unavailable";
  }
}

function formatSnapshotDate(snapshotDate: string | null): string | null {
  if (!snapshotDate) {
    return null;
  }

  const parsed = new Date(`${snapshotDate}T00:00:00Z`);
  if (Number.isNaN(parsed.getTime())) {
    return snapshotDate;
  }

  return dateFormatter.format(parsed);
}

function buildCompletenessLabel(cell: SchoolCompareCell): string | null {
  if (
    cell.completeness_status === "available" &&
    cell.availability === "available"
  ) {
    return null;
  }

  if (
    cell.availability === "unsupported" &&
    cell.completeness_reason_code === "not_applicable"
  ) {
    return null;
  }

  return formatCompletenessReasonCopy({
    reasonCode: cell.completeness_reason_code
  });
}

function buildBenchmarkLabel(
  benchmark: SchoolCompareBenchmark | null,
  unit: string
): string | null {
  if (!benchmark) {
    return null;
  }

  const national = formatBenchmarkValue(benchmark.national_value, unit);
  const local = formatBenchmarkValue(benchmark.local_value, unit);
  const parts: string[] = [];

  if (national) {
    parts.push(`England ${national}`);
  }
  if (local) {
    parts.push(`${benchmark.local_area_label} ${local}`);
  }

  return parts.length > 0 ? parts.join(" | ") : null;
}

function formatBenchmarkValue(
  value: number | null,
  unit: string
): string | null {
  if (value === null) {
    return null;
  }

  switch (unit) {
    case "count":
      return Math.round(value).toLocaleString("en-GB");
    case "currency":
      if (value >= 1_000_000) {
        return `GBP ${(value / 1_000_000).toFixed(1)}m`;
      }
      if (value >= 1_000) {
        return `GBP ${Math.round(value / 1_000)}k`;
      }
      return `GBP ${Math.round(value)}`;
    case "percent":
      return `${value.toFixed(1)}%`;
    case "rate":
      return value.toFixed(2);
    case "ratio":
      return value.toFixed(1);
    case "score":
      return value.toFixed(2);
    default:
      return `${value}`;
  }
}
