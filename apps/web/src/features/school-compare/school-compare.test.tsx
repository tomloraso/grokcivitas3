import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { getSchoolCompare } from "../../api/client";
import { ThemeProvider } from "../../app/providers/ThemeProvider";
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
      <CompareSelectionProvider initialItems={initialItems}>
        <RouterProvider router={router} />
      </CompareSelectionProvider>
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
    expect(screen.getByText("Primary Example")).toBeInTheDocument();
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

    expect(await screen.findByRole("heading", { name: "Demographics" })).toBeInTheDocument();
    expect(
      screen.getByRole("table", { name: "Demographics comparison table" })
    ).toBeInTheDocument();
    expect(compareMock).toHaveBeenCalledWith(["100001", "200002"]);
    expect(screen.getByText("England 18.0% | Westminster 19.2%")).toBeInTheDocument();
    expect(screen.getByText("Not applicable")).toBeInTheDocument();
    expect(
      screen.getAllByText(
        "The source currently has limited coverage for this information."
      )[0]
    ).toBeInTheDocument();

    await user.click(
      screen.getByRole("button", { name: "Remove Primary Example from compare" })
    );

    expect(
      await screen.findByRole("heading", { name: "Add one more school to compare" })
    ).toBeInTheDocument();
    expect(screen.getByText("Secondary Example")).toBeInTheDocument();
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
});
