import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";

import { ToastProvider } from "../../../components/ui/Toast";
import { CompareSelectionProvider } from "../../../shared/context/CompareSelectionContext";
import { ResultsOverlay } from "./ResultsOverlay";
import type { PostcodeSearchResult } from "../types";

function setMobile(mobile: boolean): void {
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: vi.fn().mockImplementation((query: string) => ({
      media: query,
      matches: mobile,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn()
    }))
  });
}

const RESULT: PostcodeSearchResult = {
  mode: "postcode",
  query: {
    postcode: "SW1A 1AA",
    radius_miles: 5,
    phases: ["primary"],
    sort: "ofsted"
  },
  center: {
    lat: 51.501009,
    lng: -0.141588
  },
  count: 2,
  schools: [
    {
      urn: "100001",
      name: "Camden Bridge Primary School",
      type: "Community school",
      phase: "Primary",
      postcode: "NW1 8NH",
      lat: 51.5424,
      lng: -0.1418,
      distance_miles: 0.52,
      pupil_count: 420,
      latest_ofsted: {
        label: "Good",
        sort_rank: 2,
        availability: "published"
      },
      academic_metric: {
        metric_key: "ks2_combined_expected_pct",
        label: "KS2 expected standard",
        display_value: "67%",
        sort_value: 67,
        availability: "published"
      }
    },
    {
      urn: "100002",
      name: "Riverbank Primary School",
      type: "Academy converter",
      phase: "Primary",
      postcode: "NW1 8NJ",
      lat: 51.541,
      lng: -0.14,
      distance_miles: 0.73,
      pupil_count: null,
      latest_ofsted: {
        label: null,
        sort_rank: null,
        availability: "not_published"
      },
      academic_metric: {
        metric_key: "ks2_combined_expected_pct",
        label: "KS2 expected standard",
        display_value: null,
        sort_value: null,
        availability: "not_published"
      }
    }
  ]
};

function renderOverlay() {
  return render(
    <MemoryRouter>
      <CompareSelectionProvider>
        <ToastProvider>
          <ResultsOverlay
            open
            status="success"
            result={RESULT}
            errorMessage={null}
            phases={["primary"]}
            sort="ofsted"
            onClose={vi.fn()}
            onRetry={vi.fn(async () => undefined)}
            onPhasesChange={vi.fn()}
            onSortChange={vi.fn()}
          />
        </ToastProvider>
      </CompareSelectionProvider>
    </MemoryRouter>
  );
}

afterEach(() => {
  localStorage.clear();
  setMobile(false);
});

describe("ResultsOverlay", () => {
  it("renders the desktop table with ranking explanation", () => {
    renderOverlay();

    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByText("Results for SW1A 1AA")).toBeInTheDocument();
    expect(
      screen.getByText("Sorted by latest Ofsted judgement, then distance.")
    ).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "School" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Academic" })).toBeInTheDocument();
    expect(screen.getByText("Camden Bridge Primary School")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Academic" })).not.toBeInTheDocument();
  });

  it("renders mobile cards and supports compare interaction", async () => {
    setMobile(true);
    const user = userEvent.setup();
    renderOverlay();

    expect(screen.queryByRole("table")).not.toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: "Add to compare" }).length).toBeGreaterThan(0);

    await user.click(screen.getAllByRole("button", { name: "Add to compare" })[0]);

    expect(screen.getByRole("button", { name: "Remove" })).toBeInTheDocument();
  });
});
