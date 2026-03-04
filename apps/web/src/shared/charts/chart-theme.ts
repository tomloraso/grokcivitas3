/**
 * Chart theme configuration for Recharts.
 *
 * Maps Civitas design tokens to Recharts component props so charts
 * integrate seamlessly with the dark-first visual system.
 *
 * Usage:
 *   import { chartTheme } from "@/shared/charts/chart-theme";
 *   <LineChart ...>
 *     <CartesianGrid {...chartTheme.grid} />
 *     <Tooltip {...chartTheme.tooltip} />
 *   </LineChart>
 */

/* ------------------------------------------------------------------ */
/* Token values resolved at module scope                               */
/* ------------------------------------------------------------------ */

// These CSS custom property values are read at render-time via
// getComputedStyle in components. For Recharts config objects we
// provide the raw token references as CSS variable strings that
// Recharts inline-styles will resolve.

const tokens = {
  bgCanvas: "var(--color-bg-canvas)",
  bgSurface: "var(--color-bg-surface)",
  bgElevated: "var(--color-bg-elevated)",
  textPrimary: "var(--color-text-primary)",
  textSecondary: "var(--color-text-secondary)",
  textDisabled: "var(--color-text-disabled)",
  borderDefault: "var(--color-border-default)",
  borderSubtle: "var(--color-border-subtle)",
  brand: "var(--color-action-primary)",
  brandHover: "var(--color-action-primary-hover)",
  accent: "var(--color-action-secondary)",
  success: "var(--color-state-success)",
  warning: "var(--color-state-warning)",
  danger: "var(--color-state-danger)",
  info: "var(--color-state-info)"
} as const;

/* ------------------------------------------------------------------ */
/* Series colour palette                                               */
/* ------------------------------------------------------------------ */

/**
 * Ordered palette for multi-series charts.
 * First colour is the primary brand accent; subsequent colours provide
 * sufficient visual separation on dark backgrounds.
 */
export const seriesColors = [
  tokens.brand,       // violet
  tokens.accent,      // cyan
  tokens.success,     // green
  tokens.warning,     // amber
  tokens.info,        // blue
  tokens.danger       // red
] as const;

/* ------------------------------------------------------------------ */
/* Component-level theme objects                                        */
/* ------------------------------------------------------------------ */

export const chartTheme = {
  /** CartesianGrid props */
  grid: {
    strokeDasharray: "3 3",
    stroke: "rgba(255, 255, 255, 0.06)",
    vertical: false
  },

  /** XAxis / YAxis shared props */
  axis: {
    stroke: "rgba(255, 255, 255, 0.08)",
    tick: {
      fill: tokens.textSecondary,
      fontSize: 11,
      fontFamily: "var(--font-family-body)"
    },
    tickLine: false,
    axisLine: false
  },

  /** Tooltip content styling */
  tooltip: {
    contentStyle: {
      backgroundColor: tokens.bgElevated,
      border: `1px solid ${tokens.borderDefault}`,
      borderRadius: "var(--radius-sm)",
      boxShadow: "var(--elevation-md)",
      color: tokens.textPrimary,
      fontSize: "12px",
      fontFamily: "var(--font-family-body)",
      padding: "8px 12px"
    },
    itemStyle: {
      color: tokens.textSecondary,
      fontSize: "11px"
    },
    labelStyle: {
      color: tokens.textPrimary,
      fontWeight: 600,
      marginBottom: "4px"
    },
    cursor: {
      stroke: tokens.brandHover,
      strokeDasharray: "4 4"
    }
  },

  /** Legend styling */
  legend: {
    wrapperStyle: {
      color: tokens.textSecondary,
      fontSize: "12px",
      fontFamily: "var(--font-family-body)"
    }
  }
} as const;
