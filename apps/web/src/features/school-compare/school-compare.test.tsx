import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { getSchoolCompare } from "../../api/client";
import { ThemeProvider } from "../../app/providers/ThemeProvider";
import { AuthProvider } from "../auth/AuthProvider";
import { ANONYMOUS_SESSION } from "../auth/types";
import {
  CompareSelectionProvider,
  type CompareSelectionItem,
} from "../../shared/context/CompareSelectionContext";
import { SchoolCompareFeature } from "./SchoolCompareFeature";
import { COMPARE_RESPONSE } from "./testData";

vi.mock("../../api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../../api/client")>();
  return {
    ...actual,
    getSchoolCompare: vi.fn(),
  };
});

const compareMock = vi.mocked(getSchoolCompare);
const STORAGE_KEY = "civitas.compare.selection";

function buildSelectionItem(
  overrides: Partial<CompareSelectionItem> & Pick<CompareSelectionItem, "urn" | "name">
): CompareSelectionItem {
  return {
    urn: overrides.urn,
    name: overrides.name,
    phase: overrides.phase ?? "Primary",
    type: overrides.type ?? "Community school",
    postcode: overrides.postcode ?? "SW1A 1AA",
    distanceMiles: overrides.distanceMiles,
    source: overrides.source ?? "search",
  };
}

function renderCompare(
  initialEntry: string,
  initialItems: CompareSelectionItem[] = []
) {
  const router = createMemoryRouter(
    [
      {
        path: "/",
        element: <div>Search page</div>,
      },
      {
        path: "/compare",
        element: <SchoolCompareFeature />,
      },
      {
        path: "/schools/:urn",
        element: <div data-testid="profile-page">Profile page</div>,
      },
    ],
    { initialEntries: [initialEntry] }
  );

  const result = render(
    <ThemeProvider>
      <AuthProvider autoLoad={false} initialSession={ANONYMOUS_SESSION}>
        <CompareSelectionProvider initialItems={initialItems}>
          <RouterProvider router={router} />
        </CompareSelectionProvider>
      </AuthProvider>
    </ThemeProvider>
  );

  return { ...result, router };
}

describe("SchoolCompareFeature", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    window.localStorage.clear();
    compareMock.mockResolvedValue(COMPARE_RESPONSE);
  });

  it("renders an underfilled state without calling the compare API", async () => {
    renderCompare("/compare?urns=100001", [
      buildSelectionItem({
        urn: "100001",
        name: "Primary Example",
        distanceMiles: 0.84,
      }),
    ]);

    expect(
      await screen.findByRole("heading", { name: "Add one more school to compare" })
    ).toBeInTheDocument();
    expect(screen.getAllByText("Primary Example")[0]).toBeInTheDocument();
    expect(compareMock).not.toHaveBeenCalled();
  });

  it("renders the compare matrix and falls back to underfilled after removing a school", async () => {
    const user = userEvent.setup();

    renderCompare("/compare?urns=100001,200002", [
      buildSelectionItem({
        urn: "100001",
        name: "Primary Example",
        distanceMiles: 1.23,
      }),
      buildSelectionItem({
        urn: "200002",
        name: "Secondary Example",
        phase: "Secondary",
        type: "Academy sponsor led",
        postcode: "SW1A 2BB",
      }),
    ]);

    expect(await screen.findByText("Pupil Demographics")).toBeInTheDocument();
    expect(
      screen.getAllByRole("table", { name: "School comparison table" })[0]
    ).toBeInTheDocument();
    expect(compareMock).toHaveBeenCalledWith(["100001", "200002"]);
    expect(screen.getAllByText("England 18.0% | Westminster 19.2%")[0]).toBeInTheDocument();
    expect(screen.getAllByText("— Not applicable")[0]).toBeInTheDocument();

    await user.click(
      screen.getByRole("button", { name: /Neighbourhood Context/i })
    );

    expect(
      screen.getAllByText(
        "The source currently has limited coverage for this information."
      )[0]
    ).toBeInTheDocument();

    await user.click(
      screen.getAllByRole("button", { name: "Remove Primary Example from compare" })[0]
    );

    expect(
      await screen.findByRole("heading", { name: "Add one more school to compare" })
    ).toBeInTheDocument();
    expect(screen.getAllByText("Secondary Example")[0]).toBeInTheDocument();
    expect(compareMock).toHaveBeenCalledTimes(1);
  });

  it("treats an explicit empty urns query as authoritative instead of reviving stored selection", async () => {
    renderCompare("/compare?urns=", [
      buildSelectionItem({
        urn: "100001",
        name: "Primary Example",
      }),
      buildSelectionItem({
        urn: "200002",
        name: "Secondary Example",
        phase: "Secondary",
      }),
    ]);

    expect(
      await screen.findByRole("heading", { name: "Start a compare set" })
    ).toBeInTheDocument();
    expect(compareMock).not.toHaveBeenCalled();
  });

  it("canonicalizes selection-only compare state into the shareable compare URL", async () => {
    const { router } = renderCompare("/compare", [
      buildSelectionItem({
        urn: "100001",
        name: "Primary Example",
      }),
      buildSelectionItem({
        urn: "200002",
        name: "Secondary Example",
        phase: "Secondary",
      }),
    ]);

    await waitFor(() => {
      expect(compareMock).toHaveBeenCalledWith(["100001", "200002"]);
      expect(router.state.location.pathname).toBe("/compare");
      expect(router.state.location.search).toBe("?urns=100001%2C200002");
    });
  });

  it("syncs persisted compare selection to the authoritative compare URL order", async () => {
    renderCompare("/compare?urns=200002,100001", [
      buildSelectionItem({
        urn: "100001",
        name: "Primary Example",
      }),
      buildSelectionItem({
        urn: "200002",
        name: "Secondary Example",
        phase: "Secondary",
      }),
    ]);

    await waitFor(() => {
      expect(compareMock).toHaveBeenCalledWith(["200002", "100001"]);
      const stored = window.localStorage.getItem(STORAGE_KEY);
      expect(stored).not.toBeNull();
      const parsed = JSON.parse(stored ?? "[]") as CompareSelectionItem[];
      expect(parsed.map((item) => item.urn)).toEqual(["200002", "100001"]);
    });
  });

  it("renders the locked compare paywall when the backend returns a locked response", async () => {
    const lockedResponse = structuredClone(COMPARE_RESPONSE);
    lockedResponse.access = {
      state: "locked",
      capability_key: "premium_comparison",
      reason_code: "premium_capability_missing",
      product_codes: ["premium_launch"],
      requires_auth: false,
      requires_purchase: true,
      school_name: null,
    };
    lockedResponse.sections = [];
    compareMock.mockResolvedValueOnce(lockedResponse);

    renderCompare("/compare?urns=100001,200002", [
      buildSelectionItem({
        urn: "100001",
        name: "Primary Example",
      }),
      buildSelectionItem({
        urn: "200002",
        name: "Secondary Example",
        phase: "Secondary",
      }),
    ]);

    expect(
      await screen.findByText("Compare schools side by side with Premium")
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "View Premium plans" })).toHaveAttribute(
      "href",
      "/account/upgrade?capability=premium_comparison&product=premium_launch&returnTo=%2Fcompare%3Furns%3D100001%2C200002"
    );
  });
});
