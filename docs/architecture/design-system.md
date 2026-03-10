# Design System & UX Guide

This document is the single source of truth for all visual and interaction standards. Every agent building pages, features, data sections, or stats must follow these rules — no exceptions.

---

## Design Philosophy: Loira Voss

The platform follows a **premium neutral facts-only aesthetic** — presenting government data clearly without editorial judgment. Every design decision supports:

1. **Neutral presentation** — data is shown as-is; no color-coded good/bad judgments
2. **Mobile-first perfection** — every layout starts at 375px and scales up
3. **Premium glass-card aesthetic** — dark navy canvas, frosted glass surfaces, subtle gradients
4. **Density without clutter** — information-rich but never overwhelming

---

## Colour Palette

| Role | Value | Token |
|---|---|---|
| Canvas background | `#0A1428 → #02060F` | `--ref-color-navy-900/950` (gradient via `theme.css`) |
| Card surface | `#0F172A` | `--ref-color-navy-800` |
| Card border | `#1E2937` | `--ref-color-navy-700` |
| Brand / accent | `#00D4C8` | `--ref-color-brand-500` |
| Trend direction | `#00D4C8` | `--color-trend-up` (both up AND down) |
| Text primary | `#F1F5F9` | `--ref-color-grey-100` |
| Text secondary | `#94A3B8` | `--ref-color-grey-400` |
| Text disabled | `#64748B` | `--ref-color-grey-500` |
| Benchmark school | teal | `--color-benchmark-school` |
| Benchmark local | cyan | `--color-benchmark-local` |
| Benchmark national | green | `--color-benchmark-national` |
| Success | `#22c55e` | `--ref-color-success-500` |
| Warning | `#f59e0b` | `--ref-color-warning-500` |
| Danger | `#ef4444` | `--ref-color-danger-500` |
| Info | `#3b82f6` | `--ref-color-info-500` |

**Tailwind semantic aliases** (use these in classes, never raw hex):

`text-primary`, `text-secondary`, `text-disabled`, `text-brand`, `bg-canvas`, `bg-surface`, `bg-elevated`, `border-border`, `border-border-subtle`, `bg-brand-solid`, `text-benchmark-school`, `text-benchmark-local`, `text-benchmark-national`

**Critical rule: trend indicators are always teal, never red/green.** Direction triangles (▲/▼) use `text-brand` regardless of whether the direction is conventionally "good" or "bad". The platform presents facts, not judgements.

---

## Typography

- **Font family:** Inter (all weights) via `@fontsource/inter`, fallback `system-ui, sans-serif`
- **Display headings:** `font-display font-semibold tracking-tight`
- **Metric numbers:** `font-bold text-3xl sm:text-4xl` (hero: `text-4xl sm:text-5xl`)
- **Body / labels:** `text-sm leading-relaxed`
- **Eyebrow / caption:** `eyebrow` CSS class → mono, xs, uppercase, `letter-spacing: 0.14em`, `text-secondary`
- **Title Case rule:** All section headings and StatCard labels use Title Case (e.g. "Free School Meals", not "FREE SCHOOL MEALS"). Never use `text-transform: uppercase` on headings or labels.

---

## Responsive Breakpoints

| Breakpoint | Width | Use |
|---|---|---|
| base | 0px | Mobile-first default |
| `xs` | 360px | Very narrow mobile |
| `sm` | 640px | Landscape mobile / tablet — switch stacked to horizontal |
| `md` | 768px | Tablet |
| `lg` | 1024px | Desktop — add sidebar/multi-column layouts |
| `xl` | 1280px | Max content width |

Every page and component starts at 375px. Common responsive patterns:
- Padding: `px-4 sm:px-6 lg:px-8`
- Typography: `text-3xl sm:text-4xl lg:text-5xl`
- Grid: 1 col mobile → 2 cols `sm` → 3–4 cols `lg`

---

## Z-Index Scale

| Layer | Value | Use |
|---|---|---|
| Base | `z-[1]` | Default elements |
| Nav | `z-[10]` | Sticky header, sticky bars |
| Popover | `z-[30]` | Tooltips, popovers |
| Modal | `z-[40]` | Modal dialogs |
| Toast | `z-[50]` | Toast notifications |

---

## Animation & Motion

| Speed | Duration | Token |
|---|---|---|
| Fast | 120ms | `duration-fast` |
| Base | 180ms | `duration-base` |
| Slow | 260ms | `duration-slow` |

All interactive components respect `prefers-reduced-motion: reduce`.

---

## CSS Utility Classes

Defined in `src/styles/theme.css`:

| Class | Purpose |
|---|---|
| `panel-surface` | Glass gradient bg, 1px border, `backdrop-filter: blur(18px)`, `box-shadow: var(--elevation-sm)` |
| `eyebrow` | Mono font, xs, uppercase, wide tracking, secondary colour |
| `section-divider` | 1px top border for section breaks |
| `scrollbar-hide` | Hides scrollbar on all browsers |

---

## Component Reference

All paths are relative to `apps/web/src/`.

### Button (`components/ui/Button.tsx`)

shadcn/ui `cva`-based button with unified micro-animation on every variant.

**Base animation:** `transition-all duration-200 ease-out hover:scale-[1.02] active:scale-[0.98]`

| Variant | Use case | Visual |
|---------|----------|--------|
| `primary` | Main CTAs: "Add to compare", "Open compare", "Browse schools" | Solid teal fill (`bg-brand-solid`) |
| `secondary` | Secondary actions: "Remove", "Save for later", "Share", "Back to search" | Outline with subtle border (`border-border bg-elevated`) |
| `ghost` | Tertiary / destructive: "Clear all" | Transparent, text-only hover |
| `compare` | Reserved — glass-card look for specialised compare contexts | Backdrop-blur glass with teal border accents |

**Sizes:** `default` (h-11 px-4 text-sm), `sm` (h-9 px-3 text-xs), `none` (no sizing).

**Props:**
```tsx
interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "compare";
  size?: "default" | "sm" | "none";
  asChild?: boolean;  // Radix Slot composition for wrapping <Link> etc.
}
```

**Usage:**
```tsx
import { Button } from "@/components/ui/Button";

<Button variant="primary">Add to Compare</Button>
<Button asChild variant="secondary" size="sm">
  <Link to="/schools">Back to Search</Link>
</Button>
```

**Rules:**
- Always use `Button` — no raw `<button>` for action buttons.
- Never add inline `hover:scale` or `transition-all` overrides; the cva base handles all animation.
- Mobile sticky bars use `min-h-[52px]` touch targets.

---

### Card (`components/ui/Card.tsx`)

`panel-surface rounded-xl` + `hover:-translate-y-0.5 hover:shadow-lg transition-all duration-200`

**Usage:**
```tsx
import { Card } from "@/components/ui/Card";
<Card className="space-y-3">{content}</Card>
```

Also exports `Panel` — extends Card with `rounded-2xl` and muted bg. Used for premium gate banners.

---

### StatCard (`components/ui/stat-card.tsx`) — CRITICAL

The single source of truth for **all** numeric stat display. Every metric on every page must use this component.

**Import:** `import { StatCard, type BenchmarkSlot } from "@/components/ui/stat-card";`

Legacy shim at `components/data/StatCard.tsx` re-exports — existing code works, new code should import from `components/ui/stat-card` directly.

**Props:**
```tsx
interface StatCardProps {
  label: ReactNode;            // Metric label — Title Case, or JSX with GlossaryTerm
  tooltip?: string;            // Expandable ⓘ paragraph (preferred over description)
  description?: string;        // Legacy alias for tooltip
  value: string;               // Formatted display value ("32.4%", "£12.5k", "—")
  footer?: ReactNode;          // Sparkline + TrendIndicator below value
  icon?: ReactNode;            // Top-right icon (standalone cards only)
  benchmark?: BenchmarkSlot;   // Comparison bars (school vs local vs national)
  variant?: "default" | "hero" | "mini";
  size?: "sm" | "md" | "lg";
  trendDirection?: "up" | "down" | null;  // Inline ▲/▼ before value (no delta number)
  valueClassName?: string;     // Escape hatch — prefer size prop
}
```

**BenchmarkSlot interface:**
```tsx
interface BenchmarkSlot {
  localLabel: string;                    // "London", "Cheshire East"
  schoolRaw: number | null;
  localRaw: number | null;
  nationalRaw: number | null;
  isPercent: boolean;                    // Fixed 0–100 scale if true
  displayDecimals: number;
  schoolValueFormatted: string | null;
  localValueFormatted: string | null;
  nationalValueFormatted: string | null;
  schoolVsLocalDelta: number | null;
  schoolVsNationalDelta: number | null;
  schoolVsLocalDeltaFormatted: string | null;
  schoolVsNationalDeltaFormatted: string | null;
}
```

**Variants:**

| Variant | When to use | Chrome |
|---|---|---|
| `default` | Standalone metric in a `MetricGrid` | `Card` wrapper, `p-4 sm:p-5`, hover lift |
| `hero` | Most important metric in a section | `Card` + teal glow border |
| `mini` | Embedded inside an existing section card | Plain `div`, zero padding, zero border |

**Rule: never use `variant="default"` or `variant="hero"` inside another `Card`. Always use `variant="mini"` for nested stats.**

**Size prop:**

| Size | `default`/`hero` value | `mini` value |
|---|---|---|
| `sm` | `text-2xl sm:text-3xl` | `text-xl` |
| `md` _(default)_ | `text-3xl sm:text-4xl` | `text-2xl` |
| `lg` | `text-4xl sm:text-5xl` | `text-2xl sm:text-3xl` |

**Built-in protections:**
- Label container: `min-h-[40px]` — values align across grid rows regardless of title wrap
- Value: `tabular-nums break-all` — numbers never overflow
- Outer wrapper: `overflow-hidden`
- Benchmark bars: `h-2` mobile, `h-[5px]` sm+, visible at all breakpoints

**Benchmark delta neutrality:** Regional and national delta values always render in neutral gray (`#94A3B8`) — never conditionally coloured by sign.

---

### MetricGrid (`components/data/MetricGrid.tsx`)

Responsive grid for laying out StatCards.

**Props:**
```tsx
interface MetricGridProps {
  children: ReactNode;
  columns?: 2 | 3 | 4;     // md+ column count (default: 3)
  mobileTwo?: boolean;      // 2-col on narrow mobile (default: false → 1-col)
}
```

**Responsive behavior:** `gap-3 sm:gap-4`. Mobile 1-col (or 2-col with `mobileTwo`), then 2-col at `sm`, then `columns` at `lg`.

**Usage:**
```tsx
import { MetricGrid } from "@/components/data/MetricGrid";
<MetricGrid columns={3} mobileTwo>
  <StatCard ... />
  <StatCard ... />
  <StatCard ... />
</MetricGrid>
```

---

### TrendIndicator (`components/data/TrendIndicator.tsx`)

**Props:**
```tsx
interface TrendIndicatorProps {
  delta: number;                         // Absolute value
  direction?: "up" | "down" | "flat";
  unit?: "%" | "pp";
  period?: string;                       // "3-yr trend", "6-yr trend"
  asPercentage?: boolean;                // Legacy alias
}
```

| Direction | Symbol | Colour |
|---|---|---|
| Up | ▲ | `text-brand` (teal) |
| Down | ▼ | `text-brand` (teal) |
| Flat | — | `text-disabled` |

**Triangles are always teal, never red.** Delta values are absolute numbers — the triangle conveys sign.

**Trend footer layout — always vertical (`space-y-1.5`), never horizontal:**
1. Sparkline full-width on top
2. `▼ 1.2%` — triangle + value, `whitespace-nowrap`
3. `3-yr trend` — period label in `text-disabled`

---

### Sparkline (`components/data/Sparkline.tsx`)

**Props:**
```tsx
interface SparklineProps {
  data: number[];           // Data points (min 1)
  width?: number;           // ViewBox width (default: 80)
  height?: number;          // SVG height (default: 28)
  strokeColor?: string;     // CSS color or var()
  strokeWidth?: number;     // Default: 2
  showFill?: boolean;       // Gradient fill below line (default: true)
}
```

Renders `width="100%"` + `preserveAspectRatio="none"`. Always pass `className="w-full"` and place inside an `overflow-hidden` container.

---

### Badge (`components/ui/Badge.tsx`)

**Variants:** `default` (teal), `success` (green), `warning` (amber), `danger` (red), `info` (blue), `outline` (bordered).

Styling: `inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold`

---

### RatingBadge (`components/data/RatingBadge.tsx`)

Ofsted rating display. Maps `"1"` → Outstanding/success, `"2"` → Good/info, `"3"` → Requires Improvement/warning, `"4"` → Inadequate/danger, `null` → Not Rated/outline.

---

### GlossaryTerm (`components/data/GlossaryTerm.tsx`)

Renders as tooltip on desktop (pointer hover), popover on mobile (touch). Terms defined in `shared/glossary.ts`.

```tsx
<GlossaryTerm term="fsm">Free School Meals</GlossaryTerm>
```

---

### ProportionBar (`components/data/ProportionBar.tsx`)

Simple percentage bar: `h-2 w-full rounded-full bg-surface/75` with filled portion in `bg-brand-solid`.

---

### EthnicityBreakdown (`components/data/EthnicityBreakdown.tsx`)

Stacked proportion bar with sortable legend, hover interaction, collapsible items. 12-colour palette.

---

### SectionCompletenessNotice (`features/school-profile/components/SectionCompletenessNotice.tsx`)

Renders nothing for `available`, AlertTriangle + message for `partial`, CircleOff + message for `unavailable`.

```tsx
<SectionCompletenessNotice sectionLabel="Performance" completeness={completeness} />
```

---

### EmptyState / ErrorState (`components/ui/EmptyState.tsx` / `ErrorState.tsx`)

EmptyState: icon + title + description + optional action button. ErrorState: danger-colored variant with optional retry.

---

### Toast (`components/ui/Toast.tsx`)

Variants: `default`, `success`, `warning`, `danger`, `info`. Wrap app in `<ToastProvider>`, call `toast({ title, variant })`.

---

### LoadingSkeleton (`components/ui/LoadingSkeleton.tsx`)

Variants: `lines` (generic animated bars), `result-card` (mimics ResultCard geometry).

---

## Layout Components

### PageContainer (`components/layout/PageContainer.tsx`)

Max width `1200px`, padding `px-4 sm:px-6 lg:px-8`, vertical `pt-8 sm:pt-10 lg:pt-12` + `pb-12`.

Every page route wraps its content in `<PageContainer>`.

### SiteHeader (`components/layout/SiteHeader.tsx`)

Sticky, backdrop-blur. Contains: logo, compare button (count badge), auth buttons, theme toggle.

### ProfileSectionAccordion (`features/school-profile/components/ProfileSectionAccordion.tsx`)

Mobile: collapsible toggle with ChevronDown. Desktop (`lg+`): always visible, no toggle. Smooth CSS transitions.

```tsx
<ProfileSectionAccordion title="Results & Progress" defaultOpen>
  <YourSectionContent />
</ProfileSectionAccordion>
```

---

## Metric Catalog (`features/school-profile/metricCatalog.ts`)

**Single source of truth for all metric labels, descriptions, units, and formatting.**

```tsx
interface MetricCatalogEntry {
  key: string;
  label: string;               // Title Case — "Free School Meals"
  description?: string;        // Plain-English tooltip text
  section: MetricSectionKey;   // "demographics" | "finance" | "attendance" | "behaviour" | "workforce" | "performance" | "area"
  unit: MetricUnit;            // "percent" | "currency" | "count" | "ratio" | "rate" | "score"
  decimals?: number;
}
```

**Key functions:**
- `getMetricCatalogEntry(key)` → entry or undefined
- `formatMetricValue(value, unit, decimals?)` → `"32.1%"`, `"£12.5k"`, `"234"`, `"—"`
- `formatMetricDelta(value, unit)` → `"+2.1%"`, `"-0.8"`

**Rule: never hard-code metric labels.** Always use `getMetricCatalogEntry(key).label`. To add a new metric, add it to the catalog first.

---

## Building a New Section — Step by Step

This is the canonical pattern. Follow it exactly for visual consistency.

### 1. Add metrics to the catalog

In `features/school-profile/metricCatalog.ts`, add entries:

```tsx
{ key: "your_metric_key", label: "Your Metric Name", description: "Plain-English explanation", section: "yourSection", unit: "percent", decimals: 1 }
```

### 2. Create the section component

File: `features/school-profile/components/YourNewSection.tsx`

```tsx
import { StatCard, type BenchmarkSlot } from "@/components/ui/stat-card";
import { MetricGrid } from "@/components/data/MetricGrid";
import { TrendIndicator } from "@/components/data/TrendIndicator";
import { Sparkline } from "@/components/data/Sparkline";
import { SectionCompletenessNotice } from "./SectionCompletenessNotice";
import { getMetricCatalogEntry, formatMetricValue } from "../metricCatalog";

// Standard section props — every section receives these
interface YourNewSectionProps {
  data: YourDataVM | null;
  trends: TrendsVM | null;
  completeness: SectionCompletenessVM;
  benchmarkDashboard: BenchmarkDashboardVM | null;
}

// Metric keys this section displays — order matters
const METRIC_KEYS = ["metric_a", "metric_b", "metric_c"] as const;

// Helper: convert benchmark API data to StatCard's BenchmarkSlot
function toBenchmarkSlot(bm: BenchmarkMetricVM): BenchmarkSlot {
  return {
    localLabel: bm.localAuthorityName,
    schoolRaw: bm.schoolValue,
    localRaw: bm.localValue,
    nationalRaw: bm.nationalValue,
    isPercent: bm.unit === "percent",
    displayDecimals: barDecimals(bm.unit),
    schoolValueFormatted: formatMetricValue(bm.schoolValue, bm.unit),
    localValueFormatted: formatMetricValue(bm.localValue, bm.unit),
    nationalValueFormatted: formatMetricValue(bm.nationalValue, bm.unit),
    schoolVsLocalDelta: bm.schoolVsLocalDelta,
    schoolVsNationalDelta: bm.schoolVsNationalDelta,
    schoolVsLocalDeltaFormatted: formatMetricDelta(bm.schoolVsLocalDelta, bm.unit),
    schoolVsNationalDeltaFormatted: formatMetricDelta(bm.schoolVsNationalDelta, bm.unit),
  };
}

// Helper: decimal places for benchmark bars
function barDecimals(unit: string): number {
  return unit === "percent" ? 1 : unit === "ratio" ? 1 : 0;
}

// Helper: render trend footer (sparkline + delta)
function renderTrendFooter(series: TrendSeriesVM | undefined): ReactNode {
  if (!series || series.values.length < 2) return null;
  const delta = series.values[series.values.length - 1] - series.values[0];
  const direction = delta > 0 ? "up" : delta < 0 ? "down" : "flat";
  const years = series.values.length;
  return (
    <div className="space-y-1.5">
      <Sparkline data={series.values} height={30} className="w-full" />
      <TrendIndicator
        delta={Math.abs(delta)}
        direction={direction}
        unit="%"
        period={`${years}-yr trend`}
      />
    </div>
  );
}

export function YourNewSection({ data, trends, completeness, benchmarkDashboard }: YourNewSectionProps) {
  if (!data) return null;

  // Build lookup maps
  const trendLookup = new Map(trends?.series.map(s => [s.metricKey, s] as const) ?? []);
  const benchmarkLookup = new Map<string, BenchmarkMetricVM>(
    benchmarkDashboard?.sections.flatMap(s => s.metrics.map(m => [m.metricKey, m] as const)) ?? []
  );

  return (
    <section
      aria-labelledby="your-section-heading"
      className="panel-surface rounded-lg space-y-4 p-4 sm:space-y-5 sm:p-6"
    >
      {/* ── Title row ── */}
      <div className="flex items-baseline justify-between gap-3">
        <h2
          id="your-section-heading"
          className="flex items-center gap-2 text-lg font-semibold text-primary sm:text-xl"
        >
          <span className="inline-block h-5 w-[3px] rounded-full bg-brand" aria-hidden />
          Your Section Title
        </h2>
        {data.yearRange && (
          <span className="text-xs text-secondary">{data.yearRange}</span>
        )}
      </div>

      {/* ── Completeness notice ── */}
      <SectionCompletenessNotice sectionLabel="YourSection" completeness={completeness} />

      {/* ── Metrics grid ── */}
      <MetricGrid columns={3} mobileTwo>
        {METRIC_KEYS.flatMap(key => {
          const value = data.metrics[key] ?? null;
          const catalog = getMetricCatalogEntry(key);
          if (value === null || !catalog) return [];

          const bm = benchmarkLookup.get(key);
          return (
            <StatCard
              key={key}
              label={catalog.label}
              tooltip={catalog.description}
              value={formatMetricValue(value, catalog.unit, catalog.decimals) ?? "—"}
              footer={renderTrendFooter(trendLookup.get(key))}
              benchmark={bm ? toBenchmarkSlot(bm) : undefined}
              variant={key === METRIC_KEYS[0] ? "hero" : "default"}
            />
          );
        })}
      </MetricGrid>
    </section>
  );
}
```

### 3. Wire into the profile page

In `features/school-profile/SchoolProfileFeature.tsx`:

```tsx
<ProfileSectionAccordion title="Your Section Title" defaultOpen={false}>
  <YourNewSection
    data={profile.yourSection}
    trends={profile.trends}
    completeness={profile.completeness.yourSection}
    benchmarkDashboard={profile.benchmarkDashboard}
  />
</ProfileSectionAccordion>
```

### 4. Spacing constants to follow

| Element | Mobile | Desktop (sm+) |
|---|---|---|
| Section outer padding | `p-4` | `sm:p-6` |
| Section internal rhythm | `space-y-4` | `sm:space-y-5` |
| Between sections | `space-y-5` | `lg:space-y-8` |
| Grid gap | `gap-3` | `sm:gap-4` |
| Subsection divider | `border-t border-border-subtle/50 pt-5` | same |
| Group header + grid | `space-y-3` | same |

### 5. Subsection pattern (when a section has groups)

```tsx
<div className="space-y-6">
  {/* Group A */}
  <div className="space-y-3">
    <h3 className="text-base font-semibold text-primary">Group A Title</h3>
    <MetricGrid columns={3} mobileTwo>{groupACards}</MetricGrid>
  </div>

  {/* Divider */}
  <div className="space-y-4 border-t border-border-subtle/50 pt-5">
    <h3 className="text-base font-semibold text-primary">Group B Title</h3>
    <MetricGrid columns={4} mobileTwo>{groupBCards}</MetricGrid>
  </div>
</div>
```

---

## Building a New Page — Step by Step

### 1. Create the feature directory

```
features/your-feature/
  YourFeature.tsx          # Main page component
  components/              # Page-specific components
  mappers/                 # API → VM transformation
  your-feature.test.tsx    # Tests
```

### 2. Page shell

```tsx
import { PageContainer } from "@/components/layout/PageContainer";

export function YourFeature() {
  return (
    <PageContainer>
      <div className="space-y-5 lg:space-y-8">
        {/* Page header */}
        <header className="space-y-3">
          <p className="eyebrow">Page Category</p>
          <h1 className="text-3xl font-bold tracking-tight text-primary sm:text-4xl lg:text-5xl">
            Page Title
          </h1>
        </header>

        {/* Sections */}
        <YourSectionA ... />
        <YourSectionB ... />
      </div>
    </PageContainer>
  );
}
```

### 3. Section title pattern

Every section heading uses a teal accent bar:

```tsx
<h2 className="flex items-center gap-2 text-lg font-semibold text-primary sm:text-xl">
  <span className="inline-block h-5 w-[3px] rounded-full bg-brand" aria-hidden />
  Section Title
</h2>
```

### 4. Two-column profile-style layout (optional)

```tsx
<div className="mx-auto max-w-[1280px] lg:grid lg:grid-cols-[280px_minmax(0,1fr)] lg:gap-8">
  {/* Sidebar (sticky TOC) */}
  <aside className="hidden lg:block">
    <nav className="sticky top-[3.75rem]">{/* TOC links */}</nav>
  </aside>

  {/* Main content */}
  <main className="space-y-5 lg:space-y-8">
    {sections}
  </main>
</div>
```

---

## Common UI Patterns

### Section title with year range
```tsx
<div className="flex items-baseline justify-between gap-3">
  <h2 className="flex items-center gap-2 text-lg font-semibold text-primary sm:text-xl">
    <span className="inline-block h-5 w-[3px] rounded-full bg-brand" aria-hidden />
    Title
  </h2>
  <span className="text-xs text-secondary">2023/24</span>
</div>
```

### Inline badge
```tsx
<span className="inline-flex items-center gap-1.5 rounded-full border border-brand/30 bg-brand/10 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.08em] text-brand">
  <Icon className="h-3 w-3" aria-hidden />
  Label
</span>
```

### Info box
```tsx
<div className="rounded-md border border-brand/20 bg-brand/5 p-4">
  <div className="flex items-start gap-3">
    <InfoIcon className="mt-0.5 h-4 w-4 shrink-0 text-brand" aria-hidden />
    <p className="text-xs leading-6 text-secondary">Informational text here.</p>
  </div>
</div>
```

### Gradient divider
```tsx
<div className="h-px bg-gradient-to-r from-brand/40 via-brand/10 to-transparent" />
```

### Mobile sticky action bar
```tsx
<div className="fixed inset-x-0 bottom-0 z-[10] border-t border-border bg-canvas/95 backdrop-blur lg:hidden"
     style={{ paddingBottom: "env(safe-area-inset-bottom)" }}>
  <div className="flex items-center gap-2 px-4 min-h-[52px]">
    <Button variant="primary" className="flex-1">Primary Action</Button>
    <Button variant="secondary" className="flex-1">Secondary</Button>
  </div>
</div>
```
When using a mobile sticky bar, add `pb-20 lg:pb-0` to main content to prevent overlap.

---

## School Profile Layout

**Mobile (`< 1024px`):**
- Single column, full-width cards
- Sections collapse into `ProfileSectionAccordion`; Ofsted and Results & Progress default open
- Sticky action bar at bottom: `min-h-[52px]`, `env(safe-area-inset-bottom)` padding
- `pb-20` on main content

**Desktop (`≥ 1024px`):**
- Two-column grid: 280px sticky TOC sidebar + flexible main content
- TOC: `position: sticky; top: 3.75rem`
- Max width: 1280px centred via `PageContainer`
- Accordion toggles are `lg:hidden` — all sections always rendered

---

## Compare Page Layout

**School strip:** Fixed 4-slot layout. `FilledCard` for schools, `GhostCard` (dashed border, "+ Add school") for empty slots. Mobile: 2×2 grid.

**Accordion sections:**
- Each data section is a collapsible accordion
- First 3 sections default open
- Toggle: `border-l-2 border-l-brand` teal accent, `bg-brand/[0.04]` tinted glass
- Metric count badge in header

**Table layout:**
- Sticky metric label column (200px), school columns (180px each)
- Zebra striping: even rows `bg-surface/[0.06]`
- Row hover: `hover:bg-surface/50`

**"This school" highlight:** First URN gets `border-l-2 border-l-brand/30 bg-brand/[0.02]` on every cell.

**Completeness labels:** Suppress `partial_metric_coverage` and `insufficient_years_published` reason codes in compare cells — they are section-level concerns that clutter when repeated per-cell.

**Mobile (`< 640px`):** Vertical stacked cards per metric (metric label header → school value cards). Desktop table hidden via `hidden sm:block`.

---

## Premium Access Gates

- Locked sections show a slim `Panel` banner with `Sparkles` icon, title, description, CTA
- SaveSchoolButton: Heart icon, tooltip on hover, status-aware label ("Save for later" / "Saved" / "Sign in to save" / "Unlock save")
- Unauthenticated users redirected to sign-in; locked users redirected to upgrade
- Dev premium bypass: `isDevUnlocked` check (same pattern on profile + compare)

---

## Shareability

- Compare page: Share button copies current URL (with `?urns=` params) to clipboard
- Profile page: URL-addressable with `/schools/:urn`
- Compare selection persisted to localStorage as fallback when navigating without explicit `urns`

---

## Anti-Patterns (Do Not)

1. **Never use red/green for trends** — always neutral teal triangles
2. **Never use `text-transform: uppercase`** — use Title Case in source strings
3. **Never nest `StatCard default/hero` inside a `Card`** — use `variant="mini"`
4. **Never add inline hover/transition overrides** — the Button cva handles animation
5. **Never use horizontal flex for trend footers** — always vertical stack
6. **Never add decorative SVG watermarks** — hero sections are illustration-free
7. **Never show completeness noise per-cell** — suppress section-level reason codes in compare
8. **Never hard-code metric labels** — use `metricCatalog.ts` as the single source
9. **Never use raw `<button>`** — always use the `Button` component
10. **Never use hex colours directly** — use Tailwind semantic tokens (`text-brand`, `bg-surface`, etc.)
11. **Never skip the `panel-surface` class on section cards** — it provides the glass aesthetic
12. **Never omit `aria-labelledby` on `<section>`** — every section needs an accessible heading link
13. **Never use `gap-8` or wider spacing on mobile** — tighten to `gap-5` with `sm:gap-8`

---

## File Reference (Quick Lookup)

| Category | File |
|---|---|
| **UI Primitives** | |
| Button | `components/ui/Button.tsx` |
| Card / Panel | `components/ui/Card.tsx` |
| StatCard | `components/ui/stat-card.tsx` |
| Badge | `components/ui/Badge.tsx` |
| Toast | `components/ui/Toast.tsx` |
| EmptyState | `components/ui/EmptyState.tsx` |
| ErrorState | `components/ui/ErrorState.tsx` |
| LoadingSkeleton | `components/ui/LoadingSkeleton.tsx` |
| Field / TextInput / Select | `components/ui/Field.tsx`, `TextInput.tsx`, `Select.tsx` |
| Tabs / Tooltip / Popover | `components/ui/Tabs.tsx`, `Tooltip.tsx`, `Popover.tsx` |
| **Data Components** | |
| MetricGrid | `components/data/MetricGrid.tsx` |
| TrendIndicator | `components/data/TrendIndicator.tsx` |
| Sparkline | `components/data/Sparkline.tsx` |
| RatingBadge | `components/data/RatingBadge.tsx` |
| ProportionBar | `components/data/ProportionBar.tsx` |
| EthnicityBreakdown | `components/data/EthnicityBreakdown.tsx` |
| GlossaryTerm | `components/data/GlossaryTerm.tsx` |
| DataStatusBadge | `components/data/DataStatusBadge.tsx` |
| MetricUnavailable | `components/data/MetricUnavailable.tsx` |
| SectionCompletenessNotice | `features/school-profile/components/SectionCompletenessNotice.tsx` |
| **Layout** | |
| PageContainer | `components/layout/PageContainer.tsx` |
| SiteHeader | `components/layout/SiteHeader.tsx` |
| SiteFooter | `components/layout/SiteFooter.tsx` |
| ProfileSectionAccordion | `features/school-profile/components/ProfileSectionAccordion.tsx` |
| **Data / Config** | |
| Metric catalog | `features/school-profile/metricCatalog.ts` |
| Glossary | `shared/glossary.ts` |
| Completeness utils | `shared/completeness.ts` |
| cn() utility | `shared/utils/cn.ts` |
| **Styles** | |
| Design tokens | `styles/tokens.css` |
| Theme utilities | `styles/theme.css` |
| Tailwind config | `../../tailwind.config.ts` (repo: `apps/web/tailwind.config.ts`) |
