import { useCallback, useEffect, useMemo, useState } from "react";
import { useLocation, useSearchParams } from "react-router-dom";

import { prefetchSchoolProfile } from "../../api/client";
import { MapOverlayLayout } from "../../components/layout/MapOverlayLayout";
import { useSearchContext } from "../../shared/context/SearchContext";
import {
  DEFAULT_SEARCH_SORT_MODE,
  normalizeSearchPhaseFilters,
  normalizeSearchSortMode,
  type SearchPhaseFilter,
  type SearchRestoreState,
  type SearchSortMode,
  type SearchViewMode,
} from "../../shared/search/searchState";
import { FilterChips } from "./components/FilterChips";
import { ResultsOverlay } from "./components/ResultsOverlay";
import { SearchForm } from "./components/SearchForm";
import { SearchModeSwitch } from "./components/SearchModeSwitch";
import { SchoolsList } from "./components/SchoolsList";
import { SchoolsMap } from "./components/SchoolsMap";
import { useResultFilters } from "./hooks/useResultFilters";
import { useResultsMode } from "./hooks/useResultsMode";
import { useSchoolsSearch } from "./hooks/useSchoolsSearch";
import { isPostcodeSearchResult, type SchoolSearchListItem } from "./types";

const EMPTY_SCHOOLS: SchoolSearchListItem[] = [];

function buildResultsSearchParams({
  view,
  phases,
  sort,
}: {
  view: SearchViewMode;
  phases: readonly SearchPhaseFilter[];
  sort: SearchSortMode;
}): URLSearchParams {
  const params = new URLSearchParams();
  if (view === "results") {
    params.set("view", "results");
    params.set("sort", sort);
    for (const phase of phases) {
      params.append("phase", phase);
    }
  }
  return params;
}

export function SchoolsSearchFeature(): JSX.Element {
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();
  const restoreSearch = (location.state as { restoreSearch?: SearchRestoreState } | null)
    ?.restoreSearch;
  const viewParam = searchParams.get("view");
  const activeView: SearchViewMode =
    viewParam === "results" || viewParam === "shortlist" ? "results" : "map";
  const resultsPhases = useMemo(
    () => normalizeSearchPhaseFilters(searchParams.getAll("phase")),
    [searchParams],
  );
  const rawResultsSort = normalizeSearchSortMode(searchParams.get("sort"));
  const resultsSort = rawResultsSort === "ofsted" ? "ofsted" : DEFAULT_SEARCH_SORT_MODE;

  const { form, state, searchMode, setSearchText, setRadius, submitSearch } = useSchoolsSearch(
    restoreSearch
      ? {
          initialPostcode: restoreSearch.postcode,
          initialRadius: restoreSearch.radius,
          autoSubmit: true,
        }
      : undefined,
  );
  const { setSearch, clearSearch } = useSearchContext();
  const [activeSchoolId, setActiveSchoolId] = useState<string | null>(null);
  const handleSchoolHover = useCallback((id: string | null) => setActiveSchoolId(id), []);
  const handlePreviewSchool = useCallback((schoolId: string) => {
    prefetchSchoolProfile(schoolId);
  }, []);

  const postcodeResult = isPostcodeSearchResult(state.result) ? state.result : null;
  const nameResult = state.result?.mode === "name" ? state.result : null;
  const resultsMode = useResultsMode({
    baseResult: postcodeResult,
    isOpen: activeView === "results",
    phases: resultsPhases,
    sort: resultsSort,
  });

  const allSchools = state.result?.schools ?? EMPTY_SCHOOLS;
  const {
    phases,
    filtered: filteredSchools,
    hiddenCount,
    hasActiveFilters,
    togglePhase,
    clearFilters,
  } = useResultFilters(allSchools);

  const resultPostcode = postcodeResult?.query.postcode;
  const resultRadius = postcodeResult?.query.radius_miles;
  const resultCount = state.result?.count;

  useEffect(() => {
    if (activeView === "results" && rawResultsSort !== resultsSort) {
      setSearchParams(
        buildResultsSearchParams({
          view: "results",
          phases: resultsPhases,
          sort: resultsSort,
        }),
        { replace: true },
      );
    }
  }, [
    activeView,
    rawResultsSort,
    setSearchParams,
    resultsPhases,
    resultsSort,
  ]);

  useEffect(() => {
    if (state.status === "success" && resultPostcode) {
      setSearch({
        postcode: resultPostcode,
        radius: resultRadius ?? 0,
        count: resultCount ?? 0,
      });
      return;
    }

    if (searchMode === "name") {
      clearSearch();
    }
  }, [
    clearSearch,
    resultCount,
    resultPostcode,
    resultRadius,
    searchMode,
    setSearch,
    state.status,
  ]);

  useEffect(() => {
    if (activeView === "results" && searchMode !== "postcode") {
      setSearchParams(new URLSearchParams(), { replace: true });
    }
  }, [activeView, searchMode, setSearchParams]);

  const handleOpenResults = useCallback(() => {
    setSearchParams(
      buildResultsSearchParams({
        view: "results",
        phases: resultsPhases,
        sort: resultsSort,
      }),
    );
  }, [setSearchParams, resultsPhases, resultsSort]);

  const handleCloseResults = useCallback(() => {
    setActiveSchoolId(null);
    setSearchParams(new URLSearchParams(), { replace: true });
  }, [setSearchParams]);

  const handleResultsPhasesChange = useCallback(
    (nextPhases: SearchPhaseFilter[]) => {
      setSearchParams(
        buildResultsSearchParams({
          view: "results",
          phases: nextPhases,
          sort: resultsSort,
        }),
        { replace: true },
      );
    },
    [setSearchParams, resultsSort],
  );

  const handleResultsSortChange = useCallback(
    (nextSort: SearchSortMode) => {
      setSearchParams(
        buildResultsSearchParams({
          view: "results",
          phases: resultsPhases,
          sort: nextSort,
        }),
        { replace: true },
      );
    },
    [setSearchParams, resultsPhases],
  );

  const hasResults = (state.status === "success" || state.status === "error") && state.result;
  const isPostcodeMode = postcodeResult != null;

  return (
    <>
      <MapOverlayLayout
        map={
          <SchoolsMap
            status={state.status}
            center={postcodeResult?.center ?? null}
            radiusMiles={postcodeResult?.query.radius_miles}
            schools={filteredSchools}
            activeSchoolId={activeSchoolId}
            onSchoolHover={handleSchoolHover}
            fitBounds={nameResult != null}
          />
        }
      >
        <div className="panel-content-enter space-y-6 p-4 sm:p-5">
          <header className="space-y-3">
            <p className="eyebrow">Schools Discovery</p>
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

        {hasResults && allSchools.length > 0 ? (
          <FilterChips
            phases={phases}
            hasActiveFilters={hasActiveFilters}
            hiddenCount={hiddenCount}
            onTogglePhase={togglePhase}
            onClear={clearFilters}
          />
        ) : null}

        <section
          aria-label="School results"
          className="results-reveal space-y-4 border-t border-border-subtle/70 px-4 pb-5 pt-6 sm:px-5"
        >
          {hasResults ? (
            <div className="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
              <p className="text-sm text-secondary" data-testid="result-summary">
                {postcodeResult ? (
                  hasActiveFilters ? (
                    <>
                      <span className="font-semibold text-primary">{filteredSchools.length}</span>{" "}
                      of <span className="font-semibold text-primary">{postcodeResult.count}</span>{" "}
                      {postcodeResult.count === 1 ? "school" : "schools"} within{" "}
                      <span className="font-semibold text-primary">
                        {postcodeResult.query.radius_miles} miles
                      </span>{" "}
                      of{" "}
                      <span className="font-mono font-semibold text-primary">
                        {postcodeResult.query.postcode}
                      </span>
                    </>
                  ) : (
                    <>
                      <span className="font-semibold text-primary">{postcodeResult.count}</span>{" "}
                      {postcodeResult.count === 1 ? "school" : "schools"} within{" "}
                      <span className="font-semibold text-primary">
                        {postcodeResult.query.radius_miles} miles
                      </span>{" "}
                      of{" "}
                      <span className="font-mono font-semibold text-primary">
                        {postcodeResult.query.postcode}
                      </span>
                    </>
                  )
                ) : (
                  <>
                    <span className="font-semibold text-primary">
                      {hasActiveFilters ? filteredSchools.length : nameResult?.count ?? 0}
                    </span>{" "}
                    {(hasActiveFilters ? filteredSchools.length : nameResult?.count ?? 0) === 1
                      ? "school"
                      : "schools"}{" "}
                    matching{" "}
                    <span className="font-semibold text-primary">
                      &ldquo;{nameResult?.nameQuery ?? form.searchText.trim()}&rdquo;
                    </span>
                  </>
                )}
              </p>

              {isPostcodeMode ? (
                <SearchModeSwitch
                  activeView={activeView}
                  resultsEnabled={postcodeResult.count > 0}
                  onMapSelect={handleCloseResults}
                  onResultsSelect={handleOpenResults}
                />
              ) : null}
            </div>
          ) : null}

          <SchoolsList
            status={state.status}
            schools={filteredSchools}
            errorMessage={state.errorMessage}
            onRetry={submitSearch}
            searchContext={
              postcodeResult
                ? {
                    postcode: postcodeResult.query.postcode,
                    radius: postcodeResult.query.radius_miles,
                    view: "map",
                  }
                : undefined
            }
            activeSchoolId={activeSchoolId}
            onSchoolHover={handleSchoolHover}
            onPreviewSchool={handlePreviewSchool}
            isNameSearch={nameResult != null}
            nameSearchQuery={nameResult?.nameQuery}
          />
        </section>
      </MapOverlayLayout>

      <ResultsOverlay
        open={activeView === "results"}
        status={resultsMode.status}
        result={resultsMode.result}
        errorMessage={resultsMode.errorMessage}
        phases={resultsPhases}
        sort={resultsSort}
        onClose={handleCloseResults}
        onRetry={resultsMode.retry}
        onPhasesChange={handleResultsPhasesChange}
        onSortChange={handleResultsSortChange}
        activeSchoolId={activeSchoolId}
        onSchoolHover={handleSchoolHover}
        onPreviewSchool={handlePreviewSchool}
      />
    </>
  );
}
