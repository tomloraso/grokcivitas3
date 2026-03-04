import { useLocation, useParams, Link } from "react-router-dom";

import { Breadcrumbs } from "../../components/layout/Breadcrumbs";
import { PageContainer } from "../../components/layout/PageContainer";
import { Button } from "../../components/ui/Button";
import { ErrorState } from "../../components/ui/ErrorState";
import { LoadingSkeleton } from "../../components/ui/LoadingSkeleton";
import { paths } from "../../shared/routing/paths";
import { CoverageNotice } from "./components/CoverageNotice";
import { DemographicsAndTrendsPanel } from "./components/DemographicsAndTrendsPanel";
import { NeighbourhoodSection } from "./components/NeighbourhoodSection";
import { OfstedTimelineCard } from "./components/OfstedTimelineCard";
import { ProfileHeader } from "./components/ProfileHeader";
import { useSchoolProfile } from "./hooks/useSchoolProfile";

export function SchoolProfileFeature(): JSX.Element {
  const { urn } = useParams<{ urn: string }>();
  const location = useLocation();
  const fromSearch = (
    location.state as { fromSearch?: { postcode: string; radius: number } } | null
  )?.fromSearch;
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
            description={
              errorMessage ?? "An unexpected error occurred while loading the school profile."
            }
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
                ? [
                    {
                      label: `${fromSearch.postcode} - ${fromSearch.radius} mi`,
                      href: paths.home,
                      state: { restoreSearch: fromSearch },
                    },
                  ]
                : []),
              { label: profile.school.name },
            ]}
          />

          <div className="space-y-14 sm:space-y-16">
            {/* Zone 1: Hero */}
            <ProfileHeader
              school={profile.school}
              ofsted={profile.ofsted}
              ofstedCompleteness={profile.completeness.ofstedLatest}
              demographics={profile.demographics}
              areaContext={profile.areaContext}
            />

            {/* Zone 2: The School */}
            <div className="space-y-10 sm:space-y-12">
              {/* Ofsted timeline - inspection record comes first */}
              <OfstedTimelineCard
                timeline={profile.ofstedTimeline}
                completeness={profile.completeness.ofstedTimeline}
              />

              {/* Demographics & Trends - unified section */}
              <DemographicsAndTrendsPanel
                demographics={profile.demographics}
                trends={profile.trends}
                demographicsCompleteness={profile.completeness.demographics}
                trendsCompleteness={profile.completeness.trends}
              />
            </div>

            {/* Zone 3: The Neighbourhood */}
            <NeighbourhoodSection
              areaContext={profile.areaContext}
              deprivationCompleteness={profile.completeness.areaDeprivation}
              crimeCompleteness={profile.completeness.areaCrime}
            />

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
