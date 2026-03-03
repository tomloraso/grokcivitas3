import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "var(--color-bg-canvas)",
        surface: "var(--color-bg-surface)",
        elevated: "var(--color-bg-elevated)",
        primary: "var(--color-text-primary)",
        secondary: "var(--color-text-secondary)",
        disabled: "var(--color-text-disabled)",
        border: "var(--color-border-default)",
        "border-subtle": "var(--color-border-subtle)",
        brand: "var(--color-action-primary)",
        "brand-hover": "var(--color-action-primary-hover)",
        "brand-solid": "var(--color-action-primary-solid)",
        accent: "var(--color-action-secondary)",
        success: "var(--color-state-success)",
        warning: "var(--color-state-warning)",
        danger: "var(--color-state-danger)",
        info: "var(--color-state-info)",
        "map-label": "var(--map-label-secondary)",
        "map-label-muted": "var(--map-label-muted)",
        "map-water": "var(--map-surface-water)"
      },
      fontFamily: {
        display: ["var(--font-family-display)", "sans-serif"],
        sans: ["var(--font-family-body)", "sans-serif"],
        mono: ["var(--font-family-mono)", "monospace"]
      },
      spacing: {
        "1": "var(--space-1)",
        "2": "var(--space-2)",
        "3": "var(--space-3)",
        "4": "var(--space-4)",
        "5": "var(--space-5)",
        "6": "var(--space-6)",
        "8": "var(--space-8)",
        "10": "var(--space-10)",
        "12": "var(--space-12)",
        "16": "var(--space-16)",
        "20": "var(--space-20)"
      },
      borderRadius: {
        sm: "var(--radius-sm)",
        md: "var(--radius-md)",
        lg: "var(--radius-lg)",
        xl: "var(--radius-xl)"
      },
      boxShadow: {
        sm: "var(--elevation-sm)",
        md: "var(--elevation-md)",
        lg: "var(--elevation-lg)",
        inner: "inset 0 1px 0 rgba(255, 255, 255, 0.05)"
      },
      transitionDuration: {
        fast: "var(--motion-fast)",
        base: "var(--motion-base)",
        slow: "var(--motion-slow)"
      },
      zIndex: {
        base: "var(--z-base)",
        nav: "var(--z-nav)",
        popover: "var(--z-popover)",
        modal: "var(--z-modal)",
        toast: "var(--z-toast)"
      },
      screens: {
        xs: "360px",
        sm: "640px",
        md: "768px",
        lg: "1024px",
        xl: "1280px",
        "2xl": "1536px"
      },
      keyframes: {
        "fade-in": {
          from: { opacity: "0" },
          to: { opacity: "1" }
        },
        "fade-out": {
          from: { opacity: "1" },
          to: { opacity: "0" }
        },
        "slide-in-right": {
          from: { transform: "translateX(100%)" },
          to: { transform: "translateX(0)" }
        },
        "slide-out-right": {
          from: { transform: "translateX(0)" },
          to: { transform: "translateX(100%)" }
        },
        "slide-in-left": {
          from: { transform: "translateX(-100%)" },
          to: { transform: "translateX(0)" }
        },
        "slide-out-left": {
          from: { transform: "translateX(0)" },
          to: { transform: "translateX(-100%)" }
        }
      },
      animation: {
        "fade-in": "fade-in var(--motion-slow) ease-out",
        "fade-out": "fade-out var(--motion-slow) ease-in",
        "slide-in-right": "slide-in-right var(--motion-slow) ease-out",
        "slide-out-right": "slide-out-right var(--motion-slow) ease-in",
        "slide-in-left": "slide-in-left var(--motion-slow) ease-out",
        "slide-out-left": "slide-out-left var(--motion-slow) ease-in"
      }
    }
  },
  plugins: []
};

export default config;
