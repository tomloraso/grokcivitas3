import { Link } from "react-router-dom";
import { ExternalLink, Clock3, GraduationCap, Building2, MapPin } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { RatingBadge } from "../../components/data/RatingBadge";
import { Breadcrumbs } from "../../components/layout/Breadcrumbs";
import { PageContainer } from "../../components/layout/PageContainer";
import { Button } from "../../components/ui/Button";
import { Card, Panel } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { ErrorState } from "../../components/ui/ErrorState";
import { LoadingSkeleton } from "../../components/ui/LoadingSkeleton";
import { paths } from "../../shared/routing/paths";
import { buildAccessActionHref } from "../premium-access/copy";
import { useAuth } from "../auth/useAuth";
import { SaveSchoolButton } from "./components/SaveSchoolButton";
import { useAccountFavourites } from "./hooks/useAccountFavourites";
import type { AccountFavouriteSchoolVM, SavedSchoolStateVM } from "./types";

function formatSavedAt(iso: string | null): string {
  if (!iso) {
    return "Saved recently";
  }

  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) {
    return iso;
  }

  return date.toLocaleString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "UTC"
  });
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

function savedStateForSchool(school: AccountFavouriteSchoolVM): SavedSchoolStateVM {
  return {
    status: "saved",
    savedAt: school.savedAt,
    capabilityKey: null,
    reasonCode: null
  };
}

function FavouriteSchoolCard({
  school,
  onRemove
}: {
  school: AccountFavouriteSchoolVM;
  onRemove: (urn: string) => void;
}): JSX.Element {
  return (
    <Card className="space-y-5 border-border-subtle/80 bg-surface/80">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-3">
          <div className="space-y-1">
            <h2 className="text-xl font-semibold text-primary">{school.name}</h2>
            <div className="flex flex-wrap items-center gap-2 text-sm text-secondary">
              <span className="inline-flex items-center gap-1.5 rounded-full border border-border-subtle/70 bg-surface/60 px-3 py-1">
                <GraduationCap className="h-3.5 w-3.5" aria-hidden />
                {school.phase ?? "Unknown"}
              </span>
              <span className="inline-flex items-center gap-1.5 rounded-full border border-border-subtle/70 bg-surface/60 px-3 py-1">
                <Building2 className="h-3.5 w-3.5" aria-hidden />
                {school.type ?? "Unknown"}
              </span>
              <span className="inline-flex items-center gap-1.5 rounded-full border border-border-subtle/70 bg-surface/60 px-3 py-1 font-mono">
                <MapPin className="h-3.5 w-3.5" aria-hidden />
                {school.postcode ?? "No postcode"}
              </span>
            </div>
          </div>

          <p className="inline-flex items-center gap-2 text-sm text-secondary">
            <Clock3 className="h-4 w-4" aria-hidden />
            Saved {formatSavedAt(school.savedAt)}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Button asChild variant="secondary" size="sm">
            <Link to={paths.schoolProfile(school.urn)}>
              <ExternalLink className="mr-1.5 h-3.5 w-3.5" aria-hidden />
              View profile
            </Link>
          </Button>
          <SaveSchoolButton
            schoolUrn={school.urn}
            savedState={savedStateForSchool(school)}
            onSavedStateChange={(nextState) => {
              if (nextState.status !== "saved") {
                onRemove(school.urn);
              }
            }}
          />
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-3">
        <div className="rounded-lg border border-border-subtle/70 bg-surface/50 p-4">
          <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-disabled">
            Latest Ofsted
          </p>
          <div className="mt-3">
            {school.latestOfsted.availability === "published" ? (
              <RatingBadge
                ratingCode={
                  school.latestOfsted.sortRank == null
                    ? null
                    : String(school.latestOfsted.sortRank)
                }
                label={school.latestOfsted.label}
              />
            ) : (
              <p className="text-sm text-secondary">
                {formatAvailability(school.latestOfsted.availability)}
              </p>
            )}
          </div>
        </div>

        <div className="rounded-lg border border-border-subtle/70 bg-surface/50 p-4">
          <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-disabled">
            Academic signal
          </p>
          <p className="mt-3 text-base font-semibold text-primary">
            {school.academicMetric.availability === "published"
              ? school.academicMetric.displayValue ?? "Published"
              : formatAvailability(school.academicMetric.availability)}
          </p>
          <p className="mt-1 text-sm text-secondary">
            {school.academicMetric.label ?? "Academic signal"}
          </p>
        </div>

        <div className="rounded-lg border border-border-subtle/70 bg-surface/50 p-4">
          <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-disabled">
            Pupils
          </p>
          <p className="mt-3 text-base font-semibold text-primary">
            {school.pupilCount == null
              ? "Not published"
              : school.pupilCount.toLocaleString("en-GB")}
          </p>
          <p className="mt-1 text-sm text-secondary">Current summary record</p>
        </div>
      </div>
    </Card>
  );
}

export function FavouritesLibraryFeature(): JSX.Element {
  const { session } = useAuth();
  const { status, favourites, errorMessage, reload } = useAccountFavourites();
  const [removedUrns, setRemovedUrns] = useState<string[]>([]);

  useEffect(() => {
    setRemovedUrns([]);
  }, [favourites]);

  const visibleSchools = useMemo(
    () =>
      (favourites?.schools ?? []).filter((school) => !removedUrns.includes(school.urn)),
    [favourites, removedUrns]
  );

  if (session.state !== "authenticated") {
    return (
      <PageContainer className="space-y-8">
        <Breadcrumbs
          segments={[{ label: "Account", href: paths.account }, { label: "Saved schools" }]}
        />
        <Panel className="space-y-4">
          <h1 className="text-3xl font-semibold text-primary sm:text-4xl">
            Saved schools
          </h1>
          <p className="max-w-2xl text-sm text-secondary sm:text-base">
            Sign in to save schools to your account and keep your shortlist available across sessions.
          </p>
          <div className="flex flex-wrap gap-3">
            <Button asChild>
              <Link to={paths.signIn(paths.accountFavourites)}>Sign in</Link>
            </Button>
            <Button asChild variant="secondary">
              <Link to={paths.home}>Browse schools</Link>
            </Button>
          </div>
        </Panel>
      </PageContainer>
    );
  }

  const accountAccess = favourites?.access ?? null;

  return (
    <PageContainer className="space-y-8">
      <Breadcrumbs
        segments={[{ label: "Account", href: paths.account }, { label: "Saved schools" }]}
      />

      <header className="space-y-3">
        <p className="eyebrow">Saved research</p>
        <h1 className="text-3xl font-semibold text-primary sm:text-4xl">
          Saved schools
        </h1>
        <p className="max-w-3xl text-sm text-secondary sm:text-base">
          Keep schools you want to revisit in one account-owned library. Latest saved appears first.
        </p>
      </header>

      {status === "loading" && !favourites ? (
        <div className="space-y-4">
          <LoadingSkeleton lines={4} />
          <LoadingSkeleton lines={6} />
        </div>
      ) : null}

      {status === "error" ? (
        <ErrorState
          title="Saved schools unavailable"
          description={errorMessage ?? "The saved schools library could not be loaded."}
          onRetry={reload}
        />
      ) : null}

      {accountAccess?.state === "locked" ? (
        <Panel className="space-y-4">
          <h2 className="text-xl font-semibold text-primary">
            Saved schools require Premium
          </h2>
          <p className="text-sm text-secondary">
            Upgrade this account to unlock saved research across your school discovery workflow.
          </p>
          <div className="flex flex-wrap gap-3">
            <Button asChild>
              <Link
                to={buildAccessActionHref({
                  access: accountAccess,
                  returnTo: paths.accountFavourites
                })}
              >
                {accountAccess.requiresAuth ? "Sign in to continue" : "View Premium plans"}
              </Link>
            </Button>
            <Button asChild variant="secondary">
              <Link to={paths.home}>Browse schools</Link>
            </Button>
          </div>
        </Panel>
      ) : null}

      {favourites && accountAccess?.state !== "locked" && visibleSchools.length === 0 ? (
        <EmptyState
          title="No saved schools yet"
          description="Save a school from postcode results, name search, or a profile page to build your research library."
          action={
            <Button asChild>
              <Link to={paths.home}>Search for schools</Link>
            </Button>
          }
        />
      ) : null}

      {favourites && accountAccess?.state !== "locked" && visibleSchools.length > 0 ? (
        <div className="space-y-4">
          <p className="text-sm text-secondary">
            <span className="font-semibold text-primary">{visibleSchools.length}</span>{" "}
            {visibleSchools.length === 1 ? "school" : "schools"} saved to this account.
          </p>
          <div className="space-y-4">
            {visibleSchools.map((school) => (
              <FavouriteSchoolCard
                key={school.urn}
                school={school}
                onRemove={(urn) => {
                  setRemovedUrns((current) =>
                    current.includes(urn) ? current : [...current, urn]
                  );
                }}
              />
            ))}
          </div>
        </div>
      ) : null}
    </PageContainer>
  );
}
