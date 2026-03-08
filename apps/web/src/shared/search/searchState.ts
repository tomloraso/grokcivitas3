export type SearchViewMode = "map" | "results";

export type SearchSortMode = "closest" | "ofsted" | "academic";

export type SearchPhaseFilter = "primary" | "secondary";

const SEARCH_PHASE_ORDER: readonly SearchPhaseFilter[] = ["primary", "secondary"];

export const DEFAULT_SEARCH_SORT_MODE: SearchSortMode = "closest";

export function normalizeSearchPhaseFilters(
  phases: readonly string[] | null | undefined
): SearchPhaseFilter[] {
  if (!phases) {
    return [];
  }

  const normalized = new Set<SearchPhaseFilter>();
  for (const phase of phases) {
    if (typeof phase !== "string") {
      continue;
    }

    const candidate = phase.trim().toLowerCase();
    if (candidate === "primary" || candidate === "secondary") {
      normalized.add(candidate);
    }
  }

  return SEARCH_PHASE_ORDER.filter((phase) => normalized.has(phase));
}

export function normalizeSearchSortMode(sort: string | null | undefined): SearchSortMode {
  if (typeof sort !== "string") {
    return DEFAULT_SEARCH_SORT_MODE;
  }

  const candidate = sort.trim().toLowerCase();
  if (candidate === "ofsted" || candidate === "academic") {
    return candidate;
  }

  return DEFAULT_SEARCH_SORT_MODE;
}

export function canUseAcademicSort(phases: readonly SearchPhaseFilter[]): boolean {
  return phases.length === 1;
}

export interface SearchRestoreState {
  postcode: string;
  radius: number;
  view?: SearchViewMode;
  resultsPhases?: SearchPhaseFilter[];
  resultsSort?: SearchSortMode;
}
