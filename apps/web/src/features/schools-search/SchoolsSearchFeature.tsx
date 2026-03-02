import { MapOverlayLayout } from "../../components/layout/MapOverlayLayout";
import { SearchForm } from "./components/SearchForm";
import { SchoolsList } from "./components/SchoolsList";
import { SchoolsMap } from "./components/SchoolsMap";
import { useSchoolsSearch } from "./hooks/useSchoolsSearch";

export function SchoolsSearchFeature(): JSX.Element {
  const { form, state, setPostcode, setRadius, submitSearch } = useSchoolsSearch();

  return (
    <MapOverlayLayout
      map={
        <SchoolsMap
          status={state.status}
          center={state.result?.center ?? null}
          schools={state.result?.schools ?? []}
        />
      }
    >
      <div className="space-y-5 p-4 sm:p-5">
        <header>
          <p className="font-mono text-xs uppercase tracking-[0.14em] text-secondary">
            Schools Discovery
          </p>
          <h1 className="mt-2 text-4xl leading-tight sm:text-5xl">Find schools near you</h1>
          <p className="mt-3 text-sm text-secondary sm:text-base">
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
        className="space-y-4 border-t border-border-subtle/70 px-4 pb-5 pt-5 sm:px-5"
      >
        {state.status === "success" && state.result ? (
          <p className="text-sm text-secondary">
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
        />
      </section>
    </MapOverlayLayout>
  );
}
