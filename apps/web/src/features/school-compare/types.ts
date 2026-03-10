import type { SectionAccessVM } from "../premium-access/types";

export type CompareCellAvailability = "available" | "unsupported" | "unavailable" | "suppressed";

export interface CompareSchoolColumnVM {
  urn: string;
  name: string;
  phase: string;
  type: string;
  postcode: string;
  ageRangeLabel: string | null;
  distanceLabel: string | null;
  profileHref: string;
  profileState: { fromCompare: { href: string } };
}

export interface CompareCellVM {
  urn: string;
  displayValue: string;
  availability: CompareCellAvailability;
  metaLabel: string | null;
  detailLabel: string | null;
  benchmarkLabel: string | null;
  isMuted: boolean;
}

export interface CompareRowVM {
  metricKey: string;
  label: string;
  unit: string;
  cells: CompareCellVM[];
}

export interface CompareSectionVM {
  key: string;
  label: string;
  rows: CompareRowVM[];
}

export interface ComparePageVM {
  access: SectionAccessVM;
  schools: CompareSchoolColumnVM[];
  sections: CompareSectionVM[];
}
