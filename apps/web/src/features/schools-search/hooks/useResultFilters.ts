import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import type { SchoolSearchListItem } from "../types";

export interface Facet {
  label: string;
  count: number;
  selected: boolean;
}

export interface ResultFilters {
  /** Available phase facets with counts and selection state */
  phases: Facet[];
  /** Filtered results */
  filtered: SchoolSearchListItem[];
  /** Number of items hidden by active filters */
  hiddenCount: number;
  /** Whether any filter is active */
  hasActiveFilters: boolean;
  /** Toggle a phase facet on/off */
  togglePhase: (label: string) => void;
  /** Clear all active filters */
  clearFilters: () => void;
}

/**
 * Client-side faceted filtering of search results by phase.
 *
 * When no chips are selected the full result set passes through (inclusive default).
 * When one or more chips are selected, only matching items are kept.
 */
export function useResultFilters(schools: SchoolSearchListItem[]): ResultFilters {
  const [selectedPhases, setSelectedPhases] = useState<Set<string>>(new Set());

  // Reset selections when result set changes (new search)
  const prevSchoolsRef = useRef(schools);
  useEffect(() => {
    if (prevSchoolsRef.current !== schools) {
      prevSchoolsRef.current = schools;
      // Only update state when there are active selections to clear,
      // returning the same reference lets React bail out of re-rendering.
      setSelectedPhases((prev) => (prev.size === 0 ? prev : new Set()));
    }
  }, [schools]);

  // Build facet maps from the full (unfiltered) result set
  const phaseCounts = useMemo(() => {
    const map = new Map<string, number>();
    for (const s of schools) {
      const key = s.phase ?? "Unknown";
      map.set(key, (map.get(key) ?? 0) + 1);
    }
    return map;
  }, [schools]);

  // Sorted facet array
  const phases: Facet[] = useMemo(
    () =>
      [...phaseCounts.entries()]
        .sort((a, b) => b[1] - a[1])
        .map(([label, count]) => ({ label, count, selected: selectedPhases.has(label) })),
    [phaseCounts, selectedPhases]
  );

  // Filtered results
  const filtered = useMemo(() => {
    if (selectedPhases.size === 0) return schools;
    return schools.filter((s) => selectedPhases.has(s.phase ?? "Unknown"));
  }, [schools, selectedPhases]);

  const hasActiveFilters = selectedPhases.size > 0;
  const hiddenCount = schools.length - filtered.length;

  const togglePhase = useCallback((label: string) => {
    setSelectedPhases((prev) => {
      const next = new Set(prev);
      if (next.has(label)) {
        next.delete(label);
      } else {
        next.add(label);
      }
      return next;
    });
  }, []);

  const clearFilters = useCallback(() => {
    setSelectedPhases(new Set());
  }, []);

  return {
    phases,
    filtered,
    hiddenCount,
    hasActiveFilters,
    togglePhase,
    clearFilters,
  };
}
