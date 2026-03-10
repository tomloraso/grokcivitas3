import { Building2, GraduationCap, LockKeyhole, MapPin } from "lucide-react";
import { useEffect, useMemo, useReducer, useRef } from "react";
import {
  Link,
  type NavigateFunction,
  useLocation,
  useNavigate,
  useSearchParams
} from "react-router-dom";

import { ApiClientError, getSchoolCompare } from "../../api/client";
import type { SchoolCompareResponse } from "../../api/types";
import { Breadcrumbs } from "../../components/layout/Breadcrumbs";
import { PageContainer } from "../../components/layout/PageContainer";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Card, Panel } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { ErrorState } from "../../components/ui/ErrorState";
import { LoadingSkeleton } from "../../components/ui/LoadingSkeleton";
import { useAuth } from "../auth/useAuth";
import type { CompareSelectionItem } from "../../shared/context/CompareSelectionContext";
import { useCompareSelection } from "../../shared/context/CompareSelectionContext";
import { readCompareUrlState } from "../../shared/routing/compareUrns";
import { paths } from "../../shared/routing/paths";
import { buildAccessActionHref, getPremiumPaywallCopy } from "../premium-access/copy";
import { mapCompareToVM } from "./mappers/compareMapper";
import type { CompareCellVM, CompareSchoolColumnVM } from "./types";

type CompareStatus = "idle" | "loading" | "success" | "error";

interface CompareState {
  status: CompareStatus;
  response: SchoolCompareResponse | null;
  errorMessage: string | null;
}

type CompareAction =
  | { type: "RESET" }
  | { type: "FETCH_START" }
  | { type: "FETCH_SUCCESS"; response: SchoolCompareResponse }
  | { type: "FETCH_ERROR"; message: string };

const INITIAL_STATE: CompareState = {
  status: "idle",
  response: null,
  errorMessage: null
};

const MAX_COMPARE_SCHOOLS = 4;

function reducer(_state: CompareState, action: CompareAction): CompareState {
  switch (action.type) {
    case "RESET":
      return INITIAL_STATE;
    case "FETCH_START":
      return { status: "loading", response: null, errorMessage: null };
    case "FETCH_SUCCESS":
      return {
        status: "success",
        response: action.response,
        errorMessage: null
      };
    case "FETCH_ERROR":
      return { status: "error", response: null, errorMessage: action.message };
    default:
      return _state;
  }
}

export function SchoolCompareFeature(): JSX.Element {
  const [searchParams] = useSearchParams();
  const location = useLocation();
  const navigate = useNavigate();
  const { session } = useAuth();
  const [state, dispatch] = useReducer(reducer, INITIAL_STATE);
  const [reloadToken, bumpReloadToken] = useReducer(
    (value: number) => value + 1,
    0
  );
  const requestSeqRef = useRef(0);
  const { items, isHydrated, removeSchool, clearSchools, replaceSchools } =
    useCompareSelection();

  const compareUrlState = useMemo(
    () => readCompareUrlState(searchParams),
    [searchParams]
  );
  const hasExplicitUrnsParam = compareUrlState.hasExplicitUrns;
  const urlUrns = compareUrlState.urns;
  const selectionUrns = useMemo(() => items.map((item) => item.urn), [items]);
  const effectiveUrns = useMemo(() => {
    if (hasExplicitUrnsParam) {
      return urlUrns;
    }
    if (!isHydrated) {
      return null;
    }
    return selectionUrns;
  }, [hasExplicitUrnsParam, isHydrated, selectionUrns, urlUrns]);
  const compareHref = `${location.pathname}${location.search}`;
  const selectionByUrn = useMemo(
    () => new Map(items.map((item) => [item.urn, item])),
    [items]
  );
  const selectionByUrnRef = useRef(selectionByUrn);

  useEffect(() => {
    selectionByUrnRef.current = selectionByUrn;
  }, [selectionByUrn]);

  useEffect(() => {
    if (!hasExplicitUrnsParam && isHydrated && selectionUrns.length > 0) {
      navigate(paths.compare(selectionUrns), { replace: true });
    }
  }, [hasExplicitUrnsParam, isHydrated, navigate, selectionUrns]);

  useEffect(() => {
    if (
      !isHydrated ||
      !hasExplicitUrnsParam ||
      urlUrns.length === 0 ||
      urlUrns.length > MAX_COMPARE_SCHOOLS
    ) {
      return;
    }

    if (selectionMatchesUrns(items, urlUrns)) {
      return;
    }

    replaceSchools(buildSelectionItemsFromUrns(urlUrns, selectionByUrn));
  }, [
    hasExplicitUrnsParam,
    isHydrated,
    items,
    replaceSchools,
    selectionByUrn,
    urlUrns
  ]);

  useEffect(() => {
    if (effectiveUrns === null) {
      return;
    }

    if (effectiveUrns.length < 2) {
      dispatch({ type: "RESET" });
      return;
    }

    if (effectiveUrns.length > MAX_COMPARE_SCHOOLS) {
      dispatch({
        type: "FETCH_ERROR",
        message: "You can compare up to four schools at a time."
      });
      return;
    }

    const requestId = ++requestSeqRef.current;
    dispatch({ type: "FETCH_START" });

    void getSchoolCompare(effectiveUrns)
      .then((response) => {
        if (requestId !== requestSeqRef.current) {
          return;
        }

        const schools = response.schools ?? [];
        const schoolByUrn = new Map(schools.map((school) => [school.urn, school]));
        replaceSchools(
          effectiveUrns.map((urn) => {
            const school = schoolByUrn.get(urn);
            const existing = selectionByUrnRef.current.get(urn);
            return {
              urn,
              name: school?.name ?? existing?.name ?? `School ${urn}`,
              phase: school?.phase ?? existing?.phase ?? null,
              type: school?.type ?? existing?.type ?? null,
              postcode: school?.postcode ?? existing?.postcode ?? null,
              distanceMiles: existing?.distanceMiles,
              source: existing?.source ?? "compare"
            };
          })
        );
        dispatch({ type: "FETCH_SUCCESS", response });
      })
      .catch((error: unknown) => {
        if (requestId !== requestSeqRef.current) {
          return;
        }

        dispatch({
          type: "FETCH_ERROR",
          message: toCompareErrorMessage(error)
        });
      });

    return () => {
      requestSeqRef.current += 1;
    };
  }, [effectiveUrns, reloadToken, replaceSchools, session.accessEpoch]);

  const fallbackSchools = useMemo(
    () =>
      buildFallbackSchoolColumns(
        effectiveUrns ?? [],
        selectionByUrn,
        compareHref
      ),
    [compareHref, effectiveUrns, selectionByUrn]
  );
  const compareVm = useMemo(() => {
    if (!state.response) {
      return null;
    }

    return mapCompareToVM(state.response, selectionByUrn, compareHref);
  }, [compareHref, selectionByUrn, state.response]);
  const visibleSchools = compareVm?.schools ?? fallbackSchools;

  return (
    <PageContainer className="space-y-8">
      <Breadcrumbs segments={[{ label: "Compare" }]} />

      <header className="space-y-4">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div className="space-y-2">
            <p className="eyebrow">Compare</p>
            <h1 className="text-3xl font-bold tracking-tight text-primary sm:text-4xl">
              Compare schools side by side
            </h1>
            <p className="max-w-3xl text-sm text-secondary sm:text-base">
              Compare two to four schools across inspection, demographics,
              attendance, behaviour, workforce, performance, and neighbourhood
              context.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <Button asChild variant="secondary">
              <Link to={paths.home}>Back to search</Link>
            </Button>
            {visibleSchools.length > 0 ? (
              <Button
                type="button"
                variant="ghost"
                onClick={() => {
                  clearSchools();
                  navigate(paths.compare());
                }}
              >
                Clear compare
              </Button>
            ) : null}
          </div>
        </div>

        <p className="text-sm text-secondary" data-testid="compare-summary">
          {effectiveUrns === null
            ? "Loading compare selection..."
            : `${effectiveUrns.length} school${effectiveUrns.length === 1 ? "" : "s"} selected.`}
        </p>
      </header>

      {effectiveUrns === null || state.status === "loading" ? (
        <CompareLoadingState />
      ) : null}

      {effectiveUrns !== null && effectiveUrns.length === 0 ? (
        <EmptyState
          title="Start a compare set"
          description="Add at least two schools from search results or a school profile to open the compare view."
          action={
            <Button asChild variant="primary">
              <Link to={paths.home}>Browse schools</Link>
            </Button>
          }
        />
      ) : null}

      {effectiveUrns !== null && effectiveUrns.length === 1 ? (
        <div className="space-y-6">
          <SchoolColumnsStrip
            schools={visibleSchools}
            onRemoveSchool={(urn) => {
              handleRemoveSchool(urn, effectiveUrns, navigate, removeSchool);
            }}
          />
          <Panel className="space-y-3">
            <h2 className="text-lg font-semibold text-primary">
              Add one more school to compare
            </h2>
            <p className="text-sm text-secondary">
              You need at least two schools to build the comparison matrix. Keep
              this school selected and add another from search or a school
              profile.
            </p>
            <div className="flex flex-wrap gap-3">
              <Button asChild variant="primary">
                <Link to={paths.home}>Find another school</Link>
              </Button>
            </div>
          </Panel>
        </div>
      ) : null}

      {effectiveUrns !== null &&
      effectiveUrns.length >= 2 &&
      state.status === "error" ? (
        <div className="space-y-6">
          <ErrorState
            title="Compare is unavailable"
            description={
              state.errorMessage ??
              "The selected schools could not be compared right now."
            }
            onRetry={bumpReloadToken}
          />
          {visibleSchools.length > 0 ? (
            <SchoolColumnsStrip
              schools={visibleSchools}
              onRemoveSchool={(urn) => {
                handleRemoveSchool(urn, effectiveUrns, navigate, removeSchool);
              }}
            />
          ) : null}
        </div>
      ) : null}

      {compareVm && state.status === "success" ? (
        <div className="space-y-6">
          <SchoolColumnsStrip
            schools={compareVm.schools}
            onRemoveSchool={(urn) => {
              handleRemoveSchool(
                urn,
                compareVm.schools.map((school) => school.urn),
                navigate,
                removeSchool
              );
            }}
          />

          {compareVm.access.state === "locked" ? (
            <CompareLockedState
              compareVm={compareVm}
              currentHref={`${location.pathname}${location.search}`}
            />
          ) : (
            compareVm.sections.map((section) => (
              <CompareSectionMatrix
                key={section.key}
                label={section.label}
                schools={compareVm.schools}
                rows={section.rows}
              />
            ))
          )}
        </div>
      ) : null}
    </PageContainer>
  );
}

function CompareLockedState({
  compareVm,
  currentHref,
}: {
  compareVm: NonNullable<ReturnType<typeof mapCompareToVM>>;
  currentHref: string;
}): JSX.Element {
  const copy = getPremiumPaywallCopy({
    capabilityKey: compareVm.access.capabilityKey,
    schoolName: null,
    requiresAuth: compareVm.access.requiresAuth,
  });
  const actionHref = buildAccessActionHref({
    access: compareVm.access,
    returnTo: currentHref,
  });

  return (
    <Panel className="space-y-5 border-brand/30 bg-brand/5">
      <div className="space-y-2">
        <p className="inline-flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.12em] text-brand">
          <LockKeyhole className="h-3.5 w-3.5" aria-hidden />
          Premium compare
        </p>
        <h2 className="text-xl font-semibold text-primary">{copy.title}</h2>
        <p className="max-w-3xl text-sm text-secondary">{copy.description}</p>
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        {compareVm.schools.map((school) => (
          <Card key={school.urn} className="border-brand/20 bg-surface/80">
            <p className="font-mono text-xs text-disabled">URN {school.urn}</p>
            <p className="mt-1 text-base font-semibold text-primary">{school.name}</p>
            <p className="mt-2 text-sm text-secondary">
              {school.phase} · {school.type}
            </p>
          </Card>
        ))}
      </div>

      <div className="flex flex-wrap gap-3">
        <Button asChild variant="primary">
          <Link to={actionHref}>{copy.buttonLabel}</Link>
        </Button>
        <Button asChild variant="secondary">
          <Link to={paths.home}>Back to search</Link>
        </Button>
      </div>
    </Panel>
  );
}

function CompareLoadingState(): JSX.Element {
  return (
    <div className="space-y-6" aria-live="polite" aria-busy="true">
      <LoadingSkeleton lines={3} />
      <LoadingSkeleton lines={6} />
      <LoadingSkeleton lines={8} />
    </div>
  );
}

function SchoolColumnsStrip({
  schools,
  onRemoveSchool
}: {
  schools: CompareSchoolColumnVM[];
  onRemoveSchool: (urn: string) => void;
}): JSX.Element {
  return (
    <Panel className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-primary">
            Selected schools
          </h2>
          <p className="text-sm text-secondary">
            Remove schools here without leaving the compare route.
          </p>
        </div>
      </div>

      <div className="overflow-x-auto pb-1">
        <div
          className="grid gap-4"
          style={{
            gridTemplateColumns: `repeat(${schools.length}, minmax(260px, 1fr))`,
            minWidth: `${schools.length * 260}px`
          }}
        >
          {schools.map((school) => (
            <Card
              key={school.urn}
              className="space-y-4 rounded-xl border border-border-subtle/80 bg-surface/90"
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-1">
                    <p className="font-mono text-xs text-disabled">
                      URN {school.urn}
                    </p>
                    <h3 className="text-lg font-semibold leading-snug text-primary">
                      <Link
                        to={school.profileHref}
                        state={school.profileState}
                        className="transition-colors hover:text-brand-hover"
                      >
                        {school.name}
                      </Link>
                    </h3>
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    aria-label={`Remove ${school.name} from compare`}
                    onClick={() => onRemoveSchool(school.urn)}
                  >
                    Remove
                  </Button>
                </div>

                <div className="flex flex-wrap gap-2">
                  <Badge variant="default" className="gap-1.5">
                    <GraduationCap className="h-3 w-3" aria-hidden />
                    {school.phase}
                  </Badge>
                  <Badge variant="outline" className="gap-1.5">
                    <Building2 className="h-3 w-3" aria-hidden />
                    {school.type}
                  </Badge>
                  <Badge variant="outline" className="gap-1.5">
                    <MapPin className="h-3 w-3" aria-hidden />
                    {school.postcode}
                  </Badge>
                </div>

                {school.ageRangeLabel || school.distanceLabel ? (
                  <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-secondary">
                    {school.ageRangeLabel ? (
                      <span>{school.ageRangeLabel}</span>
                    ) : null}
                    {school.distanceLabel ? (
                      <span className="font-mono">{school.distanceLabel}</span>
                    ) : null}
                  </div>
                ) : null}
              </div>
            </Card>
          ))}
        </div>
      </div>
    </Panel>
  );
}

function CompareSectionMatrix({
  label,
  schools,
  rows
}: {
  label: string;
  schools: CompareSchoolColumnVM[];
  rows: Array<{
    metricKey: string;
    label: string;
    unit: string;
    cells: CompareCellVM[];
  }>;
}): JSX.Element {
  const columnWidth = 220;
  const labelWidth = 220;
  const minWidth = labelWidth + schools.length * columnWidth;

  return (
    <Panel className="space-y-4 overflow-hidden">
      <div className="space-y-1">
        <h2 className="text-xl font-semibold text-primary">{label}</h2>
        <p className="text-sm text-secondary">
          Each row stays aligned by metric. Year labels and availability states
          are shown inside each school cell.
        </p>
      </div>

      <div className="overflow-x-auto">
        <table
          className="min-w-full border-separate border-spacing-px bg-border-subtle/70"
          style={{ minWidth }}
        >
          <caption className="sr-only">{label} comparison table</caption>
          <thead>
            <tr>
              <th
                scope="col"
                className="sticky left-0 top-0 z-30 bg-canvas/95 px-4 py-3 text-left align-top backdrop-blur"
                style={{ minWidth: labelWidth, width: labelWidth }}
              >
                <span className="text-xs font-semibold uppercase tracking-[0.12em] text-disabled">
                  Metric
                </span>
              </th>

              {schools.map((school) => (
                <th
                  key={school.urn}
                  scope="col"
                  className="sticky top-0 z-20 bg-canvas/95 px-4 py-3 text-left align-top backdrop-blur"
                  style={{ minWidth: columnWidth }}
                >
                  <Link
                    to={school.profileHref}
                    state={school.profileState}
                    className="block transition-colors hover:text-brand-hover"
                  >
                    <p className="text-sm font-semibold text-primary">
                      {school.name}
                    </p>
                    <p className="mt-1 font-mono text-xs text-disabled">
                      URN {school.urn}
                    </p>
                  </Link>
                </th>
              ))}
            </tr>
          </thead>

          <tbody>
            {rows.map((row) => (
              <CompareSectionRow
                key={row.metricKey}
                row={row}
                schools={schools}
                labelWidth={labelWidth}
              />
            ))}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}

function CompareSectionRow({
  row,
  schools,
  labelWidth
}: {
  row: {
    metricKey: string;
    label: string;
    unit: string;
    cells: CompareCellVM[];
  };
  schools: CompareSchoolColumnVM[];
  labelWidth: number;
}): JSX.Element {
  return (
    <tr>
      <th
        scope="row"
        className="sticky left-0 z-10 bg-surface/95 px-4 py-4 text-left align-top"
        style={{ minWidth: labelWidth, width: labelWidth }}
      >
        <div className="flex flex-col justify-center gap-1">
          <p className="text-sm font-semibold text-primary">{row.label}</p>
          {unitLabel(row.unit) ? (
            <p className="text-xs uppercase tracking-[0.08em] text-disabled">
              {unitLabel(row.unit)}
            </p>
          ) : null}
        </div>
      </th>

      {schools.map((school) => {
        const cell = row.cells.find((entry) => entry.urn === school.urn);
        if (!cell) {
          return (
            <td key={`${row.metricKey}-${school.urn}`} className="align-top">
              <div className="flex min-h-[124px] flex-col justify-center gap-2 bg-surface px-4 py-4">
                <p className="text-sm font-semibold text-secondary">
                  Unavailable
                </p>
              </div>
            </td>
          );
        }

        return (
          <CompareValueCell key={`${row.metricKey}-${cell.urn}`} cell={cell} />
        );
      })}
    </tr>
  );
}

function CompareValueCell({ cell }: { cell: CompareCellVM }): JSX.Element {
  return (
    <td className="align-top">
      <div
        className={`flex min-h-[124px] flex-col justify-center gap-2 px-4 py-4 ${cellToneClassName(
          cell.availability
        )}`}
      >
        <p
          className={`text-base font-semibold leading-snug ${
            cell.isMuted ? "text-secondary" : "text-primary"
          }`}
        >
          {cell.displayValue}
        </p>
        {cell.metaLabel ? (
          <p className="text-xs uppercase tracking-[0.08em] text-disabled">
            {cell.metaLabel}
          </p>
        ) : null}
        {cell.detailLabel ? (
          <p className="text-xs text-secondary">{cell.detailLabel}</p>
        ) : null}
        {cell.benchmarkLabel ? (
          <p className="text-xs text-secondary">{cell.benchmarkLabel}</p>
        ) : null}
      </div>
    </td>
  );
}

function handleRemoveSchool(
  urn: string,
  urns: string[],
  navigate: NavigateFunction,
  removeSchool: (urn: string) => void
): void {
  const nextUrns = urns.filter((candidate) => candidate !== urn);
  removeSchool(urn);
  navigate(paths.compare(nextUrns));
}

function buildFallbackSchoolColumns(
  urns: string[],
  selectionByUrn: Map<string, CompareSelectionItem>,
  compareHref: string
): CompareSchoolColumnVM[] {
  return urns.map((urn) => {
    const selection = selectionByUrn.get(urn);
    return {
      urn,
      name: selection?.name ?? `School ${urn}`,
      phase: selection?.phase ?? "Unknown",
      type: selection?.type ?? "Unknown",
      postcode: selection?.postcode ?? "Not published",
      ageRangeLabel: null,
      distanceLabel:
        selection?.distanceMiles !== undefined
          ? `${selection.distanceMiles.toFixed(2)} mi`
          : null,
      profileHref: paths.schoolProfile(urn),
      profileState: { fromCompare: { href: compareHref } }
    };
  });
}

function selectionMatchesUrns(
  items: CompareSelectionItem[],
  urns: string[]
): boolean {
  return (
    items.length === urns.length &&
    items.every((item, index) => item.urn === urns[index])
  );
}

function buildSelectionItemsFromUrns(
  urns: string[],
  selectionByUrn: Map<string, CompareSelectionItem>
): CompareSelectionItem[] {
  return urns.map((urn) => {
    const existing = selectionByUrn.get(urn);
    return (
      existing ?? {
        urn,
        name: `School ${urn}`,
        phase: null,
        type: null,
        postcode: null,
        source: "compare"
      }
    );
  });
}

function toCompareErrorMessage(error: unknown): string {
  if (error instanceof ApiClientError) {
    switch (error.status) {
      case 400:
        return error.message || "Compare requires two to four unique schools.";
      case 404:
        return (
          error.message || "One or more selected schools could not be found."
        );
      case 503:
        return error.message || "Compare data is temporarily unavailable.";
      default:
        return error.message;
    }
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "The selected schools could not be compared right now.";
}

function unitLabel(unit: string): string | null {
  switch (unit) {
    case "percent":
      return "Percent";
    case "count":
      return "Count";
    case "rate":
      return "Rate";
    case "ratio":
      return "Ratio";
    case "score":
      return "Score";
    case "currency":
      return "GBP";
    case "decile":
      return "Decile";
    case "date":
      return "Date";
    case "days":
      return "Days";
    case "years":
      return "Years";
    default:
      return null;
  }
}

function cellToneClassName(
  availability: CompareCellVM["availability"]
): string {
  switch (availability) {
    case "available":
      return "bg-surface";
    case "unsupported":
      return "bg-surface/80";
    case "suppressed":
      return "bg-warning/10";
    case "unavailable":
    default:
      return "bg-surface/90";
  }
}
