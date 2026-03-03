import { SearchX } from "lucide-react";

import { Button } from "../../../components/ui/Button";
import { EmptyState } from "../../../components/ui/EmptyState";
import { ErrorState } from "../../../components/ui/ErrorState";
import { LoadingSkeleton } from "../../../components/ui/LoadingSkeleton";
import { Panel } from "../../../components/ui/Card";
import { ResultCard } from "../../../components/ui/ResultCard";
import { paths } from "../../../shared/routing/paths";
import type { SchoolsSearchStatus, SchoolSearchListItem } from "../types";

interface SearchQuery {
  postcode: string;
  radius: number;
}

interface SchoolsListProps {
  status: SchoolsSearchStatus;
  schools: SchoolSearchListItem[];
  errorMessage: string | null;
  onRetry: () => Promise<void>;
  searchContext?: SearchQuery;
}

function toDisplayValue(value: string | null): string {
  return value ?? "Not available";
}

function ResultsList({
  schools,
  searchContext,
}: {
  schools: SchoolSearchListItem[];
  searchContext?: SearchQuery;
}): JSX.Element {
  return (
    <>
      {schools.map((school, index) => (
        <ResultCard
          key={school.urn}
          name={school.name}
          type={toDisplayValue(school.type)}
          phase={toDisplayValue(school.phase)}
          postcode={toDisplayValue(school.postcode)}
          distanceMiles={school.distance_miles}
          href={paths.schoolProfile(school.urn)}
          linkState={searchContext ? { fromSearch: searchContext } : undefined}
          style={{ animationDelay: `${index * 60}ms` }}
        />
      ))}
    </>
  );
}

export function SchoolsList({
  status,
  schools,
  errorMessage,
  onRetry,
  searchContext,
}: SchoolsListProps): JSX.Element {
  if (status === "loading") {
    return <LoadingSkeleton variant="result-card" count={4} />;
  }

  if (status === "error" && schools.length > 0) {
    return (
      <>
        <div
          role="alert"
          className="flex items-center justify-between gap-3 rounded-lg border border-danger/60 bg-danger/10 px-4 py-3"
        >
          <p className="flex-1 text-sm text-secondary">
            {errorMessage ?? "Search update failed. Showing previous results."}
          </p>
          <Button
            type="button"
            variant="secondary"
            onClick={() => {
              void onRetry();
            }}
          >
            Retry
          </Button>
        </div>
        <ResultsList schools={schools} searchContext={searchContext} />
      </>
    );
  }

  if (status === "error") {
    return (
      <ErrorState
        title="Search temporarily unavailable"
        description={errorMessage ?? "Please retry your search."}
        onRetry={() => {
          void onRetry();
        }}
      />
    );
  }

  if (status === "empty") {
    return (
      <EmptyState
        icon={<SearchX className="h-8 w-8" />}
        title="No schools found"
        description={
          searchContext
            ? `No schools within ${searchContext.radius} miles of ${searchContext.postcode}. Try a wider radius or a nearby postcode.`
            : "Try a wider radius or a nearby postcode to broaden the search area."
        }
      />
    );
  }

  if (status === "success") {
    return <ResultsList schools={schools} searchContext={searchContext} />;
  }

  return (
    <Panel>
      <p className="text-sm text-secondary">
        Search for nearby schools by postcode to load results.
      </p>
    </Panel>
  );
}
