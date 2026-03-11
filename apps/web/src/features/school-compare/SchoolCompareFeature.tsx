import { Share2, LockKeyhole, Sparkles } from "lucide-react";
import { useEffect, useMemo, useReducer, useRef, useState } from "react";
import {
  Link,
  type NavigateFunction,
  useLocation,
  useNavigate,
  useSearchParams,
} from "react-router-dom";

import { ApiClientError, getSchoolCompare } from "../../api/client";
import type { SchoolCompareResponse } from "../../api/types";
import { Breadcrumbs } from "../../components/layout/Breadcrumbs";
import { PageContainer } from "../../components/layout/PageContainer";
import { PageMeta } from "../../components/layout/PageMeta";
import { Button } from "../../components/ui/Button";
import { Panel } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { ErrorState } from "../../components/ui/ErrorState";
import { LoadingSkeleton } from "../../components/ui/LoadingSkeleton";
import { useAuth } from "../auth/useAuth";
import type { CompareSelectionItem } from "../../shared/context/CompareSelectionContext";
import { useCompareSelection } from "../../shared/context/CompareSelectionContext";
import { readCompareUrlState } from "../../shared/routing/compareUrns";
import { paths } from "../../shared/routing/paths";
import { buildAccessActionHref, getPremiumPaywallCopy } from "../premium-access/copy";
import { CompareSchoolStrip } from "./CompareSchoolStrip";
import { padToSlots } from "./compareSlots";
import { CompareAccordionSections } from "./CompareAccordionSections";
import { mapCompareToVM } from "./mappers/compareMapper";
import type { CompareSchoolColumnVM } from "./types";

/* ------------------------------------------------------------------ */
/* Reducer                                                             */
/* ------------------------------------------------------------------ */

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
  errorMessage: null,
};

const MAX_COMPARE_SCHOOLS = 4;

function reducer(_state: CompareState, action: CompareAction): CompareState {
  switch (action.type) {
    case "RESET":
      return INITIAL_STATE;
    case "FETCH_START":
      return { status: "loading", response: null, errorMessage: null };
    case "FETCH_SUCCESS":
      return { status: "success", response: action.response, errorMessage: null };
    case "FETCH_ERROR":
      return { status: "error", response: null, errorMessage: action.message };
    default:
      return _state;
  }
}

/* ------------------------------------------------------------------ */
/* Share button                                                        */
/* ------------------------------------------------------------------ */

function ShareButton(): JSX.Element {
  const [copied, setCopied] = useState(false);

  const handleShare = () => {
    void navigator.clipboard.writeText(window.location.href).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <Button type="button" variant="secondary" onClick={handleShare}>
      <Share2 className="mr-1.5 h-4 w-4" aria-hidden />
      {copied ? "Link copied" : "Share"}
    </Button>
  );
}

/* ------------------------------------------------------------------ */
/* Premium banner (slim)                                               */
/* ------------------------------------------------------------------ */

function ComparePremiumBanner({
  compareVm,
  currentHref,
}: {
  compareVm: { access: ReturnType<typeof mapCompareToVM>["access"] };
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
    <Panel className="border-brand/30 bg-brand/5">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-brand/10">
            <Sparkles className="h-4 w-4 text-brand" aria-hidden />
          </div>
          <div className="space-y-0.5">
            <p className="text-sm font-semibold text-primary">{copy.title}</p>
            <p className="text-xs text-secondary">{copy.description}</p>
          </div>
        </div>
        <Button asChild variant="primary" className="shrink-0">
          <Link to={actionHref}>
            <LockKeyhole className="mr-1.5 h-4 w-4" aria-hidden />
            {copy.buttonLabel}
          </Link>
        </Button>
      </div>
    </Panel>
  );
}

/* ------------------------------------------------------------------ */
/* Main feature                                                        */
/* ------------------------------------------------------------------ */

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
  const skipUrlSyncRef = useRef(false);
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
    if (hasExplicitUrnsParam) return urlUrns;
    if (!isHydrated) return null;
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

  // Sync URL → selection context
  useEffect(() => {
    if (!hasExplicitUrnsParam && isHydrated && selectionUrns.length > 0) {
      navigate(paths.compare(selectionUrns), { replace: true });
    }
  }, [hasExplicitUrnsParam, isHydrated, navigate, selectionUrns]);

  useEffect(() => {
    // Skip URL→selection sync when an explicit clear is in progress.
    // React Router's navigate uses startTransition, so clearSchools() can
    // take effect (items=[]) before the URL updates — without this guard
    // the effect sees the mismatch and repopulates the selection.
    if (skipUrlSyncRef.current) {
      skipUrlSyncRef.current = false;
      return;
    }

    if (
      !isHydrated ||
      !hasExplicitUrnsParam ||
      urlUrns.length === 0 ||
      urlUrns.length > MAX_COMPARE_SCHOOLS
    )
      return;

    if (selectionMatchesUrns(items, urlUrns)) return;

    replaceSchools(buildSelectionItemsFromUrns(urlUrns, selectionByUrn));
  }, [hasExplicitUrnsParam, isHydrated, items, replaceSchools, selectionByUrn, urlUrns]);

  // Fetch compare data
  useEffect(() => {
    if (effectiveUrns === null) return;

    if (effectiveUrns.length < 2) {
      dispatch({ type: "RESET" });
      return;
    }

    if (effectiveUrns.length > MAX_COMPARE_SCHOOLS) {
      dispatch({
        type: "FETCH_ERROR",
        message: "You can compare up to four schools at a time.",
      });
      return;
    }

    const requestId = ++requestSeqRef.current;
    dispatch({ type: "FETCH_START" });

    void getSchoolCompare(effectiveUrns)
      .then((response) => {
        if (requestId !== requestSeqRef.current) return;

        const schools = response.schools ?? [];
        const schoolByUrn = new Map(schools.map((s) => [s.urn, s]));
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
              source: existing?.source ?? "compare",
            };
          })
        );
        dispatch({ type: "FETCH_SUCCESS", response });
      })
      .catch((error: unknown) => {
        if (requestId !== requestSeqRef.current) return;
        dispatch({ type: "FETCH_ERROR", message: toCompareErrorMessage(error) });
      });

    return () => {
      requestSeqRef.current += 1;
    };
  }, [effectiveUrns, reloadToken, replaceSchools, session.accessEpoch]);

  const fallbackSchools = useMemo(
    () =>
      buildFallbackSchoolColumns(effectiveUrns ?? [], selectionByUrn, compareHref),
    [compareHref, effectiveUrns, selectionByUrn]
  );
  const compareVm = useMemo(() => {
    if (!state.response) return null;
    return mapCompareToVM(state.response, selectionByUrn, compareHref);
  }, [compareHref, selectionByUrn, state.response]);
  const visibleSchools = compareVm?.schools ?? fallbackSchools;
  const paddedSlots = useMemo(() => padToSlots(visibleSchools), [visibleSchools]);

  // Dev premium bypass check
  const isDevUnlocked =
    !import.meta.env.PROD &&
    session.accountAccessState === "premium" &&
    compareVm?.access.state === "locked" &&
    compareVm.access.capabilityKey !== null &&
    session.capabilityKeys.includes(compareVm.access.capabilityKey);

  const isLocked =
    compareVm?.access.state === "locked" && !isDevUnlocked;

  const handleRemove = (urn: string) => {
    const urns = compareVm?.schools.map((s) => s.urn) ?? effectiveUrns ?? [];
    handleRemoveSchool(urn, urns, navigate, removeSchool);
  };

  return (
    <PageContainer className="space-y-6">
      <PageMeta
        title="Compare schools"
        description="Compare up to four schools side by side across inspection, performance, demographics, staffing, and local context."
        canonicalPath={paths.compare()}
        noIndex
      />
      <Breadcrumbs segments={[{ label: "Compare" }]} />

      {/* Header */}
      <header className="space-y-3">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div className="space-y-1.5">
            <p className="text-xs font-semibold tracking-[0.04em] text-brand">
              Compare
            </p>
            <h1 className="text-2xl font-bold tracking-tight text-primary sm:text-3xl">
              Side-by-Side Comparison
            </h1>
            <p className="max-w-2xl text-sm text-secondary">
              Compare up to four schools across inspection, demographics,
              attendance, behaviour, workforce, performance, and neighbourhood context.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <ShareButton />
            <Button asChild variant="secondary">
              <Link to={paths.home}>Back to search</Link>
            </Button>
            {visibleSchools.length > 0 ? (
              <Button
                type="button"
                variant="ghost"
                onClick={() => {
                  skipUrlSyncRef.current = true;
                  clearSchools();
                  navigate("/compare?urns=", { replace: true });
                }}
              >
                Clear all
              </Button>
            ) : null}
          </div>
        </div>

        <p className="text-xs text-disabled tabular-nums" data-testid="compare-summary">
          {effectiveUrns === null
            ? "Loading compare selection..."
            : `${effectiveUrns.length} school${effectiveUrns.length === 1 ? "" : "s"} selected`}
        </p>
      </header>

      {/* Loading */}
      {effectiveUrns === null || state.status === "loading" ? (
        <CompareLoadingState />
      ) : null}

      {/* Empty */}
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

      {/* Single school */}
      {effectiveUrns !== null && effectiveUrns.length === 1 ? (
        <div className="space-y-4">
          <CompareSchoolStrip slots={paddedSlots} onRemoveSchool={handleRemove} />
          <Panel className="space-y-3">
            <h2 className="text-base font-semibold text-primary">
              Add one more school to compare
            </h2>
            <p className="text-sm text-secondary">
              You need at least two schools to build the comparison table.
            </p>
            <Button asChild variant="primary">
              <Link to={paths.home}>Find another school</Link>
            </Button>
          </Panel>
        </div>
      ) : null}

      {/* Error */}
      {effectiveUrns !== null &&
      effectiveUrns.length >= 2 &&
      state.status === "error" ? (
        <div className="space-y-4">
          <ErrorState
            title="Compare is unavailable"
            description={
              state.errorMessage ??
              "The selected schools could not be compared right now."
            }
            onRetry={bumpReloadToken}
          />
          {visibleSchools.length > 0 ? (
            <CompareSchoolStrip slots={paddedSlots} onRemoveSchool={handleRemove} />
          ) : null}
        </div>
      ) : null}

      {/* Success */}
      {compareVm && state.status === "success" && effectiveUrns !== null && effectiveUrns.length >= 2 ? (
        <div className="space-y-5">
          <CompareSchoolStrip
            slots={paddedSlots}
            onRemoveSchool={handleRemove}
          />

          {isLocked ? (
            <ComparePremiumBanner
              compareVm={compareVm}
              currentHref={`${location.pathname}${location.search}`}
            />
          ) : (
            <CompareAccordionSections
              slots={paddedSlots}
              sections={compareVm.sections}
              originUrn={effectiveUrns?.[0] ?? null}
            />
          )}
        </div>
      ) : null}
    </PageContainer>
  );
}

/* ------------------------------------------------------------------ */
/* Loading skeleton                                                    */
/* ------------------------------------------------------------------ */

function CompareLoadingState(): JSX.Element {
  return (
    <div className="space-y-4" aria-live="polite" aria-busy="true">
      <LoadingSkeleton lines={3} />
      <LoadingSkeleton lines={6} />
      <LoadingSkeleton lines={8} />
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Helpers (unchanged logic)                                           */
/* ------------------------------------------------------------------ */

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
      profileState: { fromCompare: { href: compareHref } },
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
        source: "compare",
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
        return error.message || "One or more selected schools could not be found.";
      case 503:
        return error.message || "Compare data is temporarily unavailable.";
      default:
        return error.message;
    }
  }

  if (error instanceof Error) return error.message;

  return "The selected schools could not be compared right now.";
}
