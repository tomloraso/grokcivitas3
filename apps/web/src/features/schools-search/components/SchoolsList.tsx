import { EmptyState } from "../../../components/ui/EmptyState";
import { ErrorState } from "../../../components/ui/ErrorState";
import { LoadingSkeleton } from "../../../components/ui/LoadingSkeleton";
import { Panel } from "../../../components/ui/Card";
import { ResultCard } from "../../../components/ui/ResultCard";
import type { SchoolsSearchStatus, SchoolSearchListItem } from "../types";

interface SchoolsListProps {
  status: SchoolsSearchStatus;
  schools: SchoolSearchListItem[];
  errorMessage: string | null;
  onRetry: () => Promise<void>;
}

function toDisplayValue(value: string | null): string {
  return value ?? "Not available";
}

export function SchoolsList({
  status,
  schools,
  errorMessage,
  onRetry
}: SchoolsListProps): JSX.Element {
  if (status === "loading") {
    return <LoadingSkeleton lines={6} />;
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
        title="No schools found"
        description="Try a wider radius or a nearby postcode to broaden the search area."
      />
    );
  }

  if (status === "success") {
    return (
      <>
        {schools.map((school) => (
          <ResultCard
            key={school.urn}
            name={school.name}
            type={toDisplayValue(school.type)}
            phase={toDisplayValue(school.phase)}
            postcode={toDisplayValue(school.postcode)}
            distanceMiles={school.distance_miles}
          />
        ))}
      </>
    );
  }

  return (
    <Panel>
      <p className="text-sm text-secondary">
        Search for nearby schools by postcode to load results.
      </p>
    </Panel>
  );
}
