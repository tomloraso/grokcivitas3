import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { ThemeModeToggle } from "./ThemeModeToggle";
import { renderWithProviders } from "../../test/render";
import { runA11yAudit } from "../../test/accessibility";

describe("ThemeModeToggle", () => {
  it("renders a button with the correct aria-label for each mode", () => {
    const { rerender } = renderWithProviders(
      <ThemeModeToggle mode="system" onCycle={() => undefined} />,
    );
    expect(screen.getByRole("button", { name: "System theme" })).toBeInTheDocument();

    rerender(<ThemeModeToggle mode="light" onCycle={() => undefined} />);
    expect(screen.getByRole("button", { name: "Light theme" })).toBeInTheDocument();

    rerender(<ThemeModeToggle mode="dark" onCycle={() => undefined} />);
    expect(screen.getByRole("button", { name: "Dark theme" })).toBeInTheDocument();
  });

  it("calls onCycle when clicked", async () => {
    const user = userEvent.setup();
    let cycled = false;
    renderWithProviders(
      <ThemeModeToggle mode="dark" onCycle={() => { cycled = true; }} />,
    );

    await user.click(screen.getByRole("button", { name: "Dark theme" }));
    expect(cycled).toBe(true);
  });

  it("passes accessibility smoke check", async () => {
    const { container } = renderWithProviders(
      <ThemeModeToggle mode="system" onCycle={() => undefined} />,
    );
    const results = await runA11yAudit(container);
    expect(results).toHaveNoViolations();
  });
});
