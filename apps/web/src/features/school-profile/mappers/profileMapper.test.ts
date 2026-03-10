import { describe, expect, it } from "vitest";

import { DASHBOARD_RESPONSE, PROFILE_RESPONSE, TRENDS_RESPONSE } from "../testData";
import {
  fallback,
  fmtDate,
  fmtPct,
  mapCompletenessReasonToMessageKey,
  mapProfileToVM
} from "./profileMapper";

describe("fmtPct", () => {
  it("formats a number to 1dp with % suffix", () => {
    expect(fmtPct(17.2)).toBe("17.2%");
  });

  it("returns null for null input", () => {
    expect(fmtPct(null)).toBeNull();
  });
});

describe("fmtDate", () => {
  it("formats an ISO date to readable UK format", () => {
    expect(fmtDate("2025-10-10")).toMatch(/10.*Oct.*2025/);
  });
});

describe("fallback", () => {
  it("returns the placeholder for empty values", () => {
    expect(fallback(null, "Unknown")).toBe("Unknown");
    expect(fallback("", "Unknown")).toBe("Unknown");
    expect(fallback("   ", "Unknown")).toBe("Unknown");
  });
});

describe("mapCompletenessReasonToMessageKey", () => {
  it("maps backend reason codes to stable UI message keys", () => {
    expect(mapCompletenessReasonToMessageKey("source_missing")).toBe("missing");
    expect(mapCompletenessReasonToMessageKey("partial_metric_coverage")).toBe(
      "partialMetricCoverage"
    );
    expect(mapCompletenessReasonToMessageKey("stale_after_school_refresh")).toBe(
      "staleAfterSchoolRefresh"
    );
    expect(mapCompletenessReasonToMessageKey(null)).toBeNull();
  });
});

describe("mapProfileToVM", () => {
  it("maps the widened profile surface into feature view models", () => {
    const vm = mapProfileToVM(PROFILE_RESPONSE, TRENDS_RESPONSE, DASHBOARD_RESPONSE);

    expect(vm.school.name).toBe("Camden Bridge Primary School");
    expect(vm.overviewText).toMatch(/open academy in Camden/i);
    expect(vm.analyst.text).toMatch(/more stability than volatility/i);
    expect(vm.demographics?.coverage.fsm6Supported).toBe(true);
    expect(vm.demographics?.sendPrimaryNeeds[0]?.label).toBe("Autistic spectrum disorder");
    expect(vm.attendance?.overallAttendancePct).toBe(94.7);
    expect(vm.behaviour?.suspensionsRate).toBe(0.9);
    expect(vm.workforce?.pupilTeacherRatio).toBe(16.7);
    expect(vm.leadership?.headteacherName).toBe("A. Smith");
    expect(vm.ofsted?.providerPageUrl).toBe("https://reports.ofsted.gov.uk/provider/21/100001");
    expect(vm.neighbourhood.areaContext?.housePrices?.areaName).toBe("Camden");
    expect(vm.neighbourhood.areaContext?.crime?.annualIncidentsPer1000).toHaveLength(3);
    expect(vm.benchmarkDashboard?.sections).toHaveLength(6);
  });

  it("keeps unsupported source-limited metrics explicit", () => {
    const vm = mapProfileToVM(PROFILE_RESPONSE, TRENDS_RESPONSE, DASHBOARD_RESPONSE);
    const labels = vm.unsupportedMetrics.map((metric) => metric.label);

    expect(labels).toContain("Pupil mobility / turnover");
    expect(labels).toContain("Top non-English languages");
    expect(labels).not.toContain("FSM6");
  });

  it("maps new completeness sections and trend section completeness", () => {
    const vm = mapProfileToVM(PROFILE_RESPONSE, TRENDS_RESPONSE, DASHBOARD_RESPONSE);

    expect(vm.completeness.attendance.status).toBe("available");
    expect(vm.completeness.workforce.messageKey).toBe("partialMetricCoverage");
    expect(vm.completeness.areaHousePrices.status).toBe("available");
    expect(vm.trends?.sectionCompleteness.behaviour.status).toBe("available");
  });

  it("handles missing optional trend and dashboard payloads", () => {
    const vm = mapProfileToVM(PROFILE_RESPONSE, null, null);

    expect(vm.trends).toBeNull();
    expect(vm.benchmarkDashboard?.sections[0]?.metrics[0]?.trendPoints).toEqual([]);
    expect(vm.completeness.trends.status).toBe("unavailable");
  });

  it("maps locked analyst and neighbourhood previews without leaking premium data", () => {
    const lockedProfile = structuredClone(PROFILE_RESPONSE);
    lockedProfile.analyst = {
      access: {
        state: "locked",
        capability_key: "premium_ai_analyst",
        reason_code: "premium_capability_missing",
        product_codes: ["premium_launch"],
        requires_auth: false,
        requires_purchase: true,
        school_name: "Camden Bridge Primary School",
      },
      text: null,
      teaser_text: "The published profile points to a school with more stability than volatility.",
      disclaimer: PROFILE_RESPONSE.analyst.disclaimer,
    };
    lockedProfile.neighbourhood = {
      access: {
        state: "locked",
        capability_key: "premium_neighbourhood",
        reason_code: "premium_capability_missing",
        product_codes: ["premium_launch"],
        requires_auth: false,
        requires_purchase: true,
        school_name: "Camden Bridge Primary School",
      },
      area_context: null,
      teaser_text: "Premium neighbourhood context is available for Camden Bridge Primary School.",
    };

    const vm = mapProfileToVM(lockedProfile, TRENDS_RESPONSE, DASHBOARD_RESPONSE);

    expect(vm.analyst.access.state).toBe("locked");
    expect(vm.analyst.text).toBeNull();
    expect(vm.analyst.teaserText).toMatch(/more stability than volatility/i);
    expect(vm.neighbourhood.access.state).toBe("locked");
    expect(vm.neighbourhood.areaContext).toBeNull();
  });
});
