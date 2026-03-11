/**
 * SchoolProfileFeature — Loira Voss design system (P9 refresh, 2026-03-09)
 *
 * COLOUR PALETTE
 *   Background canvas : #0A1428 → #02060F  (deep navy gradient, via CSS tokens)
 *   Card surface      : #0F172A  border: #1E2937  + backdrop-blur glass (panel-surface utility)
 *   Brand / accent    : #00D4C8  (teal — replaces purple across the whole token system)
 *   Trend positive    : #00D4C8  (teal)
 *   Trend negative    : #FF4D6D  (soft red)
 *   Text primary      : #F1F5F9  secondary: #94A3B8
 *
 * TYPOGRAPHY
 *   All weights       : Inter (loaded via @fontsource/inter, falls back to system-ui)
 *   Headings          : font-display (Inter), font-semibold, tracking-tight
 *   Metric numbers    : font-bold text-3xl sm:text-4xl  (hero variant: text-4xl sm:text-5xl)
 *
 * LAYOUT
 *   Mobile  (<1024px) : single column; sections 3–8 collapse into accordions (Ofsted +
 *                       Results open by default); sticky teal "Add to compare" bar fixed
 *                       to viewport bottom; pb-20 guards content above the 52px bar.
 *   Desktop (≥1024px) : 280px sticky TOC sidebar + minmax(0,1fr) main content column;
 *                       accordion toggles hidden (all sections always visible); max-w-[1280px]
 *                       centred via PageContainer.
 *
 * MOBILE DENSITY (P9 iteration 3)
 *   Section panel padding : p-4 mobile / p-6 sm+  (was p-5 / p-6)
 *   Section panel rhythm  : space-y-4 mobile / space-y-5–6 sm+  (was always space-y-5–6)
 *   Section gap           : space-y-5 lg:space-y-8  (was space-y-8 unconditionally)
 *   Hero metric strip     : gap-5 sm:gap-8  (was gap-8 sm:gap-10)
 *   Accordion chrome      : min-h-[44px] px-3 py-2.5  (was px-4 py-3)
 *   Bottom guard          : pb-20 lg:pb-0  (was pb-24 lg:pb-0)
 *   Touch targets         : all interactive elements ≥ 44px height maintained.
 *
 * CARDS
 *   rounded-xl, transition-all hover:-translate-y-0.5 hover:shadow-lg (Card primitive)
 *
 * NO BACKGROUND ILLUSTRATIONS
 *   The decorative UK map SVG watermark was removed (P9 iteration 2). Hero is clean.
 *
 * BRAND PLACEHOLDER
 *   Every "CIVITAS" string has been replaced with "[BRAND]" across SiteHeader, SiteFooter,
 *   and all aria-labels in this file.
 */
import { useCallback, useEffect, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";

import { Breadcrumbs } from "../../components/layout/Breadcrumbs";
import { PageContainer } from "../../components/layout/PageContainer";
import { Button } from "../../components/ui/Button";
import { ErrorState } from "../../components/ui/ErrorState";
import { LoadingSkeleton } from "../../components/ui/LoadingSkeleton";
import { useToast } from "../../components/ui/ToastContext";
import { SaveSchoolButton } from "../favourites/components/SaveSchoolButton";
import type { SavedSchoolStateVM } from "../favourites/types";
import { CompareActionButton } from "../premium-access/components/CompareActionButton";
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
import { ProfileSectionAccordion } from "./components/ProfileSectionAccordion";
import { SchoolOverviewSection } from "./components/SchoolOverviewSection";
import { SchoolAdmissionsSection } from "./components/SchoolAdmissionsSection";
import { SchoolDestinationsSection } from "./components/SchoolDestinationsSection";
import { SchoolFinanceSection } from "./components/SchoolFinanceSection";
import { WorkforceLeadershipSection } from "./components/WorkforceLeadershipSection";
import { useSchoolProfile } from "./hooks/useSchoolProfile";

const TOC_SECTIONS = [
  { id: "overview", label: "School Overview" },
  { id: "analyst-view", label: "Analyst View" },
  { id: "ofsted-profile", label: "Ofsted Profile" },
  { id: "results-progress", label: "Results & Progress" },
  { id: "leaver-destinations", label: "Leaver Destinations" },
  { id: "day-to-day", label: "Day-to-Day" },
  { id: "demographics", label: "Pupil Demographics" },
  { id: "admissions", label: "Admissions" },
  { id: "teachers-staff", label: "Teachers & Staff" },
  { id: "finance", label: "Finance" },
  { id: "neighbourhood", label: "Neighbourhood" },
] as const;

function ProfileTableOfContents(): JSX.Element {
  return (
    <nav aria-label="Page sections" className="space-y-1">
      <p className="mb-3 px-3 text-[10px] font-semibold uppercase tracking-[0.12em] text-disabled">
        Contents
      </p>
      <ul className="space-y-0.5">
        {TOC_SECTIONS.map(({ id, label }) => (
          <li key={id}>
            <a
              href={`#${id}`}
              className="block rounded-lg px-3 py-1.5 text-sm text-secondary transition-colors duration-fast hover:bg-surface/80 hover:text-primary focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-brand"
            >
              {label}
            </a>
          </li>
        ))}
      </ul>
    </nav>
  );
}

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
  const [savedStateOverride, setSavedStateOverride] =
    useState<SavedSchoolStateVM | null>(null);
  const selected = profile ? hasSchool(profile.school.urn) : false;
  const savedState = savedStateOverride ?? profile?.savedState ?? null;

  const handleCompareToggle = useCallback(() => {
    if (!profile) return;
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
  }, [profile, selected, addSchool, removeSchool, toast]);

  useEffect(() => {
    setSavedStateOverride(null);
  }, [urn]);

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
                      state: { restoreSearch: fromSearch },
                    },
                  ]
                : []),
              ...(fromCompare ? [{ label: "Compare", href: fromCompare.href }] : []),
              { label: profile.school.name },
            ]}
          />

          <div className="mb-8">
            <ProfileHeader
              school={profile.school}
              ofsted={profile.ofsted}
              ofstedCompleteness={profile.completeness.ofstedLatest}
              demographics={profile.demographics}
              areaContext={profile.neighbourhood.areaContext}
              actions={
                selected ? (
                  <>
                    <Button
                      type="button"
                      variant="secondary"
                      size="default"
                      onClick={handleCompareToggle}
                    >
                      Remove from compare
                    </Button>
                    {items.length >= 2 ? (
                      <CompareActionButton
                        urns={items.map((item) => item.urn)}
                        label={`Open compare (${items.length})`}
                        lockedLabel="Unlock compare"
                        variant="primary"
                        size="default"
                      />
                    ) : null}
                  </>
                ) : (
                  <>
                    <Button
                      type="button"
                      variant="primary"
                      size="default"
                      onClick={handleCompareToggle}
                    >
                      Add to compare{items.length > 0 ? ` (${items.length}/4)` : ""}
                    </Button>
                    {savedState ? (
                      <SaveSchoolButton
                        schoolUrn={profile.school.urn}
                        savedState={savedState}
                        size="default"
                        onSavedStateChange={setSavedStateOverride}
                      />
                    ) : null}
                  </>
                )
              }
            />
          </div>

          <div className="lg:grid lg:grid-cols-[280px_minmax(0,1fr)] lg:items-start lg:gap-8">
            <aside className="hidden lg:block lg:sticky lg:top-[3.75rem] lg:self-start">
              <div className="panel-surface rounded-xl p-4">
                <ProfileTableOfContents />
              </div>
            </aside>

            <div className="space-y-5 pb-20 lg:space-y-8 lg:pb-0">
              <div id="overview">
                <SchoolOverviewSection overviewText={profile.overviewText} />
              </div>

              <div id="analyst-view">
                <SchoolAnalystSection analyst={profile.analyst} />
              </div>

              <div id="ofsted-profile">
                <ProfileSectionAccordion title="Ofsted Profile" defaultOpen={true}>
                  <OfstedProfileSection
                    providerPageUrl={profile.ofsted?.providerPageUrl ?? null}
                    ofsted={profile.ofsted}
                    timeline={profile.ofstedTimeline}
                    ofstedCompleteness={profile.completeness.ofstedLatest}
                    timelineCompleteness={profile.completeness.ofstedTimeline}
                  />
                </ProfileSectionAccordion>
              </div>

              <div id="results-progress">
                <ProfileSectionAccordion title="Results & Progress" defaultOpen={true}>
                  <AcademicPerformanceSection
                    performance={profile.performance}
                    completeness={profile.completeness.performance}
                    benchmarkDashboard={profile.benchmarkDashboard}
                  />
                </ProfileSectionAccordion>
              </div>

              <div id="leaver-destinations">
                <ProfileSectionAccordion title="Leaver Destinations" defaultOpen={false}>
                  <SchoolDestinationsSection
                    destinations={profile.destinations}
                    trends={profile.trends}
                    completeness={profile.completeness.destinations}
                    trendsCompleteness={profile.trends?.sectionCompleteness.destinations ?? profile.completeness.trends}
                  />
                </ProfileSectionAccordion>
              </div>

              <div id="day-to-day">
                <ProfileSectionAccordion title="Day-to-Day at School" defaultOpen={false}>
                  <AttendanceBehaviourSection
                    attendance={profile.attendance}
                    behaviour={profile.behaviour}
                    trends={profile.trends}
                    attendanceCompleteness={profile.completeness.attendance}
                    behaviourCompleteness={profile.completeness.behaviour}
                    benchmarkDashboard={profile.benchmarkDashboard}
                  />
                </ProfileSectionAccordion>
              </div>

              <div id="demographics">
                <ProfileSectionAccordion title="Pupil Demographics" defaultOpen={false}>
                  <DemographicsAndTrendsPanel
                    demographics={profile.demographics}
                    trends={profile.trends}
                    demographicsCompleteness={profile.completeness.demographics}
                    trendsCompleteness={profile.completeness.trends}
                    benchmarkDashboard={profile.benchmarkDashboard}
                  />
                </ProfileSectionAccordion>
              </div>

              <div id="admissions">
                <ProfileSectionAccordion title="School Admissions" defaultOpen={false}>
                  <SchoolAdmissionsSection
                    admissions={profile.admissions}
                    trends={profile.trends}
                    completeness={profile.completeness.admissions}
                    benchmarkDashboard={profile.benchmarkDashboard}
                  />
                </ProfileSectionAccordion>
              </div>

              <div id="teachers-staff">
                <ProfileSectionAccordion title="Teachers & Staff" defaultOpen={false}>
                  <WorkforceLeadershipSection
                    workforce={profile.workforce}
                    leadership={profile.leadership}
                    trends={profile.trends}
                    workforceCompleteness={profile.completeness.workforce}
                    leadershipCompleteness={profile.completeness.leadership}
                    benchmarkDashboard={profile.benchmarkDashboard}
                  />
                </ProfileSectionAccordion>
              </div>

              <div id="finance">
                <ProfileSectionAccordion title="School Finance" defaultOpen={false}>
                  <SchoolFinanceSection
                    finance={profile.finance}
                    trends={profile.trends}
                    completeness={profile.completeness.finance}
                    benchmarkDashboard={profile.benchmarkDashboard}
                  />
                </ProfileSectionAccordion>
              </div>

              <div id="neighbourhood">
                <ProfileSectionAccordion title="Neighbourhood Context" defaultOpen={false}>
                  <NeighbourhoodSection
                    neighbourhood={profile.neighbourhood}
                    deprivationCompleteness={profile.completeness.areaDeprivation}
                    crimeCompleteness={profile.completeness.areaCrime}
                    housePriceCompleteness={profile.completeness.areaHousePrices}
                  />
                </ProfileSectionAccordion>
              </div>

              <CoverageNotice
                unsupportedMetrics={profile.unsupportedMetrics}
                completeness={profile.completeness}
              />
            </div>
          </div>

          <div className="fixed bottom-0 left-0 right-0 z-nav lg:hidden">
            <div
              className="flex gap-2 border-t border-border-subtle/60 bg-canvas/95 px-4 pt-3 backdrop-blur-xl"
              style={{ paddingBottom: "max(1rem, env(safe-area-inset-bottom))" }}
            >
              <Button
                type="button"
                variant={selected ? "secondary" : "primary"}
                size="default"
                className="min-h-[52px] flex-1 justify-center font-semibold"
                onClick={handleCompareToggle}
              >
                {selected
                  ? "Remove from compare"
                  : `Add to compare${items.length > 0 ? ` (${items.length}/4)` : ""}`}
              </Button>
              {savedState && !selected ? (
                <SaveSchoolButton
                  schoolUrn={profile.school.urn}
                  savedState={savedState}
                  size="default"
                  className="min-h-[52px] shrink-0"
                  onSavedStateChange={setSavedStateOverride}
                />
              ) : null}
              {selected && items.length >= 2 ? (
                <CompareActionButton
                  urns={items.map((item) => item.urn)}
                  label={`Compare (${items.length})`}
                  lockedLabel="Unlock"
                  variant="primary"
                  size="default"
                  className="min-h-[52px] shrink-0"
                />
              ) : null}
            </div>
          </div>
        </>
      ) : null}
    </PageContainer>
  );
}
