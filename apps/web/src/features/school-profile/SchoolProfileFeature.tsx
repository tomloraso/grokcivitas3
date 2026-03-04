import { useParams, useLocation, Link } from "react-router-dom";

import { Breadcrumbs } from "../../components/layout/Breadcrumbs";
import { PageContainer } from "../../components/layout/PageContainer";
import { Button } from "../../components/ui/Button";
import { ErrorState } from "../../components/ui/ErrorState";
import { LoadingSkeleton } from "../../components/ui/LoadingSkeleton";
import { paths } from "../../shared/routing/paths";
import { AreaCrimeSummaryCard } from "./components/AreaCrimeSummaryCard";
import { AreaDeprivationCard } from "./components/AreaDeprivationCard";
import { CoverageNotice } from "./components/CoverageNotice";
import { DemographicsSummary } from "./components/DemographicsSummary";
import { KeyFactsSummary } from "./components/KeyFactsSummary";
import { OfstedHeadlineCard } from "./components/OfstedHeadlineCard";
import { OfstedTimelineCard } from "./components/OfstedTimelineCard";
import { ProfileHeader } from "./components/ProfileHeader";
import { TrendPanel } from "./components/TrendPanel";
import { useSchoolProfile } from "./hooks/useSchoolProfile";

export function SchoolProfileFeature(): JSX.Element {
  const { urn } = useParams<{ urn: string }>();
  const location = useLocation();
  const fromSearch = (location.state as { fromSearch?: { postcode: string; radius: number } } | null)?.fromSearch;
  const { status, profile, errorMessage, retry } = useSchoolProfile(urn);

  return (
    <PageContainer>
      {/* Loading */}
      {(status === "idle" || status === "loading") ? (
        <>
          <Breadcrumbs segments={[{ label: "Loading..." }]} />
          <div className="space-y-6">
            <LoadingSkeleton lines={4} />
            <LoadingSkeleton lines={6} />
            <LoadingSkeleton lines={4} />
          </div>
        </>
      ) : null}

      {/* Not found */}
      {status === "not-found" ? (
        <>
          <Breadcrumbs segments={[{ label: "Not Found" }]} />
          <ErrorState
            title="School not found"
            description={`No school was found with URN ${urn ?? "unknown"}. It may have been removed or the URN is incorrect.`}
            action={
              <Button asChild variant="primary">
                <Link to={paths.home}>Back to search</Link>
              </Button>
            }
          />
        </>
      ) : null}

      {/* Error */}
      {status === "error" ? (
        <>
          <Breadcrumbs segments={[{ label: "Error" }]} />
          <ErrorState
            title="Something went wrong"
            description={errorMessage ?? "An unexpected error occurred while loading the school profile."}
            onRetry={retry}
          />
        </>
      ) : null}

      {/* Success */}
      {status === "success" && profile ? (
        <>
          <Breadcrumbs
            segments={[
              ...(fromSearch
                ? [{
                    label: `${fromSearch.postcode} · ${fromSearch.radius} mi`,
                    href: paths.home,
                    state: { restoreSearch: fromSearch },
                  }]
                : []),
              { label: profile.school.name },
            ]}
          />

          <div className="space-y-10 sm:space-y-12">
            {/* School identity header */}
            <ProfileHeader school={profile.school} />

            {/* Key facts — prominent at-a-glance summary */}
            <KeyFactsSummary
              ofsted={profile.ofsted}
              demographics={profile.demographics}
              areaContext={profile.areaContext}
            />

            {/* Ofsted + demographics row on larger screens */}
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_2fr]">
              {/* Ofsted headline */}
              <OfstedHeadlineCard
                ofsted={profile.ofsted}
                completeness={profile.completeness.ofstedLatest}
              />

              {/* Demographics summary — current-year values only */}
              <DemographicsSummary
                demographics={profile.demographics}
                completeness={profile.completeness.demographics}
              />
            </div>

            {/* Trends — directional change only, suppressed when < 2 years */}
            <TrendPanel trends={profile.trends} completeness={profile.completeness.trends} />

            {/* Ofsted timeline */}
            <OfstedTimelineCard
              timeline={profile.ofstedTimeline}
              completeness={profile.completeness.ofstedTimeline}
            />

            {/* Area context */}
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
              <AreaDeprivationCard
                areaContext={profile.areaContext}
                completeness={profile.completeness.areaDeprivation}
              />
              <AreaCrimeSummaryCard
                areaContext={profile.areaContext}
                completeness={profile.completeness.areaCrime}
              />
            </div>

            {/* Coverage notice */}
            <CoverageNotice
              unsupportedMetrics={profile.unsupportedMetrics}
              completeness={profile.completeness}
            />
          </div>
        </>
      ) : null}
    </PageContainer>
  );
}
