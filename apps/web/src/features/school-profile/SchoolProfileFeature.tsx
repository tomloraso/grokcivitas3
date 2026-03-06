import { Link, useLocation, useParams } from "react-router-dom";

import { Breadcrumbs } from "../../components/layout/Breadcrumbs";
import { PageContainer } from "../../components/layout/PageContainer";
import { Button } from "../../components/ui/Button";
import { ErrorState } from "../../components/ui/ErrorState";
import { LoadingSkeleton } from "../../components/ui/LoadingSkeleton";
import { paths } from "../../shared/routing/paths";
import { AcademicPerformanceSection } from "./components/AcademicPerformanceSection";
import { SchoolAnalystSection } from "./components/SchoolAnalystSection";
import { AttendanceBehaviourSection } from "./components/AttendanceBehaviourSection";
import { BenchmarkComparisonSection } from "./components/BenchmarkComparisonSection";
import { CoverageNotice } from "./components/CoverageNotice";
import { DemographicsAndTrendsPanel } from "./components/DemographicsAndTrendsPanel";
import { NeighbourhoodSection } from "./components/NeighbourhoodSection";
import { OfstedProfileSection } from "./components/OfstedProfileSection";
import { ProfileHeader } from "./components/ProfileHeader";
import { SchoolDetailsSection } from "./components/SchoolDetailsSection";
import { SchoolOverviewSection } from "./components/SchoolOverviewSection";
import { WorkforceLeadershipSection } from "./components/WorkforceLeadershipSection";
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

      {status === "success" && profile ? (
        <>
          <Breadcrumbs
            segments={[
              ...(fromSearch
                ? [
                    {
                      label: `${fromSearch.postcode} - ${fromSearch.radius} mi`,
                      href: paths.home,
                      state: { restoreSearch: fromSearch }
                    }
                  ]
                : []),
              { label: profile.school.name }
            ]}
          />

          <div className="space-y-14 sm:space-y-16">
            <ProfileHeader
              school={profile.school}
              ofsted={profile.ofsted}
              ofstedCompleteness={profile.completeness.ofstedLatest}
              demographics={profile.demographics}
              areaContext={profile.areaContext}
            />

            <SchoolOverviewSection overviewText={profile.overviewText} />
            <SchoolAnalystSection analystText={profile.analystText} />

            <SchoolDetailsSection school={profile.school} />

            <div className="space-y-10 sm:space-y-12">
              <OfstedProfileSection
                ofsted={profile.ofsted}
                timeline={profile.ofstedTimeline}
                ofstedCompleteness={profile.completeness.ofstedLatest}
                timelineCompleteness={profile.completeness.ofstedTimeline}
              />

              <DemographicsAndTrendsPanel
                demographics={profile.demographics}
                trends={profile.trends}
                demographicsCompleteness={profile.completeness.demographics}
                trendsCompleteness={profile.completeness.trends}
              />

              <AttendanceBehaviourSection
                attendance={profile.attendance}
                behaviour={profile.behaviour}
                trends={profile.trends}
                attendanceCompleteness={profile.completeness.attendance}
                behaviourCompleteness={profile.completeness.behaviour}
              />

              <WorkforceLeadershipSection
                workforce={profile.workforce}
                leadership={profile.leadership}
                trends={profile.trends}
                workforceCompleteness={profile.completeness.workforce}
                leadershipCompleteness={profile.completeness.leadership}
              />

              <AcademicPerformanceSection
                performance={profile.performance}
                completeness={profile.completeness.performance}
              />

              <BenchmarkComparisonSection
                benchmarkDashboard={profile.benchmarkDashboard}
              />
            </div>

            <NeighbourhoodSection
              areaContext={profile.areaContext}
              deprivationCompleteness={profile.completeness.areaDeprivation}
              crimeCompleteness={profile.completeness.areaCrime}
              housePriceCompleteness={profile.completeness.areaHousePrices}
            />

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
