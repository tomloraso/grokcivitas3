import { useEffect } from "react";

import { MapOverlayLayout } from "../../components/layout/MapOverlayLayout";
import { useSearchContext } from "../../shared/context/SearchContext";
import { SearchForm } from "./components/SearchForm";
import { SchoolsList } from "./components/SchoolsList";
import { SchoolsMap } from "./components/SchoolsMap";
import { useSchoolsSearch } from "./hooks/useSchoolsSearch";

/** Compact vertical summary shown in the collapsed rail on desktop */
function CollapsedSummary({
  count,
  radius,
  postcode,
}: {
  count: number | null;
  radius: string | null;
  postcode: string | null;
}): JSX.Element | null {
  if (count === null) return null;
  return (
    <>
      <span className="text-lg font-semibold text-primary">{count}</span>
      <span className="text-[10px] uppercase tracking-wide">schools</span>
      {radius ? (
        <span className="mt-1 text-[10px] uppercase tracking-wide">{radius} mi</span>
      ) : null}
      {postcode ? (
        <span className="mt-1 font-mono text-[10px] text-primary">{postcode}</span>
      ) : null}
    </>
  );
}

export function SchoolsSearchFeature(): JSX.Element {
  const { form, state, setPostcode, setRadius, submitSearch } = useSchoolsSearch();
  const { setSearch } = useSearchContext();

  useEffect(() => {
    if (state.status === "success" && state.result) {
      setSearch({
        postcode: state.result.query.postcode,
        radius: state.result.query.radius_miles,
        count: state.result.count,
      });
    }
  }, [state.status, state.result, setSearch]);

  const resultSummary =
    (state.status === "success" || state.status === "error") && state.result ? (
      <CollapsedSummary
        count={state.result.count}
        radius={String(state.result.query.radius_miles)}
        postcode={state.result.query.postcode}
      />
    ) : null;

  return (
    <MapOverlayLayout
      map={
        <SchoolsMap
          status={state.status}
          center={state.result?.center ?? null}
          radiusMiles={state.result?.query.radius_miles}
          schools={state.result?.schools ?? []}
        />
      }
      summary={resultSummary}
    >
      <div className="panel-content-enter space-y-6 p-4 sm:p-5">
        <header className="space-y-3">
          <p className="eyebrow">
            Schools Discovery
          </p>
          <h1 className="text-4xl leading-tight sm:text-5xl">Find schools near you</h1>
          <p className="text-muted text-sm sm:text-base">
            Search by UK postcode to explore nearby schools in list and map view.
          </p>
        </header>

        <SearchForm
          postcode={form.postcode}
          radius={form.radius}
          postcodeError={form.postcodeError}
          isSubmitting={state.status === "loading"}
          onPostcodeChange={setPostcode}
          onRadiusChange={setRadius}
          onSubmit={submitSearch}
        />
      </div>

      <section
        aria-label="School results"
        className="results-reveal space-y-4 border-t border-border-subtle/70 px-4 pb-5 pt-6 sm:px-5"
      >
        {(state.status === "success" || state.status === "error") && state.result ? (
          <p className="text-sm text-secondary" data-testid="result-summary">
            <span className="font-semibold text-primary">{state.result.count}</span>{" "}
            {state.result.count === 1 ? "school" : "schools"} within{" "}
            <span className="font-semibold text-primary">{state.result.query.radius_miles} miles</span>{" "}
            of{" "}
            <span className="font-mono font-semibold text-primary">{state.result.query.postcode}</span>
          </p>
        ) : null}
        <SchoolsList
          status={state.status}
          schools={state.result?.schools ?? []}
          errorMessage={state.errorMessage}
          onRetry={submitSearch}
          searchContext={
            state.result?.query
              ? { postcode: state.result.query.postcode, radius: state.result.query.radius_miles }
              : undefined
          }
        />
      </section>
    </MapOverlayLayout>
  );
}
