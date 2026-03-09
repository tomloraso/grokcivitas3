import { Link, useLocation, useParams } from "react-router-dom";

import { Breadcrumbs } from "../../components/layout/Breadcrumbs";
import { PageContainer } from "../../components/layout/PageContainer";
import { Button } from "../../components/ui/Button";
import { ErrorState } from "../../components/ui/ErrorState";
import { LoadingSkeleton } from "../../components/ui/LoadingSkeleton";
import { useToast } from "../../components/ui/ToastContext";
import { useCompareSelection } from "../../shared/context/CompareSelectionContext";
import { paths } from "../../shared/routing/paths";
import type { SearchRestoreState } from "../../shared/search/searchState";
import { AcademicPerformanceSection } from "./components/AcademicPerformanceSection";
import { SchoolAnalystSection } from "./components/SchoolAnalystSection";
import { AttendanceBehaviourSection } from "./components/AttendanceBehaviourSection";
import { CoverageNotice } from "./components/CoverageNotice";
import { DemographicsAndTrendsPanel } from "./components/DemographicsAndTrendsPanel";
import { NeighbourhoodSection } from "./components/NeighbourhoodSection";
import { OfstedProfileSection } from "./components/OfstedProfileSection";
import { ProfileHeader } from "./components/ProfileHeader";
import { SchoolOverviewSection } from "./components/SchoolOverviewSection";
import { WorkforceLeadershipSection } from "./components/WorkforceLeadershipSection";
import { useSchoolProfile } from "./hooks/useSchoolProfile";

export function SchoolProfileFeature(): JSX.Element {
  const { urn } = useParams<{ urn: string }>();
  const location = useLocation();
  const routeState = location.state as {
    fromSearch?: SearchRestoreState;
    fromCompare?: { href: string };
  } | null;
  const fromSearch = routeState?.fromSearch;
  const fromCompare = routeState?.fromCompare;
  const { toast } = useToast();
  const { addSchool, hasSchool, items, removeSchool } = useCompareSelection();
  const { status, profile, errorMessage, retry } = useSchoolProfile(urn);
  const selected = profile ? hasSchool(profile.school.urn) : false;

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
                      href: paths.homeSearch({
                        view: fromSearch.view,
                        resultsPhases: fromSearch.resultsPhases,
                        resultsSort: fromSearch.resultsSort,
                      }),
                      state: { restoreSearch: fromSearch }
                    }
                  ]
                : []),
              ...(fromCompare ? [{ label: "Compare", href: fromCompare.href }] : []),
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
              actions={
                <>
                  <Button
                    type="button"
                    variant="compare"
                    size="none"
                    onClick={() => {
                      if (selected) {
                        removeSchool(profile.school.urn);
                        return;
                      }

                      const result = addSchool({
                        urn: profile.school.urn,
                        name: profile.school.name,
                        phase: profile.school.phase,
                        type: profile.school.type,
                        postcode: profile.school.postcode,
                        source: "profile",
                      });
                      if (result === "limit") {
                        toast({
                          title: "Compare limit reached",
                          description: "You can compare up to four schools at a time.",
                          variant: "warning",
                        });
                      }
                    }}
                  >
                    {selected ? "Remove from compare" : "Add to compare"}
                  </Button>
                  {items.length >= 2 ? (
                    <Button asChild variant="compare" size="none">
                      <Link to={paths.compare(items.map((item) => item.urn))}>Open compare</Link>
                    </Button>
                  ) : null}
                </>
              }
            />

            <SchoolOverviewSection overviewText={profile.overviewText} />
            <SchoolAnalystSection analystText={profile.analystText} />

            <div className="space-y-10 sm:space-y-12">
              <OfstedProfileSection
                providerPageUrl={profile.ofsted?.providerPageUrl ?? null}
                ofsted={profile.ofsted}
                timeline={profile.ofstedTimeline}
                ofstedCompleteness={profile.completeness.ofstedLatest}
                timelineCompleteness={profile.completeness.ofstedTimeline}
              />

              <AcademicPerformanceSection
                performance={profile.performance}
                completeness={profile.completeness.performance}
                benchmarkDashboard={profile.benchmarkDashboard}
              />

              <AttendanceBehaviourSection
                attendance={profile.attendance}
                behaviour={profile.behaviour}
                trends={profile.trends}
                attendanceCompleteness={profile.completeness.attendance}
                behaviourCompleteness={profile.completeness.behaviour}
                benchmarkDashboard={profile.benchmarkDashboard}
              />

              <DemographicsAndTrendsPanel
                demographics={profile.demographics}
                trends={profile.trends}
                demographicsCompleteness={profile.completeness.demographics}
                trendsCompleteness={profile.completeness.trends}
              />

              <WorkforceLeadershipSection
                workforce={profile.workforce}
                leadership={profile.leadership}
                trends={profile.trends}
                workforceCompleteness={profile.completeness.workforce}
                leadershipCompleteness={profile.completeness.leadership}
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
