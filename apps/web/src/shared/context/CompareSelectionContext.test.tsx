import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";

import {
  CompareSelectionProvider,
  useCompareSelection
} from "./CompareSelectionContext";

const STORAGE_KEY = "civitas.compare.selection";

function Probe(): JSX.Element {
  const { addSchool, count, isHydrated, items } = useCompareSelection();

  return (
    <div>
      <p>{isHydrated ? "hydrated" : "hydrating"}</p>
      <p>{`count:${count}`}</p>
      <button
        type="button"
        onClick={() =>
          addSchool({
            urn: "200002",
            name: "Secondary Example",
            phase: "Secondary",
            type: "Academy sponsor led",
            postcode: "SW1A 2BB",
            source: "profile"
          })
        }
      >
        Add second
      </button>
      <ul>
        {items.map((item) => (
          <li key={item.urn}>{item.urn}</li>
        ))}
      </ul>
    </div>
  );
}

describe("CompareSelectionProvider", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("hydrates persisted selections before writing back to local storage", async () => {
    window.localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify([
        {
          urn: "100001",
          name: "Primary Example",
          phase: "Primary",
          type: "Community school",
          postcode: "SW1A 1AA",
          source: "search"
        }
      ])
    );

    const user = userEvent.setup();

    render(
      <CompareSelectionProvider>
        <Probe />
      </CompareSelectionProvider>
    );

    await screen.findByText("hydrated");
    expect(screen.getByText("count:1")).toBeInTheDocument();
    expect(screen.getByText("100001")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Add second" }));

    await waitFor(() => {
      const stored = window.localStorage.getItem(STORAGE_KEY);
      expect(stored).not.toBeNull();
      const parsed = JSON.parse(stored ?? "[]") as Array<{ urn: string }>;
      expect(parsed.map((item) => item.urn)).toEqual(["100001", "200002"]);
    });
  });
});
