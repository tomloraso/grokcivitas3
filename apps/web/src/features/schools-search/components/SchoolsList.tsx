import { useMemo, useState } from "react";

import { Button } from "../../../components/ui/Button";
import { EmptyState } from "../../../components/ui/EmptyState";
import { MapEmptyState } from "../../../components/ui/EmptyState";
import { ErrorState } from "../../../components/ui/ErrorState";
import { LoadingSkeleton } from "../../../components/ui/LoadingSkeleton";
import { Panel } from "../../../components/ui/Card";
import { ResultCard } from "../../../components/ui/ResultCard";
import { useToast } from "../../../components/ui/ToastContext";
import { useCompareSelection } from "../../../shared/context/CompareSelectionContext";
import { paths } from "../../../shared/routing/paths";
import type { SearchRestoreState } from "../../../shared/search/searchState";
import type { SchoolsSearchStatus, SchoolSearchListItem } from "../types";

interface PhaseGroup {
  phase: string;
  schools: SchoolSearchListItem[];
}

interface SchoolsListProps {
  status: SchoolsSearchStatus;
  schools: SchoolSearchListItem[];
  errorMessage: string | null;
  onRetry: () => Promise<void>;
  searchContext?: SearchRestoreState;
  activeSchoolId?: string | null;
  onSchoolHover?: (id: string | null) => void;
  onPreviewSchool?: (schoolId: string) => void;
  isNameSearch?: boolean;
  nameSearchQuery?: string;
}

function toDisplayValue(value: string | null): string {
  return value ?? "Not available";
}

/**
 * Canonical education-phase ordering.
 * Phases progress from youngest to oldest; "Not applicable" and "Unknown" sort last.
 */
const PHASE_ORDER: Record<string, number> = {
  "Nursery": 0,
  "Primary": 1,
  "Middle deemed primary": 2,
  "Secondary": 3,
  "Middle deemed secondary": 4,
  "All-through": 5,
  "16 plus": 6,
  "Not applicable": 97,
  "Unknown": 99,
};

function phaseRank(phase: string): number {
  return PHASE_ORDER[phase] ?? 98; // unseen phases just before Unknown
}

/** Group schools by phase, ordered by education progression. */
function groupByPhase(schools: SchoolSearchListItem[]): PhaseGroup[] {
  const groupMap = new Map<string, SchoolSearchListItem[]>();
  for (const school of schools) {
    const key = school.phase ?? "Unknown";
    const group = groupMap.get(key);
    if (group) {
      group.push(school);
    } else {
      groupMap.set(key, [school]);
    }
  }

  const entries = [...groupMap.entries()];
  entries.sort((a, b) => phaseRank(a[0]) - phaseRank(b[0]));

  return entries.map(([phase, items]) => ({ phase, schools: items }));
}

function toCompareSelectionItem(school: SchoolSearchListItem) {
  return {
    urn: school.urn,
    name: school.name,
    phase: school.phase,
    type: school.type,
    postcode: school.postcode,
    distanceMiles: school.distance_miles,
    source: "search" as const,
  };
}

function PhaseGroupSection({
  group,
  searchContext,
  activeSchoolId,
  onSchoolHover,
  onPreviewSchool,
  globalIndex,
  isNameSearch,
  renderCompareAction,
}: {
  group: PhaseGroup;
  searchContext?: SearchRestoreState;
  activeSchoolId?: string | null;
  onSchoolHover?: (id: string | null) => void;
  onPreviewSchool?: (schoolId: string) => void;
  globalIndex: number;
  isNameSearch?: boolean;
  renderCompareAction: (school: SchoolSearchListItem) => JSX.Element;
}): JSX.Element {
  const [expanded, setExpanded] = useState(true);

  return (
    <div role="group" aria-labelledby={`phase-header-${group.phase}`}>
      <button
        id={`phase-header-${group.phase}`}
        type="button"
        onClick={() => setExpanded((v) => !v)}
        className="sticky top-0 z-10 flex w-full items-center gap-2 rounded-lg bg-surface-raised/95 px-3 py-2 text-left backdrop-blur-sm transition-colors hover:bg-surface-raised"
        aria-expanded={expanded}
      >
        <svg
          className={`h-4 w-4 shrink-0 text-secondary transition-transform ${expanded ? "rotate-90" : ""}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
        </svg>
        <span className="text-sm font-semibold text-primary">{group.phase}</span>
        <span className="ml-auto rounded-full bg-brand/10 px-2 py-0.5 text-xs font-medium text-brand">
          {group.schools.length}
        </span>
      </button>
      {expanded && (
        <div className="mt-2 space-y-3">
          {group.schools.map((school, index) => (
            <ResultCard
              key={school.urn}
              id={school.urn}
              name={school.name}
              type={toDisplayValue(school.type)}
              phase={toDisplayValue(school.phase)}
              postcode={toDisplayValue(school.postcode)}
              distanceMiles={isNameSearch ? undefined : school.distance_miles}
              href={paths.schoolProfile(school.urn)}
              linkState={searchContext ? { fromSearch: searchContext } : undefined}
              style={{ animationDelay: `${(globalIndex + index) * 60}ms` }}
              isActive={activeSchoolId === school.urn}
              onHover={onSchoolHover}
              onNavigateIntent={onPreviewSchool}
              actions={renderCompareAction(school)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function ResultsList({
  schools,
  searchContext,
  activeSchoolId,
  onSchoolHover,
  onPreviewSchool,
  isNameSearch,
  renderCompareAction,
}: {
  schools: SchoolSearchListItem[];
  searchContext?: SearchRestoreState;
  activeSchoolId?: string | null;
  onSchoolHover?: (id: string | null) => void;
  onPreviewSchool?: (schoolId: string) => void;
  isNameSearch?: boolean;
  renderCompareAction: (school: SchoolSearchListItem) => JSX.Element;
}): JSX.Element {
  const groups = useMemo(() => groupByPhase(schools), [schools]);

  if (groups.length <= 1) {
    // Single group or empty — no headers needed
    return (
      <>
        {schools.map((school, index) => (
          <ResultCard
            key={school.urn}
            id={school.urn}
            name={school.name}
            type={toDisplayValue(school.type)}
            phase={toDisplayValue(school.phase)}
            postcode={toDisplayValue(school.postcode)}
            distanceMiles={isNameSearch ? undefined : school.distance_miles}
            href={paths.schoolProfile(school.urn)}
            linkState={searchContext ? { fromSearch: searchContext } : undefined}
            style={{ animationDelay: `${index * 60}ms` }}
            isActive={activeSchoolId === school.urn}
            onHover={onSchoolHover}
            onNavigateIntent={onPreviewSchool}
            actions={renderCompareAction(school)}
          />
        ))}
      </>
    );
  }

  let globalIndex = 0;
  return (
    <div className="space-y-4">
      {groups.map((group) => {
        const startIndex = globalIndex;
        globalIndex += group.schools.length;
        return (
          <PhaseGroupSection
            key={group.phase}
            group={group}
            searchContext={searchContext}
            activeSchoolId={activeSchoolId}
            onSchoolHover={onSchoolHover}
            onPreviewSchool={onPreviewSchool}
            globalIndex={startIndex}
            isNameSearch={isNameSearch}
            renderCompareAction={renderCompareAction}
          />
        );
      })}
    </div>
  );
}

export function SchoolsList({
  status,
  schools,
  errorMessage,
  onRetry,
  searchContext,
  activeSchoolId,
  onSchoolHover,
  onPreviewSchool,
  isNameSearch,
  nameSearchQuery,
}: SchoolsListProps): JSX.Element {
  const { toast } = useToast();
  const { addSchool, count, hasSchool, removeSchool } = useCompareSelection();

  const renderCompareAction = (school: SchoolSearchListItem) => {
    const selected = hasSchool(school.urn);

    return (
      <>
        <p className="text-xs text-secondary">
          {selected ? "Included in compare" : `Add up to ${4 - count} more`}
        </p>
        <Button
          type="button"
          variant={selected ? "ghost" : "secondary"}
          size="sm"
          onClick={() => {
            if (selected) {
              removeSchool(school.urn);
              return;
            }

            const result = addSchool(toCompareSelectionItem(school));
            if (result === "limit") {
              toast({
                title: "Compare limit reached",
                description: "You can compare up to four schools at a time.",
                variant: "warning",
              });
            }
          }}
        >
          {selected ? "Remove" : "Add to compare"}
        </Button>
      </>
    );
  };

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
        <ResultsList
          schools={schools}
          searchContext={searchContext}
          activeSchoolId={activeSchoolId}
          onSchoolHover={onSchoolHover}
          onPreviewSchool={onPreviewSchool}
          isNameSearch={isNameSearch}
          renderCompareAction={renderCompareAction}
        />
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
    if (isNameSearch) {
      return (
        <EmptyState
          title="No schools found"
          description={
            nameSearchQuery && nameSearchQuery.trim().length > 0
              ? `No schools match "${nameSearchQuery}". Try a shorter or alternative school name.`
              : "No schools match that name. Try a shorter or alternative school name."
          }
        />
      );
    }

    return (
      <MapEmptyState
        postcode={searchContext?.postcode}
        radiusMiles={searchContext?.radius}
      />
    );
  }

  if (status === "success") {
    return (
      <ResultsList
        schools={schools}
        searchContext={searchContext}
        activeSchoolId={activeSchoolId}
        onSchoolHover={onSchoolHover}
        onPreviewSchool={onPreviewSchool}
        isNameSearch={isNameSearch}
        renderCompareAction={renderCompareAction}
      />
    );
  }

  return (
    <Panel>
      <p className="text-sm text-secondary">
        Search for nearby schools by postcode or name to load results.
      </p>
    </Panel>
  );
}
