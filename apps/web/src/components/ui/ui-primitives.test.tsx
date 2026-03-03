import { fireEvent, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { runA11yAudit } from "../../test/accessibility";
import { renderWithProviders } from "../../test/render";
import { Button } from "./Button";
import { Card, Panel } from "./Card";
import { EmptyState } from "./EmptyState";
import { ErrorState } from "./ErrorState";
import { Field } from "./Field";
import { LoadingSkeleton } from "./LoadingSkeleton";
import { ResultCard } from "./ResultCard";
import { Select } from "./Select";
import { TextInput } from "./TextInput";

describe("UI primitives", () => {
  it("renders a labeled field with text input and helper text", () => {
    renderWithProviders(
      <Field label="Postcode" htmlFor="postcode-input" helperText="Use full postcode">
        <TextInput id="postcode-input" aria-label="Postcode input" />
      </Field>
    );

    expect(screen.getByLabelText("Postcode input")).toBeInTheDocument();
    expect(screen.getByText("Use full postcode")).toBeInTheDocument();
  });

  it("supports keyboard interaction in radix select", async () => {
    const user = userEvent.setup();
    const onValueChange = vi.fn();

    renderWithProviders(
      <Select
        id="radius"
        ariaLabel="Radius"
        value="5"
        onValueChange={onValueChange}
        options={[
          { value: "1", label: "1 mile" },
          { value: "5", label: "5 miles" },
          { value: "10", label: "10 miles" }
        ]}
      />
    );

    const trigger = screen.getByLabelText("Radius");
    trigger.focus();
    fireEvent.keyDown(trigger, { key: "Enter" });
    await user.click(screen.getByRole("option", { name: "10 miles" }));

    expect(onValueChange).toHaveBeenCalledWith("10");
  });

  it("renders shared loading, empty, and error states", async () => {
    renderWithProviders(
      <div>
        <LoadingSkeleton lines={2} />
        <EmptyState title="Nothing here" description="Try changing filters." />
        <ErrorState
          title="Request failed"
          description="Something went wrong."
          onRetry={() => undefined}
        />
      </div>
    );

    expect(screen.getByRole("status")).toHaveAttribute("aria-label", "Loading content");
    expect(screen.getByText("Nothing here")).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent("Request failed");
    expect(screen.getByRole("button", { name: "Try again" })).toBeInTheDocument();
  });

  it("renders shaped result-card skeleton variant", () => {
    renderWithProviders(<LoadingSkeleton variant="result-card" count={3} />);

    expect(screen.getByRole("status")).toHaveAttribute("aria-label", "Loading results");
  });

  it("renders empty state with icon slot", () => {
    renderWithProviders(
      <EmptyState
        title="No results"
        description="Try again."
        icon={<span data-testid="empty-icon">icon</span>}
      />
    );

    expect(screen.getByTestId("empty-icon")).toBeInTheDocument();
    expect(screen.getByText("No results")).toBeInTheDocument();
  });

  it("renders card wrappers and result shell content", () => {
    renderWithProviders(
      <div>
        <Card>Card body</Card>
        <Panel>Panel body</Panel>
        <ResultCard
          name="Camden Bridge Primary"
          type="Community school"
          phase="Primary"
          postcode="NW1 8NH"
          distanceMiles={0.52}
        />
      </div>
    );

    expect(screen.getByText("Card body")).toBeInTheDocument();
    expect(screen.getByText("Panel body")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Camden Bridge Primary" })).toBeInTheDocument();
    expect(screen.getByText("0.52 mi")).toBeInTheDocument();
  });

  it("keeps primary button at touch-friendly height", () => {
    renderWithProviders(<Button type="button">Run</Button>);

    expect(screen.getByRole("button", { name: "Run" }).className).toContain("h-11");
  });

  it("passes accessibility smoke checks", async () => {
    const { container } = renderWithProviders(
      <div>
        <Field label="Example field" htmlFor="example-input">
          <TextInput id="example-input" aria-label="Example input" />
        </Field>
        <Button type="button">Save</Button>
      </div>
    );

    const results = await runA11yAudit(container);
    expect(results).toHaveNoViolations();
  });
});
