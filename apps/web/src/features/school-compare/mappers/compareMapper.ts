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
  CompareSectionVM,
  CompareSchoolColumnVM
} from "../types";

/* ------------------------------------------------------------------ */
/* Section relabelling & ordering — align with school profile          */
/* ------------------------------------------------------------------ */

/** Map backend section keys → profile-matching display labels */
const SECTION_LABEL_MAP: Record<string, string> = {
  inspection: "Ofsted Profile",
  performance: "Results & Progress",
  attendance: "Day-to-Day at School",
  behaviour: "Day-to-Day at School",
  demographics: "Pupil Demographics",
  workforce: "Teachers & Staff",
  finance: "School Finance",
  admissions: "School Admissions",
  destinations: "Leaver Destinations",
  area: "Neighbourhood Context",
};

/** Canonical section order matching the school profile layout */
const SECTION_ORDER: string[] = [
  "Ofsted Profile",
  "Results & Progress",
  "Day-to-Day at School",
  "Pupil Demographics",
  "Teachers & Staff",
  "School Finance",
  "School Admissions",
  "Leaver Destinations",
  "Neighbourhood Context",
];

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
    sections: relabelMergeAndOrder(
      (response.sections ?? []).map((section) => ({
        key: section.key,
        label: SECTION_LABEL_MAP[section.key] ?? section.label,
        rows: (section.rows ?? []).map((row) => ({
          metricKey: row.metric_key,
          label: row.label,
          unit: row.unit,
          cells: (row.cells ?? []).map((cell) => mapCellToVM(cell, row.unit))
        }))
      }))
    )
  };
}

/**
 * Merge sections that share the same label (e.g. attendance + behaviour
 * → "Day-to-Day at School") and enforce canonical profile order.
 */
function relabelMergeAndOrder(sections: CompareSectionVM[]): CompareSectionVM[] {
  // Merge sections with the same label
  const merged = new Map<string, CompareSectionVM>();
  for (const section of sections) {
    const existing = merged.get(section.label);
    if (existing) {
      existing.rows.push(...section.rows);
    } else {
      merged.set(section.label, { ...section, rows: [...section.rows] });
    }
  }

  // Sort by SECTION_ORDER, unknown sections go to the end
  const result = [...merged.values()];
  result.sort((a, b) => {
    const ai = SECTION_ORDER.indexOf(a.label);
    const bi = SECTION_ORDER.indexOf(b.label);
    return (ai === -1 ? 999 : ai) - (bi === -1 ? 999 : bi);
  });

  return result;
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

  // Section-level concerns — noisy when repeated in every cell
  if (
    cell.completeness_reason_code === "partial_metric_coverage" ||
    cell.completeness_reason_code === "insufficient_years_published"
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
