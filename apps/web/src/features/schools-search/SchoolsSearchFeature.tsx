import { AppShell } from "../../components/layout/AppShell";
import { PageContainer } from "../../components/layout/PageContainer";
import { SplitPaneLayout } from "../../components/layout/SplitPaneLayout";
import { SearchForm } from "./components/SearchForm";
import { SchoolsList } from "./components/SchoolsList";
import { SchoolsMap } from "./components/SchoolsMap";
import { useSchoolsSearch } from "./hooks/useSchoolsSearch";

export function SchoolsSearchFeature(): JSX.Element {
  const { form, state, setPostcode, setRadius, submitSearch } = useSchoolsSearch();

  return (
    <AppShell>
      <PageContainer className="space-y-6">
        <header className="panel-surface rounded-xl p-5 sm:p-7">
          <p className="font-mono text-xs uppercase tracking-[0.14em] text-secondary">
            Phase 0D2 Search And Map
          </p>
          <h1 className="mt-2 text-3xl leading-tight sm:text-4xl">Civitas Schools Discovery</h1>
          <p className="mt-3 max-w-2xl text-sm text-secondary sm:text-base">
            Search by UK postcode to explore nearby schools in a shared list and map view.
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

        <SplitPaneLayout
          listPane={
            <SchoolsList
              status={state.status}
              schools={state.result?.schools ?? []}
              errorMessage={state.errorMessage}
              onRetry={submitSearch}
            />
          }
          mapPane={
            <SchoolsMap
              status={state.status}
              center={state.result?.center ?? null}
              schools={state.result?.schools ?? []}
            />
          }
        />
      </PageContainer>
    </AppShell>
  );
}
