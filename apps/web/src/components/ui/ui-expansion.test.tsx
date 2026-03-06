import { act, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { runA11yAudit } from "../../test/accessibility";
import { renderWithProviders } from "../../test/render";
import { Badge } from "./Badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./Tabs";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "./Tooltip";
import { ToastProvider } from "./Toast";
import { useToast } from "./ToastContext";

/* ================================================================== */
/* Badge                                                               */
/* ================================================================== */

describe("Badge", () => {
  it("renders with default variant", () => {
    renderWithProviders(<Badge>Default</Badge>);
    expect(screen.getByText("Default")).toBeInTheDocument();
  });

  it.each(["success", "warning", "danger", "info", "outline"] as const)(
    "renders %s variant without crashing",
    (variant) => {
      renderWithProviders(<Badge variant={variant}>{variant}</Badge>);
      expect(screen.getByText(variant)).toBeInTheDocument();
    }
  );

  it("applies custom className", () => {
    renderWithProviders(<Badge className="custom-class">Test</Badge>);
    expect(screen.getByText("Test")).toHaveClass("custom-class");
  });

  it("passes accessibility smoke", async () => {
    const { container } = renderWithProviders(
      <div>
        <Badge variant="default">Outstanding</Badge>
        <Badge variant="success">Good</Badge>
        <Badge variant="danger">Inadequate</Badge>
      </div>
    );
    const results = await runA11yAudit(container);
    expect(results).toHaveNoViolations();
  });
});

/* ================================================================== */
/* Tabs                                                                */
/* ================================================================== */

describe("Tabs", () => {
  function TabsExample() {
    return (
      <Tabs defaultValue="demographics">
        <TabsList aria-label="Profile sections">
          <TabsTrigger value="demographics">Demographics</TabsTrigger>
          <TabsTrigger value="ofsted">Ofsted</TabsTrigger>
          <TabsTrigger value="trends">Trends</TabsTrigger>
        </TabsList>
        <TabsContent value="demographics">Demographics content</TabsContent>
        <TabsContent value="ofsted">Ofsted content</TabsContent>
        <TabsContent value="trends">Trends content</TabsContent>
      </Tabs>
    );
  }

  it("renders the default active tab content", () => {
    renderWithProviders(<TabsExample />);
    expect(screen.getByText("Demographics content")).toBeInTheDocument();
  });

  it("switches content on click", async () => {
    const user = userEvent.setup();
    renderWithProviders(<TabsExample />);

    await user.click(screen.getByRole("tab", { name: "Ofsted" }));
    expect(screen.getByText("Ofsted content")).toBeInTheDocument();
  });

  it("supports keyboard navigation between tabs", async () => {
    const user = userEvent.setup();
    renderWithProviders(<TabsExample />);

    // Move focus to the first tab through user interaction to keep updates in act().
    await user.tab();
    expect(screen.getByRole("tab", { name: "Demographics" })).toHaveFocus();

    // Arrow right moves to next tab
    await user.keyboard("{ArrowRight}");
    await waitFor(() =>
      expect(screen.getByRole("tab", { name: "Ofsted" })).toHaveFocus()
    );

    await user.keyboard("{ArrowRight}");
    await waitFor(() =>
      expect(screen.getByRole("tab", { name: "Trends" })).toHaveFocus()
    );
  });

  it("maintains proper ARIA roles", () => {
    renderWithProviders(<TabsExample />);

    expect(screen.getByRole("tablist")).toBeInTheDocument();
    expect(screen.getAllByRole("tab")).toHaveLength(3);
    expect(screen.getByRole("tabpanel")).toBeInTheDocument();
  });

  it("passes accessibility smoke", async () => {
    const { container } = renderWithProviders(<TabsExample />);
    const results = await runA11yAudit(container);
    expect(results).toHaveNoViolations();
  });
});

/* ================================================================== */
/* Tooltip                                                             */
/* ================================================================== */

describe("Tooltip", () => {
  function TooltipExample() {
    return (
      <TooltipProvider delayDuration={0}>
        <Tooltip>
          <TooltipTrigger asChild>
            <button type="button">Hover me</button>
          </TooltipTrigger>
          <TooltipContent>Helpful context</TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  it("renders the trigger", () => {
    renderWithProviders(<TooltipExample />);
    expect(screen.getByRole("button", { name: "Hover me" })).toBeInTheDocument();
  });

  it("shows tooltip content on focus", async () => {
    const user = userEvent.setup();
    renderWithProviders(<TooltipExample />);

    await user.tab();
    expect(screen.getByRole("button", { name: "Hover me" })).toHaveFocus();
    expect(await screen.findByRole("tooltip")).toHaveTextContent("Helpful context");
  });

  it("passes accessibility smoke", async () => {
    const { container } = renderWithProviders(<TooltipExample />);
    const results = await runA11yAudit(container);
    expect(results).toHaveNoViolations();
  });
});

/* ================================================================== */
/* Toast                                                               */
/* ================================================================== */

describe("Toast", () => {
  function ToastTrigger() {
    const { toast } = useToast();
    return (
      <button
        type="button"
        onClick={() => toast({ title: "Saved", description: "Changes applied." })}
      >
        Show toast
      </button>
    );
  }

  function ToastExample() {
    return (
      <ToastProvider>
        <ToastTrigger />
      </ToastProvider>
    );
  }

  it("renders toast on trigger", async () => {
    const user = userEvent.setup();
    renderWithProviders(<ToastExample />);

    await user.click(screen.getByRole("button", { name: "Show toast" }));

    expect(await screen.findByText("Saved")).toBeInTheDocument();
    expect(screen.getByText("Changes applied.")).toBeInTheDocument();
  });

  it("renders close button with accessible label", async () => {
    const user = userEvent.setup();
    renderWithProviders(<ToastExample />);

    await user.click(screen.getByRole("button", { name: "Show toast" }));

    const closeButton = await screen.findByLabelText("Close notification");
    expect(closeButton).toBeInTheDocument();
  });

  it("passes accessibility smoke", async () => {
    const user = userEvent.setup();
    const { container } = renderWithProviders(<ToastExample />);

    await act(async () => {
      await user.click(screen.getByRole("button", { name: "Show toast" }));
      await new Promise((resolve) => window.setTimeout(resolve, 1100));
    });

    expect(screen.getByText("Saved")).toBeInTheDocument();
    expect(screen.getByLabelText("Close notification")).toBeInTheDocument();

    const results = await runA11yAudit(container);
    expect(results).toHaveNoViolations();
  });
});
