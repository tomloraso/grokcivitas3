import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { runA11yAudit } from "../../test/accessibility";
import { renderWithProviders } from "../../test/render";
import { MetricGrid } from "./MetricGrid";
import { MetricUnavailable } from "./MetricUnavailable";
import { RatingBadge } from "./RatingBadge";
import { Sparkline } from "./Sparkline";
import { StatCard } from "./StatCard";
import { TrendIndicator } from "./TrendIndicator";

/* ================================================================== */
/* StatCard                                                            */
/* ================================================================== */

describe("StatCard", () => {
  it("renders label and value", () => {
    renderWithProviders(<StatCard label="FSM Eligibility" value="32.4%" />);
    expect(screen.getByText("FSM Eligibility")).toBeInTheDocument();
    expect(screen.getByText("32.4%")).toBeInTheDocument();
  });

  it("renders optional footer content", () => {
    renderWithProviders(
      <StatCard
        label="SEN Support"
        value="18.1%"
        footer={<span data-testid="footer-content">trend delta</span>}
      />
    );
    expect(screen.getByTestId("footer-content")).toBeInTheDocument();
  });

  it("renders optional icon", () => {
    renderWithProviders(
      <StatCard
        label="EAL"
        value="42%"
        icon={<span data-testid="stat-icon">icon</span>}
      />
    );
    expect(screen.getByTestId("stat-icon")).toBeInTheDocument();
  });

  it("passes accessibility smoke", async () => {
    const { container } = renderWithProviders(
      <StatCard label="Metric" value="100" />
    );
    const results = await runA11yAudit(container);
    expect(results).toHaveNoViolations();
  });
});

/* ================================================================== */
/* TrendIndicator                                                      */
/* ================================================================== */

describe("TrendIndicator", () => {
  it("renders positive delta with up direction", () => {
    renderWithProviders(<TrendIndicator delta={2.3} />);
    const el = screen.getByLabelText("Trending up: +2.3%");
    expect(el).toBeInTheDocument();
  });

  it("renders negative delta with down direction", () => {
    renderWithProviders(<TrendIndicator delta={-1.5} />);
    const el = screen.getByLabelText("Trending down: -1.5%");
    expect(el).toBeInTheDocument();
  });

  it("renders zero delta with flat direction", () => {
    renderWithProviders(<TrendIndicator delta={0} />);
    const el = screen.getByLabelText("No change: 0.0%");
    expect(el).toBeInTheDocument();
  });

  it("respects explicit direction override", () => {
    renderWithProviders(<TrendIndicator delta={0} direction="up" />);
    expect(screen.getByLabelText("Trending up: 0.0%")).toBeInTheDocument();
  });

  it("renders non-percentage format", () => {
    renderWithProviders(<TrendIndicator delta={5} asPercentage={false} />);
    expect(screen.getByLabelText("Trending up: +5")).toBeInTheDocument();
  });

  it("passes accessibility smoke", async () => {
    const { container } = renderWithProviders(
      <div>
        <TrendIndicator delta={1.2} />
        <TrendIndicator delta={-0.8} />
        <TrendIndicator delta={0} />
      </div>
    );
    const results = await runA11yAudit(container);
    expect(results).toHaveNoViolations();
  });
});

/* ================================================================== */
/* RatingBadge                                                         */
/* ================================================================== */

describe("RatingBadge", () => {
  it("maps rating code 1 to Outstanding", () => {
    renderWithProviders(<RatingBadge ratingCode="1" />);
    expect(screen.getByText("Outstanding")).toBeInTheDocument();
    expect(screen.getByLabelText("Ofsted rating: Outstanding")).toBeInTheDocument();
  });

  it("maps rating code 2 to Good", () => {
    renderWithProviders(<RatingBadge ratingCode="2" />);
    expect(screen.getByText("Good")).toBeInTheDocument();
  });

  it("maps rating code 3 to Requires Improvement", () => {
    renderWithProviders(<RatingBadge ratingCode="3" />);
    expect(screen.getByText("Requires Improvement")).toBeInTheDocument();
  });

  it("maps rating code 4 to Inadequate", () => {
    renderWithProviders(<RatingBadge ratingCode="4" />);
    expect(screen.getByText("Inadequate")).toBeInTheDocument();
  });

  it("handles null rating code as Not Rated", () => {
    renderWithProviders(<RatingBadge ratingCode={null} />);
    expect(screen.getByText("Not Rated")).toBeInTheDocument();
  });

  it("handles unknown rating code as Not Rated", () => {
    renderWithProviders(<RatingBadge ratingCode="99" />);
    expect(screen.getByText("Not Rated")).toBeInTheDocument();
  });

  it("shows Ungraded for ungraded inspection with no code", () => {
    renderWithProviders(<RatingBadge ratingCode={null} isUngraded />);
    expect(screen.getByText("Ungraded")).toBeInTheDocument();
  });

  it("accepts label override", () => {
    renderWithProviders(<RatingBadge ratingCode="1" label="Custom Label" />);
    expect(screen.getByText("Custom Label")).toBeInTheDocument();
    expect(screen.getByLabelText("Ofsted rating: Custom Label")).toBeInTheDocument();
  });

  it("passes accessibility smoke", async () => {
    const { container } = renderWithProviders(
      <div>
        <RatingBadge ratingCode="1" />
        <RatingBadge ratingCode="4" />
        <RatingBadge ratingCode={null} />
      </div>
    );
    const results = await runA11yAudit(container);
    expect(results).toHaveNoViolations();
  });
});

/* ================================================================== */
/* Sparkline                                                           */
/* ================================================================== */

describe("Sparkline", () => {
  it("renders SVG with multi-point data", () => {
    const { container } = renderWithProviders(
      <Sparkline data={[10, 20, 15, 25, 22]} />
    );
    const svg = container.querySelector("svg");
    expect(svg).toBeInTheDocument();
    expect(svg?.querySelector("polyline")).toBeInTheDocument();
  });

  it("renders single-point data as a circle", () => {
    const { container } = renderWithProviders(<Sparkline data={[42]} />);
    const svg = container.querySelector("svg");
    expect(svg).toBeInTheDocument();
    expect(svg?.querySelector("circle")).toBeInTheDocument();
    expect(svg?.querySelector("polyline")).not.toBeInTheDocument();
  });

  it("renders empty data gracefully", () => {
    const { container } = renderWithProviders(<Sparkline data={[]} />);
    const svg = container.querySelector("svg");
    expect(svg).toBeInTheDocument();
    expect(svg?.querySelector("polyline")).not.toBeInTheDocument();
    expect(svg?.querySelector("circle")).not.toBeInTheDocument();
  });

  it("has accessible aria-label", () => {
    renderWithProviders(
      <Sparkline data={[10, 20, 15]} aria-label="SEN trend" />
    );
    expect(screen.getByLabelText("SEN trend")).toBeInTheDocument();
  });

  it("generates default aria-label from data", () => {
    renderWithProviders(<Sparkline data={[5, 10, 15]} />);
    expect(screen.getByLabelText("Trend: 5, 10, 15")).toBeInTheDocument();
  });

  it("renders fill gradient when showFill is true", () => {
    const { container } = renderWithProviders(
      <Sparkline data={[10, 20, 15]} showFill />
    );
    expect(container.querySelector("polygon")).toBeInTheDocument();
    expect(container.querySelector("linearGradient")).toBeInTheDocument();
  });

  it("does not render fill when showFill is false", () => {
    const { container } = renderWithProviders(
      <Sparkline data={[10, 20, 15]} showFill={false} />
    );
    expect(container.querySelector("polygon")).not.toBeInTheDocument();
  });

  it("passes accessibility smoke", async () => {
    const { container } = renderWithProviders(
      <Sparkline data={[10, 20, 15, 25]} aria-label="Trend line" />
    );
    const results = await runA11yAudit(container);
    expect(results).toHaveNoViolations();
  });
});

/* ================================================================== */
/* MetricGrid                                                          */
/* ================================================================== */

describe("MetricGrid", () => {
  it("renders children in a grid", () => {
    renderWithProviders(
      <MetricGrid>
        <div>Card 1</div>
        <div>Card 2</div>
        <div>Card 3</div>
      </MetricGrid>
    );
    expect(screen.getByText("Card 1")).toBeInTheDocument();
    expect(screen.getByText("Card 2")).toBeInTheDocument();
    expect(screen.getByText("Card 3")).toBeInTheDocument();
  });

  it("applies responsive grid classes", () => {
    const { container } = renderWithProviders(
      <MetricGrid columns={4}>
        <div>A</div>
      </MetricGrid>
    );
    const grid = container.firstElementChild;
    expect(grid?.className).toContain("grid");
    expect(grid?.className).toContain("lg:grid-cols-4");
  });

  it("defaults to 3 columns", () => {
    const { container } = renderWithProviders(
      <MetricGrid>
        <div>X</div>
      </MetricGrid>
    );
    const grid = container.firstElementChild;
    expect(grid?.className).toContain("lg:grid-cols-3");
  });
});

/* ================================================================== */
/* MetricUnavailable                                                   */
/* ================================================================== */

describe("MetricUnavailable", () => {
  it("renders default message", () => {
    renderWithProviders(<MetricUnavailable />);
    expect(screen.getByText("Data not available")).toBeInTheDocument();
  });

  it("renders metric-specific message", () => {
    renderWithProviders(<MetricUnavailable metricLabel="Ethnicity breakdown" />);
    expect(
      screen.getByText("Ethnicity breakdown data is not available")
    ).toBeInTheDocument();
  });

  it("has accessible status role and label", () => {
    renderWithProviders(<MetricUnavailable metricLabel="FSM" />);
    const el = screen.getByRole("status");
    expect(el).toHaveAttribute("aria-label", "FSM data is not available");
  });

  it("passes accessibility smoke", async () => {
    const { container } = renderWithProviders(
      <MetricUnavailable metricLabel="Test metric" />
    );
    const results = await runA11yAudit(container);
    expect(results).toHaveNoViolations();
  });
});

/* ================================================================== */
/* Composition: StatCard + TrendIndicator + Sparkline                  */
/* ================================================================== */

describe("Composition", () => {
  it("renders StatCard with TrendIndicator footer", () => {
    renderWithProviders(
      <StatCard
        label="Disadvantaged"
        value="28.5%"
        footer={<TrendIndicator delta={-1.2} />}
      />
    );
    expect(screen.getByText("28.5%")).toBeInTheDocument();
    expect(screen.getByLabelText("Trending down: -1.2%")).toBeInTheDocument();
  });

  it("renders MetricGrid with StatCards", () => {
    renderWithProviders(
      <MetricGrid columns={2}>
        <StatCard label="SEN" value="12%" />
        <StatCard label="EHCP" value="3.4%" />
      </MetricGrid>
    );
    expect(screen.getByText("SEN")).toBeInTheDocument();
    expect(screen.getByText("EHCP")).toBeInTheDocument();
  });

  it("passes accessibility smoke for composed layout", async () => {
    const { container } = renderWithProviders(
      <MetricGrid>
        <StatCard
          label="FSM"
          value="22.1%"
          footer={<TrendIndicator delta={0.5} />}
        />
        <StatCard
          label="EAL"
          value="41%"
          footer={<Sparkline data={[38, 39, 40, 41]} aria-label="EAL trend" />}
        />
        <MetricUnavailable metricLabel="Ethnicity" />
      </MetricGrid>
    );
    const results = await runA11yAudit(container);
    expect(results).toHaveNoViolations();
  });
});
