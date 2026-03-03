import { useCallback, useEffect, useState } from "react";
import { useLocation } from "react-router-dom";

import { MapOverlayLayout } from "../../components/layout/MapOverlayLayout";
import { useSearchContext } from "../../shared/context/SearchContext";
import { FilterChips } from "./components/FilterChips";
import { SearchForm } from "./components/SearchForm";
import { SchoolsList } from "./components/SchoolsList";
import { SchoolsMap } from "./components/SchoolsMap";
import { useResultFilters } from "./hooks/useResultFilters";
import { useSchoolsSearch } from "./hooks/useSchoolsSearch";
import type { SchoolSearchListItem } from "./types";

const EMPTY_SCHOOLS: SchoolSearchListItem[] = [];

export function SchoolsSearchFeature(): JSX.Element {
  const location = useLocation();
  const restoreSearch = (location.state as { restoreSearch?: { postcode: string; radius: number } } | null)?.restoreSearch;
  const { form, state, searchMode, setSearchText, setRadius, submitSearch } = useSchoolsSearch(
    restoreSearch
      ? { initialPostcode: restoreSearch.postcode, initialRadius: restoreSearch.radius, autoSubmit: true }
      : undefined
  );
  const { setSearch, clearSearch } = useSearchContext();
  const [activeSchoolId, setActiveSchoolId] = useState<string | null>(null);
  const handleSchoolHover = useCallback((id: string | null) => setActiveSchoolId(id), []);

  // Client-side faceted filters — stable empty array prevents infinite re-renders
  const allSchools = state.result?.schools ?? EMPTY_SCHOOLS;
  const {
    phases, filtered: filteredSchools, hiddenCount, hasActiveFilters,
    togglePhase, clearFilters,
  } = useResultFilters(allSchools);

  // Derive primitive values so the effect doesn't depend on an object reference
  const resultMode = state.result?.mode;
  const resultPostcode = state.result?.query?.postcode;
  const resultRadius = state.result?.query?.radius_miles;
  const resultCount = state.result?.count;

  useEffect(() => {
    if (state.status === "success" && resultMode === "postcode" && resultPostcode) {
      setSearch({
        postcode: resultPostcode,
        radius: resultRadius!,
        count: resultCount!,
      });
      return;
    }
    if (searchMode === "name") {
      clearSearch();
    }
  }, [state.status, resultMode, resultPostcode, resultRadius, resultCount, searchMode, setSearch, clearSearch]);

  const hasResults = (state.status === "success" || state.status === "error") && state.result;
  const isPostcodeMode = state.result?.mode === "postcode";

  return (
    <MapOverlayLayout
      map={
        <SchoolsMap
          status={state.status}
          center={state.result?.center ?? null}
          radiusMiles={isPostcodeMode ? state.result?.query?.radius_miles : undefined}
          schools={filteredSchools}
          activeSchoolId={activeSchoolId}
          onSchoolHover={handleSchoolHover}
          fitBounds={state.result?.mode === "name"}
        />
      }
    >
      <div className="panel-content-enter space-y-6 p-4 sm:p-5">
        <header className="space-y-3">
          <p className="eyebrow">
            Schools Discovery
          </p>
          <h1 className="text-4xl leading-tight sm:text-5xl">Find schools near you</h1>
          <p className="text-muted text-sm sm:text-base">
            Search by UK postcode to explore nearby schools, or type a school name.
          </p>
        </header>

        <SearchForm
          searchText={form.searchText}
          radius={form.radius}
          searchError={form.searchError}
          searchMode={searchMode}
          isSubmitting={state.status === "loading"}
          onSearchTextChange={setSearchText}
          onRadiusChange={setRadius}
          onSubmit={submitSearch}
        />
      </div>

      {/* Filter chips — shown between form and results when we have data */}
      {hasResults && allSchools.length > 0 && (
        <FilterChips
          phases={phases}
          hasActiveFilters={hasActiveFilters}
          hiddenCount={hiddenCount}
          onTogglePhase={togglePhase}
          onClear={clearFilters}
        />
      )}

      <section
        aria-label="School results"
        className="results-reveal space-y-4 border-t border-border-subtle/70 px-4 pb-5 pt-6 sm:px-5"
      >
        {hasResults ? (
          <p className="text-sm text-secondary" data-testid="result-summary">
            {isPostcodeMode ? (
              hasActiveFilters ? (
                <>
                  <span className="font-semibold text-primary">{filteredSchools.length}</span>{" "}
                  of <span className="font-semibold text-primary">{state.result!.count}</span>{" "}
                  {state.result!.count === 1 ? "school" : "schools"} within{" "}
                  <span className="font-semibold text-primary">{state.result!.query!.radius_miles} miles</span>{" "}
                  of{" "}
                  <span className="font-mono font-semibold text-primary">{state.result!.query!.postcode}</span>
                </>
              ) : (
                <>
                  <span className="font-semibold text-primary">{state.result!.count}</span>{" "}
                  {state.result!.count === 1 ? "school" : "schools"} within{" "}
                  <span className="font-semibold text-primary">{state.result!.query!.radius_miles} miles</span>{" "}
                  of{" "}
                  <span className="font-mono font-semibold text-primary">{state.result!.query!.postcode}</span>
                </>
              )
            ) : (
              <>
                <span className="font-semibold text-primary">
                  {hasActiveFilters ? filteredSchools.length : state.result!.count}
                </span>{" "}
                {(hasActiveFilters ? filteredSchools.length : state.result!.count) === 1 ? "school" : "schools"}{" "}
                matching{" "}
                <span className="font-semibold text-primary">
                  &ldquo;{state.result?.nameQuery ?? form.searchText.trim()}&rdquo;
                </span>
              </>
            )}
          </p>
        ) : null}
        <SchoolsList
          status={state.status}
          schools={filteredSchools}
          errorMessage={state.errorMessage}
          onRetry={submitSearch}
          searchContext={
            state.result?.query
              ? { postcode: state.result.query.postcode, radius: state.result.query.radius_miles }
              : undefined
          }
          activeSchoolId={activeSchoolId}
          onSchoolHover={handleSchoolHover}
          isNameSearch={state.result?.mode === "name"}
          nameSearchQuery={state.result?.nameQuery}
        />
      </section>
    </MapOverlayLayout>
  );
}
