import { Link } from "react-router-dom";
import { ArrowUpDown, Sparkles, UsersRound, X } from "lucide-react";
import { useEffect } from "react";

import { RatingBadge } from "../../../components/data/RatingBadge";
import { Button } from "../../../components/ui/Button";
import { Panel } from "../../../components/ui/Card";
import { EmptyState } from "../../../components/ui/EmptyState";
import { ErrorState } from "../../../components/ui/ErrorState";
import { LoadingSkeleton } from "../../../components/ui/LoadingSkeleton";
import { useToast } from "../../../components/ui/ToastContext";
import { SaveSchoolButton } from "../../favourites/components/SaveSchoolButton";
import { mapSavedSchoolState } from "../../favourites/mappers";
import type { SavedSchoolStateVM } from "../../favourites/types";
import { CompareActionButton } from "../../premium-access/components/CompareActionButton";
import { useCompareSelection } from "../../../shared/context/CompareSelectionContext";
import { useIsMobile } from "../../../shared/hooks/useIsMobile";
import {
  type SearchPhaseFilter,
  type SearchRestoreState,
  type SearchSortMode,
} from "../../../shared/search/searchState";
import { paths } from "../../../shared/routing/paths";
import { cn } from "../../../shared/utils/cn";
import type {
  PostcodeSearchResult,
  SchoolsSearchStatus,
} from "../types";
import { SearchModeSwitch } from "./SearchModeSwitch";

interface ResultsOverlayProps {
  open: boolean;
  status: SchoolsSearchStatus;
  result: PostcodeSearchResult | null;
  savedStateByUrn: Record<string, SavedSchoolStateVM>;
  errorMessage: string | null;
  phases: readonly SearchPhaseFilter[];
  sort: SearchSortMode;
  onClose: () => void;
  onRetry: () => Promise<void>;
  onSavedStateChange: (urn: string, savedState: SavedSchoolStateVM) => void;
  onPhasesChange: (phases: SearchPhaseFilter[]) => void;
  onSortChange: (sort: SearchSortMode) => void;
  activeSchoolId?: string | null;
  onSchoolHover?: (id: string | null) => void;
  onPreviewSchool?: (schoolId: string) => void;
}

function formatDistance(distanceMiles: number): string {
  return `${distanceMiles.toFixed(2)} mi`;
}

function formatPupilCount(pupilCount: number | null): string {
  return pupilCount == null ? "Not published" : pupilCount.toLocaleString("en-GB");
}

function formatAvailability(availability: string): string {
  if (availability === "published") {
    return "Published";
  }
  if (availability === "unsupported") {
    return "Not applicable";
  }
  return "Not published";
}

function getAcademicSummary(result: PostcodeSearchResult["schools"][number]): string {
  if (result.academic_metric.availability !== "published") {
    return formatAvailability(result.academic_metric.availability);
  }

  return result.academic_metric.display_value ?? "Published";
}

function getRankingExplanation(result: PostcodeSearchResult): string {
  if (result.query.sort === "ofsted") {
    return "Sorted by latest Ofsted judgement, then distance.";
  }
  return `Sorted by distance from ${result.query.postcode}.`;
}

function buildRestoreState({
  postcode,
  radiusMiles,
  phases,
  sort,
}: {
  postcode: string;
  radiusMiles: number;
  phases: readonly SearchPhaseFilter[];
  sort: SearchSortMode;
}): SearchRestoreState {
  return {
    postcode,
    radius: radiusMiles,
    view: "results",
    resultsPhases: [...phases],
    resultsSort: sort,
  };
}

function PhaseToggle({
  label,
  phase,
  selected,
  onToggle,
}: {
  label: string;
  phase: SearchPhaseFilter;
  selected: boolean;
  onToggle: (phase: SearchPhaseFilter) => void;
}): JSX.Element {
  return (
    <button
      type="button"
      onClick={() => onToggle(phase)}
      aria-pressed={selected}
      className={cn(
        "rounded-full border px-3 py-1.5 text-xs font-semibold transition-colors duration-fast",
        selected
          ? "border-brand/50 bg-brand/15 text-primary"
          : "border-border-subtle/70 bg-surface/60 text-secondary hover:bg-elevated hover:text-primary",
      )}
    >
      {label}
    </button>
  );
}

function SortToggle({
  label,
  value,
  active,
  onSelect,
}: {
  label: string;
  value: SearchSortMode;
  active: boolean;
  onSelect: (value: SearchSortMode) => void;
}): JSX.Element {
  return (
    <button
      type="button"
      onClick={() => onSelect(value)}
      aria-pressed={active}
      className={cn(
        "rounded-full border px-3 py-1.5 text-xs font-semibold transition-colors duration-fast",
        active
          ? "border-brand/50 bg-brand/15 text-primary"
          : "border-border-subtle/70 bg-surface/60 text-secondary hover:bg-elevated hover:text-primary",
      )}
    >
      {label}
    </button>
  );
}

function ResultsTable({
  result,
  phases,
  sort,
  savedStateByUrn,
  onSavedStateChange,
  activeSchoolId,
  onSchoolHover,
  onPreviewSchool,
}: {
  result: PostcodeSearchResult;
  phases: readonly SearchPhaseFilter[];
  sort: SearchSortMode;
  savedStateByUrn: Record<string, SavedSchoolStateVM>;
  onSavedStateChange: (urn: string, savedState: SavedSchoolStateVM) => void;
  activeSchoolId?: string | null;
  onSchoolHover?: (id: string | null) => void;
  onPreviewSchool?: (schoolId: string) => void;
}): JSX.Element {
  const { toast } = useToast();
  const { addSchool, count, hasSchool, removeSchool } = useCompareSelection();
  const restoreState = buildRestoreState({
    postcode: result.query.postcode,
    radiusMiles: result.query.radius_miles,
    phases,
    sort,
  });

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full border-separate border-spacing-0">
        <thead className="bg-canvas/95">
          <tr className="text-left text-xs uppercase tracking-[0.16em] text-secondary">
            <th className="border-b border-border-subtle/70 px-4 py-3 font-medium">School</th>
            <th className="border-b border-border-subtle/70 px-4 py-3 font-medium">Distance</th>
            <th className="border-b border-border-subtle/70 px-4 py-3 font-medium">Phase</th>
            <th className="border-b border-border-subtle/70 px-4 py-3 font-medium">Type</th>
            <th className="border-b border-border-subtle/70 px-4 py-3 font-medium">Ofsted</th>
            <th className="border-b border-border-subtle/70 px-4 py-3 font-medium">Academic</th>
            <th className="border-b border-border-subtle/70 px-4 py-3 font-medium">Pupils</th>
            <th className="border-b border-border-subtle/70 px-4 py-3 font-medium">Actions</th>
          </tr>
        </thead>
        <tbody>
          {result.schools.map((school) => {
            const selected = hasSchool(school.urn);
            const savedState =
              savedStateByUrn[school.urn] ?? mapSavedSchoolState(school.saved_state);
            return (
              <tr
                key={school.urn}
                className={cn(
                  "transition-colors duration-fast hover:bg-white/[0.04]",
                  activeSchoolId === school.urn && "bg-brand/10",
                )}
                onMouseEnter={() => onSchoolHover?.(school.urn)}
                onMouseLeave={() => onSchoolHover?.(null)}
              >
                <td className="border-b border-border-subtle/40 px-4 py-4 align-top">
                  <div className="space-y-1">
                    <Link
                      to={paths.schoolProfile(school.urn)}
                      state={{ fromSearch: restoreState }}
                      className="text-sm font-semibold text-primary transition-colors duration-fast hover:text-brand-hover"
                      onMouseEnter={() => onPreviewSchool?.(school.urn)}
                      onFocus={() => onPreviewSchool?.(school.urn)}
                    >
                      {school.name}
                    </Link>
                    <p className="font-mono text-xs text-secondary">{school.postcode ?? "No postcode"}</p>
                  </div>
                </td>
                <td className="border-b border-border-subtle/40 px-4 py-4 align-top text-sm text-primary">
                  {formatDistance(school.distance_miles)}
                </td>
                <td className="border-b border-border-subtle/40 px-4 py-4 align-top text-sm text-secondary">
                  {school.phase ?? "Unknown"}
                </td>
                <td className="border-b border-border-subtle/40 px-4 py-4 align-top text-sm text-secondary">
                  {school.type ?? "Unknown"}
                </td>
                <td className="border-b border-border-subtle/40 px-4 py-4 align-top">
                  {school.latest_ofsted.availability === "published" ? (
                    <RatingBadge
                      ratingCode={
                        school.latest_ofsted.sort_rank == null
                          ? null
                          : String(school.latest_ofsted.sort_rank)
                      }
                      label={school.latest_ofsted.label}
                    />
                  ) : (
                    <span className="text-sm text-disabled">
                      {formatAvailability(school.latest_ofsted.availability)}
                    </span>
                  )}
                </td>
                <td className="border-b border-border-subtle/40 px-4 py-4 align-top">
                  <div className="space-y-1">
                    <p className="text-sm font-semibold text-primary">
                      {getAcademicSummary(school)}
                    </p>
                    <p className="text-xs text-secondary">
                      {school.academic_metric.label ?? "Academic signal"}
                    </p>
                  </div>
                </td>
                <td className="border-b border-border-subtle/40 px-4 py-4 align-top text-sm text-primary">
                  {formatPupilCount(school.pupil_count)}
                </td>
                <td className="border-b border-border-subtle/40 px-4 py-4 align-top">
                  <div className="flex min-w-[152px] flex-col items-start gap-2">
                    <SaveSchoolButton
                      schoolUrn={school.urn}
                      savedState={savedState}
                      onSavedStateChange={(nextState) => {
                        onSavedStateChange(school.urn, nextState);
                      }}
                    />
                    <Button
                      type="button"
                      variant={selected ? "ghost" : "secondary"}
                      size="sm"
                      onClick={() => {
                        if (selected) {
                          removeSchool(school.urn);
                          return;
                        }

                        const addResult = addSchool({
                          urn: school.urn,
                          name: school.name,
                          phase: school.phase,
                          type: school.type,
                          postcode: school.postcode,
                          distanceMiles: school.distance_miles,
                          source: "search",
                        });
                        if (addResult === "limit") {
                          toast({
                            title: "Compare limit reached",
                            description: "You can compare up to four schools at a time.",
                            variant: "warning",
                          });
                        }
                      }}
                    >
                      {selected ? "Remove" : count >= 4 ? "Compare full" : "Add"}
                    </Button>
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function ResultsCards({
  result,
  phases,
  sort,
  savedStateByUrn,
  onSavedStateChange,
  activeSchoolId,
  onSchoolHover,
  onPreviewSchool,
}: {
  result: PostcodeSearchResult;
  phases: readonly SearchPhaseFilter[];
  sort: SearchSortMode;
  savedStateByUrn: Record<string, SavedSchoolStateVM>;
  onSavedStateChange: (urn: string, savedState: SavedSchoolStateVM) => void;
  activeSchoolId?: string | null;
  onSchoolHover?: (id: string | null) => void;
  onPreviewSchool?: (schoolId: string) => void;
}): JSX.Element {
  const { toast } = useToast();
  const { addSchool, count, hasSchool, removeSchool } = useCompareSelection();
  const restoreState = buildRestoreState({
    postcode: result.query.postcode,
    radiusMiles: result.query.radius_miles,
    phases,
    sort,
  });

  return (
    <div className="space-y-3">
      {result.schools.map((school) => {
        const selected = hasSchool(school.urn);
        const savedState =
          savedStateByUrn[school.urn] ?? mapSavedSchoolState(school.saved_state);
        return (
          <Panel
            key={school.urn}
            className={cn(
              "space-y-4 border-border-subtle/70 bg-canvas/85 p-4",
              activeSchoolId === school.urn && "border-brand/40 shadow-[0_0_0_1px_rgba(255,255,255,0.06)]",
            )}
            onMouseEnter={() => onSchoolHover?.(school.urn)}
            onMouseLeave={() => onSchoolHover?.(null)}
          >
            <div className="flex items-start justify-between gap-3">
              <div className="space-y-1">
                <Link
                  to={paths.schoolProfile(school.urn)}
                  state={{ fromSearch: restoreState }}
                  className="text-base font-semibold leading-tight text-primary transition-colors duration-fast hover:text-brand-hover"
                  onMouseEnter={() => onPreviewSchool?.(school.urn)}
                  onFocus={() => onPreviewSchool?.(school.urn)}
                >
                  {school.name}
                </Link>
                <p className="text-sm text-secondary">
                  {school.phase ?? "Unknown"} - {school.type ?? "Unknown"}
                </p>
              </div>
              <span className="rounded-full border border-brand/40 bg-brand/10 px-3 py-1 font-mono text-xs text-brand-hover">
                {formatDistance(school.distance_miles)}
              </span>
            </div>

            <div className="grid gap-3 sm:grid-cols-3">
              <div className="rounded-lg border border-border-subtle/60 bg-surface/50 px-3 py-2">
                <p className="text-[11px] uppercase tracking-[0.14em] text-secondary">Ofsted</p>
                <div className="mt-2">
                  {school.latest_ofsted.availability === "published" ? (
                    <RatingBadge
                      ratingCode={
                        school.latest_ofsted.sort_rank == null
                          ? null
                          : String(school.latest_ofsted.sort_rank)
                      }
                      label={school.latest_ofsted.label}
                    />
                  ) : (
                    <p className="text-sm text-disabled">
                      {formatAvailability(school.latest_ofsted.availability)}
                    </p>
                  )}
                </div>
              </div>

              <div className="rounded-lg border border-border-subtle/60 bg-surface/50 px-3 py-2">
                <p className="text-[11px] uppercase tracking-[0.14em] text-secondary">Academic</p>
                <p className="mt-2 text-sm font-semibold text-primary">
                  {getAcademicSummary(school)}
                </p>
                <p className="mt-1 text-xs text-secondary">
                  {school.academic_metric.label ?? "Academic signal"}
                </p>
              </div>

              <div className="rounded-lg border border-border-subtle/60 bg-surface/50 px-3 py-2">
                <p className="text-[11px] uppercase tracking-[0.14em] text-secondary">Pupils</p>
                <p className="mt-2 text-sm font-semibold text-primary">
                  {formatPupilCount(school.pupil_count)}
                </p>
                <p className="mt-1 font-mono text-xs text-secondary">
                  {school.postcode ?? "No postcode"}
                </p>
              </div>
            </div>

            <div className="flex items-center justify-between gap-3 border-t border-border-subtle/60 pt-3">
              <p className="text-xs text-secondary">
                {selected ? "Included in compare" : `Add up to ${Math.max(0, 4 - count)} more`}
              </p>
              <div className="flex items-center gap-2">
                <SaveSchoolButton
                  schoolUrn={school.urn}
                  savedState={savedState}
                  onSavedStateChange={(nextState) => {
                    onSavedStateChange(school.urn, nextState);
                  }}
                />
                <Button
                  type="button"
                  variant={selected ? "ghost" : "secondary"}
                  size="sm"
                  onClick={() => {
                    if (selected) {
                      removeSchool(school.urn);
                      return;
                    }

                    const addResult = addSchool({
                      urn: school.urn,
                      name: school.name,
                      phase: school.phase,
                      type: school.type,
                      postcode: school.postcode,
                      distanceMiles: school.distance_miles,
                      source: "search",
                    });
                    if (addResult === "limit") {
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
              </div>
            </div>
          </Panel>
        );
      })}
    </div>
  );
}

export function ResultsOverlay({
  open,
  status,
  result,
  savedStateByUrn,
  errorMessage,
  phases,
  sort,
  onClose,
  onRetry,
  onSavedStateChange,
  onPhasesChange,
  onSortChange,
  activeSchoolId,
  onSchoolHover,
  onPreviewSchool,
}: ResultsOverlayProps): JSX.Element | null {
  const isMobile = useIsMobile();
  const { items } = useCompareSelection();

  useEffect(() => {
    if (!open) {
      return;
    }

    const handleKeyDown = (event: KeyboardEvent): void => {
      if (event.key === "Escape") {
        onClose();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose, open]);

  useEffect(() => {
    if (!open) {
      return;
    }

    const previousBodyOverflow = document.body.style.overflow;
    const previousHtmlOverflow = document.documentElement.style.overflow;
    document.body.style.overflow = "hidden";
    document.documentElement.style.overflow = "hidden";

    return () => {
      document.body.style.overflow = previousBodyOverflow;
      document.documentElement.style.overflow = previousHtmlOverflow;
    };
  }, [open]);

  if (!open) {
    return null;
  }

  const handlePhaseToggle = (phase: SearchPhaseFilter): void => {
    const next = phases.includes(phase)
      ? phases.filter((value) => value !== phase)
      : phase === "primary"
        ? (["primary", ...phases.filter((value) => value !== "primary")] as SearchPhaseFilter[])
        : ([...phases.filter((value) => value !== "secondary"), "secondary"] as SearchPhaseFilter[]);
    onPhasesChange(next);
  };

  return (
    <div className="fixed inset-x-0 bottom-0 top-14 z-modal" role="dialog" aria-modal="true">
      <div className="absolute inset-0 bg-canvas/72 backdrop-blur-md" aria-hidden />
      <div className={cn("relative z-10 flex h-full", isMobile ? "p-0" : "items-center justify-center p-4 sm:p-6")}>
        <Panel
          className={cn(
            "scrollbar-hide h-full w-full overflow-y-auto overflow-x-hidden border border-border-subtle/70 bg-canvas/94 shadow-[0_24px_80px_rgba(6,10,18,0.55)]",
            isMobile ? "rounded-none" : "max-w-[1180px] rounded-[1.5rem]",
          )}
        >
          <header className="sticky top-0 z-20 border-b border-border-subtle/70 bg-canvas/94 px-4 py-4 sm:px-6 sm:py-5">
            <div className="flex items-start justify-between gap-4">
              <div className="space-y-3">
                <div className="flex flex-wrap items-center gap-3">
                  <SearchModeSwitch
                    activeView="results"
                    resultsEnabled
                    onMapSelect={onClose}
                    onResultsSelect={() => undefined}
                  />
                  <span className="inline-flex items-center gap-2 rounded-full border border-border-subtle/70 bg-surface/60 px-3 py-1 text-[11px] uppercase tracking-[0.16em] text-secondary">
                    <Sparkles className="h-3.5 w-3.5" aria-hidden />
                    Analysis mode
                  </span>
                </div>
                <div>
                  <h2 className="text-2xl font-semibold text-primary sm:text-3xl">
                    {result ? `Results for ${result.query.postcode}` : "Results"}
                  </h2>
                  <p className="mt-1 text-sm text-secondary">
                    {result
                      ? `Rank, filter, and compare ${result.count} ${result.count === 1 ? "school" : "schools"} within ${result.query.radius_miles} miles.`
                      : "Rank, filter, and compare the schools from your active postcode search."}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <CompareActionButton
                  urns={items.map((item) => item.urn)}
                  label={items.length >= 2 ? "Open compare" : `Compare ${items.length}/4`}
                  lockedLabel="Unlock compare"
                  variant="secondary"
                  size="sm"
                />
                <Button type="button" variant="ghost" size="sm" onClick={onClose} aria-label="Back to map">
                  <X className="h-4 w-4" aria-hidden />
                </Button>
              </div>
            </div>

            <div className="mt-4 flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
              <div className="space-y-2">
                <p className="text-[11px] uppercase tracking-[0.14em] text-secondary">Phase</p>
                <div className="flex flex-wrap gap-2">
                  <PhaseToggle
                    label="Primary"
                    phase="primary"
                    selected={phases.includes("primary")}
                    onToggle={handlePhaseToggle}
                  />
                  <PhaseToggle
                    label="Secondary"
                    phase="secondary"
                    selected={phases.includes("secondary")}
                    onToggle={handlePhaseToggle}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <p className="text-[11px] uppercase tracking-[0.14em] text-secondary">Sort</p>
                <div className="flex flex-wrap gap-2">
                  <SortToggle
                    label="Closest"
                    value="closest"
                    active={sort === "closest"}
                    onSelect={onSortChange}
                  />
                  <SortToggle
                    label="Ofsted"
                    value="ofsted"
                    active={sort === "ofsted"}
                    onSelect={onSortChange}
                  />
                </div>
              </div>
            </div>

            <div className="mt-4 flex flex-wrap items-center gap-3 text-sm text-secondary">
              <span className="inline-flex items-center gap-2 rounded-full border border-border-subtle/60 bg-surface/40 px-3 py-1">
                <ArrowUpDown className="h-3.5 w-3.5" aria-hidden />
                {result ? getRankingExplanation(result) : "Preparing results."}
              </span>
              <span className="inline-flex items-center gap-2 rounded-full border border-border-subtle/60 bg-surface/40 px-3 py-1">
                <UsersRound className="h-3.5 w-3.5" aria-hidden />
                Compare up to four schools
              </span>
            </div>

            {status === "loading" ? (
              <p className="mt-3 text-xs text-secondary">Updating results...</p>
            ) : null}
            {status === "error" && result ? (
              <div className="mt-4 flex items-center justify-between gap-3 rounded-xl border border-danger/50 bg-danger/10 px-4 py-3">
                <p className="text-sm text-secondary">
                  {errorMessage ?? "Results update failed. Showing previous results."}
                </p>
                <Button type="button" variant="secondary" size="sm" onClick={() => void onRetry()}>
                  Retry
                </Button>
              </div>
            ) : null}
          </header>

          <div className="px-4 py-4 sm:px-6 sm:py-5">
            {status === "loading" && !result ? (
              <div className="space-y-4">
                <LoadingSkeleton lines={3} />
                <LoadingSkeleton lines={8} />
              </div>
            ) : null}

            {status === "error" && !result ? (
              <ErrorState
                title="Results unavailable"
                description={errorMessage ?? "Please retry your results analysis."}
                onRetry={() => {
                  void onRetry();
                }}
              />
            ) : null}

            {status === "empty" && result ? (
              <EmptyState
                title="No schools match these filters"
                description="Try removing a phase filter or switching back to closest or Ofsted sorting."
              />
            ) : null}

            {result && result.schools.length > 0 ? (
              isMobile ? (
                <ResultsCards
                  result={result}
                  phases={phases}
                  sort={sort}
                  savedStateByUrn={savedStateByUrn}
                  onSavedStateChange={onSavedStateChange}
                  activeSchoolId={activeSchoolId}
                  onSchoolHover={onSchoolHover}
                  onPreviewSchool={onPreviewSchool}
                />
              ) : (
                <ResultsTable
                  result={result}
                  phases={phases}
                  sort={sort}
                  savedStateByUrn={savedStateByUrn}
                  onSavedStateChange={onSavedStateChange}
                  activeSchoolId={activeSchoolId}
                  onSchoolHover={onSchoolHover}
                  onPreviewSchool={onPreviewSchool}
                />
              )
            ) : null}
          </div>
        </Panel>
      </div>
    </div>
  );
}
