import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { FilterChips } from "./FilterChips";
import type { Facet } from "../hooks/useResultFilters";

const PHASES: Facet[] = [
  { label: "Primary", count: 12, selected: false },
  { label: "Secondary", count: 8, selected: false },
  { label: "All through", count: 3, selected: false },
];

function renderChips(overrides: Partial<Parameters<typeof FilterChips>[0]> = {}) {
  const props = {
    phases: PHASES,
    hasActiveFilters: false,
    hiddenCount: 0,
    onTogglePhase: vi.fn(),
    onClear: vi.fn(),
    ...overrides,
  };
  return { ...render(<FilterChips {...props} />), props };
}

describe("FilterChips", () => {
  it("renders phase chips", () => {
    renderChips();

    expect(screen.getByText("Primary")).toBeInTheDocument();
    expect(screen.getByText("Secondary")).toBeInTheDocument();
    expect(screen.getByText("All through")).toBeInTheDocument();
  });

  it("shows counts on each chip", () => {
    renderChips();

    expect(screen.getByText("12")).toBeInTheDocument();
    expect(screen.getByText("8")).toBeInTheDocument();
  });

  it("calls onTogglePhase when a chip is clicked", () => {
    const { props } = renderChips();

    fireEvent.click(screen.getByText("Primary"));
    expect(props.onTogglePhase).toHaveBeenCalledWith("Primary");
  });

  it("marks selected chips with aria-selected", () => {
    const selectedPhases = PHASES.map((p) =>
      p.label === "Primary" ? { ...p, selected: true } : p
    );

    renderChips({ phases: selectedPhases });

    const primaryChip = screen.getByRole("option", { name: /Primary/ });
    expect(primaryChip).toHaveAttribute("aria-selected", "true");
  });

  it("shows clear button and hidden count when filters active", () => {
    const { props } = renderChips({ hasActiveFilters: true, hiddenCount: 7 });

    expect(screen.getByText("7 schools hidden")).toBeInTheDocument();
    const clearBtn = screen.getByRole("button", { name: /Clear/ });
    fireEvent.click(clearBtn);
    expect(props.onClear).toHaveBeenCalled();
  });

  it("hides clear button when no filters active", () => {
    renderChips({ hasActiveFilters: false });

    expect(screen.queryByText(/hidden/)).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Clear/ })).not.toBeInTheDocument();
  });

  it("returns null when only one phase (nothing to filter)", () => {
    const singlePhase = [{ label: "Primary", count: 10, selected: false }];
    const { container } = render(
      <FilterChips
        phases={singlePhase}
        hasActiveFilters={false}
        hiddenCount={0}
        onTogglePhase={vi.fn()}
        onClear={vi.fn()}
      />
    );

    expect(container.firstChild).toBeNull();
  });

  it("returns null when no phases", () => {
    const { container } = render(
      <FilterChips
        phases={[]}
        hasActiveFilters={false}
        hiddenCount={0}
        onTogglePhase={vi.fn()}
        onClear={vi.fn()}
      />
    );

    expect(container.firstChild).toBeNull();
  });

  it("has accessible group role", () => {
    renderChips();

    expect(screen.getByRole("group", { name: "Filter results" })).toBeInTheDocument();
  });
});
