# Web

React + TypeScript frontend for Civitas, consuming backend API contracts.

## Commands

```bash
npm install
npm run dev
npm run lint
npm run typecheck
npm run test
npm run build
npm run generate:types
```

## Contract typing

- Backend OpenAPI is the contract source of truth.
- Generated types live in `src/api/generated-types.ts`.
- Frontend should consume aliases from `src/api/types.ts`.

---

## Design System

The central design system & UX guide lives at **[`docs/architecture/design-system.md`](../../docs/architecture/design-system.md)**. It covers:

- Colour palette, typography, and spacing tokens
- Every UI primitive (Button, Card, StatCard, MetricGrid, TrendIndicator, Sparkline, etc.) with props and usage
- Step-by-step cookbook for building new sections and pages
- Layout patterns (profile, compare, mobile sticky bars)
- Anti-patterns and rules

**Read it before building any UI.** The sections below are kept for historical context but the central guide is the source of truth.

---

## School Profile UI — Loira Voss design system (P9, 2026-03-09)

### Colour palette

| Role | Value | Token |
|---|---|---|
| Canvas background | `#0A1428 → #02060F` | `--ref-color-navy-900/950` (gradient via `theme.css`) |
| Card surface | `#0F172A` | `--ref-color-navy-800` |
| Card border | `#1E2937` | `--ref-color-navy-700` |
| Brand / accent | `#00D4C8` | `--ref-color-brand-500` |
| Trend positive | `#00D4C8` | `--color-trend-up` |
| Trend negative | `#FF4D6D` | `--color-trend-down` |
| Text primary | `#F1F5F9` | `--ref-color-grey-100` |
| Text secondary | `#94A3B8` | `--ref-color-grey-400` |

### Typography

- **Font family:** Inter (all weights) — loaded via `@fontsource/inter`, falls back to `system-ui, sans-serif`
- **Display headings:** `font-display font-semibold tracking-tight`
- **Metric numbers:** `font-bold text-3xl sm:text-4xl` (hero variant: `text-4xl sm:text-5xl`)
- **Body / labels:** `text-sm leading-relaxed`

### Card primitive (`src/components/ui/Card.tsx`)

`panel-surface rounded-xl` + `hover:-translate-y-0.5 hover:shadow-lg transition-all duration-200`

`panel-surface` is a CSS utility in `theme.css`: glass gradient background, 1px border at `--color-border-default`, `backdrop-filter: blur(18px)`.

### Button system (`src/components/ui/Button.tsx`)

shadcn/ui `cva`-based button with unified micro-animation on every variant.

**Base animation:** `transition-all duration-200 ease-out hover:scale-[1.02] active:scale-[0.98]`

| Variant | Use case | Visual |
|---------|----------|--------|
| `primary` | Main CTAs: "Add to compare", "Open compare", "Browse schools" | Solid teal fill (`bg-brand-solid`) |
| `secondary` | Secondary actions: "Remove from compare", "Save for later", "Share", "Back to search" | Outline with subtle border (`border-border bg-elevated`) |
| `ghost` | Tertiary / destructive: "Clear all" | Transparent, text-only hover |
| `compare` | Reserved — glass-card look for specialised compare contexts | Backdrop-blur glass with teal border accents |

**Sizes:** `default` (h-11 px-4 text-sm), `sm` (h-9 px-3 text-xs), `none` (no sizing — for custom layout).

**Rules:**
- Always use the shadcn `Button` component — no raw `<button>` for action buttons.
- Never add inline `hover:scale` or `transition-all` overrides; the cva base handles all animation.
- Profile header uses `primary` for the main CTA and `secondary` for the secondary action in both "not in compare" and "in compare" states.
- Mobile sticky bar mirrors desktop variant assignments with `min-h-[52px]` touch targets.

### School profile layout (`src/features/school-profile/SchoolProfileFeature.tsx`)

**Mobile (`< 1024px`)**
- Single column, full-width cards, 24px internal padding
- Sections 3–8 (Ofsted → Neighbourhood) collapse into accordions (`ProfileSectionAccordion`); Ofsted Profile and Results & Progress open by default
- Sticky "Add to compare" bar fixed to viewport bottom; `min-h-[52px]` for thumb-friendly tap target; `env(safe-area-inset-bottom)` padding guards iOS home indicator
- `pb-24` on main content column keeps the last section visible above the sticky bar

**Desktop (`≥ 1024px`)**
- Two-column grid: `280px` sticky TOC sidebar + `minmax(0, 1fr)` main content
- TOC sidebar: `position: sticky; top: 3.75rem` (flush below the 56px nav)
- Accordion toggles are `lg:hidden`; all sections always rendered
- Max content width: `1280px` centred via `PageContainer`

### Brand placeholder

Every user-facing `"CIVITAS"` string replaced with `"[BRAND]"` in:
- `SiteHeader.tsx` — nav logo + aria-label
- `SiteFooter.tsx` — footer logo + copyright line

### No background illustrations

Hero section is illustration-free. Any decorative SVG watermarks must not be reintroduced.

### StatCard primitive — design system rule (P10, 2026-03-09)

**Canonical location:** `src/components/ui/stat-card.tsx`

`StatCard` is the single source of truth for all numeric stat display across the school profile. It uses `cva` for variant and size control.

#### Variants

| Variant | When to use | Chrome |
|---|---|---|
| `default` | Standalone metric in a `MetricGrid` | `Card` wrapper, `p-4 sm:p-5`, hover lift |
| `hero` | Most important metric in a section | `Card` + teal glow border |
| `mini` | Embedded inside an existing section card | Plain `div`, zero padding, zero border |

**Rule: never use `variant="default"` or `variant="hero"` inside another `Card`. Always use `variant="mini"` for nested stats.** This prevents the double-padding bug that caused desktop overflow.

#### Size prop

| Size | `default` / `hero` value | `mini` value |
|---|---|---|
| `sm` | `text-2xl sm:text-3xl` | `text-xl` |
| `md` _(default)_ | `text-3xl sm:text-4xl` | `text-2xl` |
| `lg` | `text-4xl sm:text-5xl` | `text-2xl sm:text-3xl` |
| _(hero md)_ | `text-4xl sm:text-5xl` | — |
| _(hero lg)_ | `text-5xl sm:text-6xl` | — |

`size` replaces ad-hoc `valueClassName` overrides entirely. Use `valueClassName` only as a one-off escape hatch.

#### Overflow protection (built in)

- Label container: `min-w-0 leading-tight` — long labels wrap cleanly inside grid cells.
- Value: `tabular-nums break-all` — numeric strings never overflow their container.
- Outer wrapper: `overflow-hidden` — nothing escapes the card boundary.

#### Tooltip / info text

Pass `tooltip` (preferred) to show an expandable ⓘ paragraph when tapped. `description` is accepted as a legacy alias and behaves identically.

#### Shim

`src/components/data/StatCard.tsx` is a re-export shim — existing section components continue to work without modification. New code should import from `components/ui/stat-card` directly.

#### BenchmarkSlot

`BenchmarkSlot` interface and benchmark bar rendering are internal to `stat-card.tsx`. Import `BenchmarkSlot` type from `components/ui/stat-card` (or the shim).

**Benchmark delta neutrality rule:** Regional and national delta values (e.g. "+5.77%", "-2.7%") always render in neutral gray (`#94A3B8`) — never conditionally coloured by sign. The platform presents facts, not judgements.

#### `trendDirection` prop (P11, 2026-03-10)

```tsx
<StatCard trendDirection="up" ... />   // ▲ teal inline after value
<StatCard trendDirection="down" ... /> // ▼ teal inline after value
```

Renders a solid ▲ or ▼ immediately before the value number in brand teal (`text-brand`). Use this when you want direction without a delta number. When you also need a sparkline or delta number, continue using the `footer` prop with `<TrendIndicator>`.

**Trend footer layout rule — always use a vertical column (`space-y-1.5`), never a horizontal row:**
1. Sparkline full-width on top: `<Sparkline className="w-full" height={30} />`
2. `▼ 1.2%` — triangle immediately before the value, `whitespace-nowrap` (never splits)
3. `3-yr trend` — period label on its own line in `text-disabled`

Period label short form: `X-yr trend` (e.g. `3-yr trend`, `6-yr trend`). Never use `flex justify-between` for sparkline + indicator — it collapses the sparkline in narrow cards.

**Title case rule:** All StatCard titles use Title Case (e.g. "Free School Meals", "English as Additional Language") for superior readability and premium feel. The `uppercase` CSS class has been removed; labels render in their natural Title Case from the metric catalog. Never re-add `text-transform: uppercase`.

**Title min-height rule:** The label container inside `StatCard` has `min-h-[40px]`. This ensures the main value always starts at the same vertical position across a grid row, regardless of whether the title wraps to 1 or 2 lines. Never remove this — without it, long labels like "Education Health & Care Plan" push values down and break grid alignment.

---

### Trend indicators — design system rule (P11, 2026-03-10)

**Canonical location:** `src/components/data/TrendIndicator.tsx`

All trend indicators across the school profile use solid direction triangles:

| Direction | Symbol | Colour |
|---|---|---|
| Up | ▲ | `text-brand` (teal `#00D4C8`) |
| Down | ▼ | `text-brand` (teal `#00D4C8`) |
| Flat | — | `text-disabled` |

**Rule: triangles are always teal, never red. Direction only — no implied good/bad.** Whether a number going up is good (attendance) or bad (absence rate) is left to the reader. The platform presents facts, not judgements.

Delta values are rendered as absolute numbers — the triangle already conveys sign. Example output: `▲ 2.1% · 3yr`, `▼ 0.8% · 5-year trend`.

The `TrendingUp` / `TrendingDown` lucide icons and `text-trend-up` / `text-trend-down` conditional colours have been removed from `TrendIndicator`. The `period` prop is unchanged. The `asPercentage` prop is kept for backward compatibility.

---

### Neighbourhood desktop polish (P9 iterations 6–9 → superseded by P10)

Neighbourhood Context mini-stats now use `<StatCard variant="mini" size="sm">` inside each section card's light-bordered container. This eliminates the double-padding root cause. Domain decile labels use `min-w-0 leading-tight tracking-[0.04em]` to wrap long strings cleanly. Neighbourhood grid: `xl:grid-cols-3 xl:items-stretch`.

### Sparkline sizing (P9 iteration 5, 2026-03-09)

`Sparkline.tsx` now renders `width="100%"` + `preserveAspectRatio="none"` on all SVG paths. The `width` prop is viewBox coordinate space only — it no longer controls rendered pixel width. Pass `className="w-full"` at the call site inside an `overflow-hidden` container.

### Benchmark bars (P9 iteration 4, 2026-03-09)

`BenchmarkBlock` in `StatCard.tsx` renders bars at all breakpoints. The `hidden sm:block` / `sm:hidden` split has been removed. Bar height: `h-2` (8px) mobile, `h-[5px]` sm+. `TextRow` component deleted.

### Mobile density (P9 iteration 3, 2026-03-09)

Cards were over-padded on mobile, creating an "old people mode" feel. Tightened without touching desktop:

| Element | Mobile before | Mobile after | Desktop (sm+) |
|---|---|---|---|
| Section panel padding | `p-5` (20px) | `p-4` (16px) | `p-6` (24px) unchanged |
| Section internal rhythm | `space-y-5/6` | `space-y-4` | `space-y-5/6` unchanged |
| Between-section gap | `space-y-8` | `space-y-5` | `lg:space-y-8` unchanged |
| Hero metric strip gap | `gap-8` | `gap-5` | `sm:gap-8` unchanged |
| Accordion toggle height | `py-3` (48px+) | `py-2.5 min-h-[44px]` | hidden on desktop |
| Bottom guard | `pb-24` | `pb-20` | `lg:pb-0` unchanged |

All interactive elements retain ≥ 44px touch targets.

### School Finance section (P15-UI, 2026-03-11)

**Canonical location:** `src/features/school-profile/components/SchoolFinanceSection.tsx`

The finance section follows the same `benchmarkDashboard` wiring pattern as all other profile sections. It surfaces 21 finance fields across four visually distinct subsections:

**1. Latest Totals** — 5 summary cards (Total Income, Total Expenditure, Staff Costs, Revenue Reserve, In-Year Balance) rendered as `StatCard variant="mini" size="sm"` inside a glass inner card. In-Year Balance uses `trendDirection` to show surplus (▲) or deficit (▼) at a glance. Layout: `grid grid-cols-2 gap-x-6 gap-y-4 lg:grid-cols-5`.

**2. Funding Sources** — `FundingBar` component: stacked proportion bar (teal for grants, amber for self-generated) + two-column legend grid matching the ethnicity breakdown layout (colour dot, truncated label, right-aligned percentage, secondary amount). Built by `buildFundingMix()`.

**3. Where the Money Goes** — `SpendingBar` component: stacked proportion bar with up to 9 categories (8 named + "Other Costs" remainder) + two-column legend grid. Same layout as ethnicity and funding. Built by `buildSpendingBreakdown()`.

**4. Per-Pupil & Benchmarked** — 6 benchmarked cards in a standard `MetricGrid columns={3} mobileTwo`: Income/Pupil, Expenditure/Pupil, Staff Costs %, Revenue Reserve/Pupil, Teaching Staff Costs/Pupil, Supply Staff Costs Share. These receive benchmark bars (school / local / national) from the benchmark dashboard via `toBenchmarkSlot()`.

**Visual separation:** `border-t border-border-subtle/50 pt-5` dividers between subsections.

**Spending breakdown "Other Costs":** When known cost categories don't sum to total expenditure (common — the AAR has cost lines not surfaced individually), an "Other Costs" slice fills the remainder so the bar always reaches 100%.

**Negative currency formatting:** `formatMetricValue` in `metricCatalog.ts` uses `Math.abs()` for threshold comparison with a sign prefix, so `-276000` renders as `-£276k`.

---

### Chart colour palette (P15-UI, 2026-03-11)

A shared solid-colour palette used across all stacked bars and category breakdowns. Designed for high contrast on the dark navy canvas — no opacity variants.

| Index | Tailwind class | Hex | Role |
|---|---|---|---|
| 0 | `teal-400` | `#2dd4bf` | Primary / first category |
| 1 | `teal-600` | `#0d9488` | Secondary teal |
| 2 | `sky-400` | `#38bdf8` | Blue accent |
| 3 | `sky-600` | `#0284c7` | Darker blue |
| 4 | `violet-400` | `#a78bfa` | Purple |
| 5 | `amber-400` | `#fbbf24` | Warm accent |
| 6 | `rose-400` | `#fb7185` | Pink |
| 7 | `emerald-500` | `#22c55e` | Green |
| 8 | `gray-400` | `#9ca3af` | Neutral / "Other" |
| 9 | `purple-400` | `#c084fc` | Extended purple |
| 10 | `orange-400` | `#f97316` | Extended warm |
| 11 | `cyan-300` | `#67e8f9` | Extended cool |

**Used by:**
- `SchoolFinanceSection.tsx` — `CHART_COLORS` (hex, indices 0–8) and `FUNDING_HEX` (hex, teal-400 + amber-400)
- `EthnicityBreakdown.tsx` — `SEGMENT_COLORS` (hex, indices 0–11)

**Rule:** Never use opacity-based Tailwind colours (`bg-brand/40`, `bg-sky-500/15`) for chart segments — they vanish on the dark canvas. Always use full-opacity solid hex values from this palette.

### Stacked bar + legend pattern (P15-UI, 2026-03-11)

All proportion visualisations (ethnicity, funding sources, spending breakdown) share identical layout and hover behaviour:

**Layout:**
- Stacked bar: `flex h-3 overflow-hidden rounded-full`, segments sized by `width: ${pct}%`
- Legend: `grid grid-cols-1 gap-0.5 sm:grid-cols-2` — each row is colour dot (`h-2.5 w-2.5 rounded-full`) + truncated label (`truncate text-secondary`) + right-aligned percentage (`ml-auto tabular-nums font-medium text-primary`) + optional secondary value (`text-xs text-secondary`)

**Hover interaction (bidirectional):**
- Hovering a bar segment or legend row highlights that item and fades all others
- Bar segments: non-hovered fade to `opacity: 0.3`, `transition-opacity duration-150`
- Legend rows: active gets `bg-surface/50` highlight; non-hovered get `opacity-40` via Tailwind class
- State managed by `useState<string | null>` keyed on category label/group key

**Canonical implementations:**
- `EthnicityBreakdown.tsx` — `StackedBar` + `LegendRow` sub-components, `hoveredKey` state
- `SchoolFinanceSection.tsx` — `FundingBar` + `SpendingBar` components, `hovered` state

**Rule:** New proportion charts must follow this pattern. Do not use separate tooltip popovers or different fade values.

---

### Compare page — design system (P13.1–P13.5, 2026-03-10)

**Canonical location:** `src/features/school-compare/`

The Compare page uses the same Loira Voss design system as the school profile. Key components:

| Component | File | Role |
|---|---|---|
| `SchoolCompareFeature` | `SchoolCompareFeature.tsx` | Main page: data fetching, URL sync, layout orchestration |
| `CompareSchoolStrip` | `CompareSchoolStrip.tsx` | Fixed 4-slot strip: `FilledCard` for schools, `GhostCard` for empty slots |
| `CompareAccordionSections` | `CompareAccordionSections.tsx` | Collapsible accordion per section; first 3 default open |
| `CompareAccordionContent` | `CompareAccordionContent.tsx` | Metric rows inside each accordion: sticky label column + school cells |

**Accordion pattern:**
- Each section (Inspection, Demographics, Attendance, etc.) is a collapsible accordion
- First 3 sections default open; rest collapsed — reduces scroll fatigue
- Toggle button: `border-l-2 border-l-brand` full-opacity teal left accent bar, `text-base font-semibold`, `px-5 py-3.5` breathing room, `bg-brand/[0.04]` subtle teal-tinted glass
- Open state: `rounded-b-none border-b-transparent` with `p-1` padded content panel below
- Metric count badge (`text-[10px] text-disabled`) shown in each accordion header
- Hover: `hover:border-l-brand hover:border-brand/30` — accent bar intensifies

**"This school" highlight:**
- The first URN in the URL is treated as the origin school
- Its column gets `border-l-2 border-l-brand/30 bg-brand/[0.02]` on every cell + header

**Layout rules:**
- Metric label column: sticky `left-0`, 200px wide, `bg-surface/95 backdrop-blur`
- School columns: 180px min each, `overflow-x-auto` for horizontal scroll within each accordion
- Row padding: `py-3.5` with `border-b border-border-subtle/25` between rows
- Zebra striping: even rows get `bg-surface/[0.06]` (cells) / `bg-surface/[0.08]` (sticky label)
- Row hover: `hover:bg-surface/50` — visible neutral hover for tracking across columns
- Share button: copies current URL to clipboard with "Link copied" feedback

**Unavailable treatment:**
- Muted cells: `font-medium text-disabled/60` with em-dash prefix (`— Not applicable`)
- Detail labels: `text-disabled/70` (softer than secondary)
- Availability backgrounds: `unsupported` → `bg-surface/30`, `unavailable` → `bg-surface/20` (lighter than before)

**Premium gate:**
- Slim `Panel` banner with `Sparkles` icon, title, description, CTA button
- Dev premium bypass: inline `isDevUnlocked` check (same pattern as profile)

**Fixed 4-slot layout (P13.5):**
- Always render exactly 4 columns in both strip and accordion table, regardless of school count
- `padToSlots(schools)` pads the array with `null` to 4 entries; exported from `CompareSchoolStrip`
- `CompareSlot = CompareSchoolColumnVM | null` — shared type for both strip and accordion
- Empty slots: strip shows `GhostCard` (dashed border, `+ Add school` link), table shows blank cells
- `LABEL_COL_WIDTH = 200`, `SCHOOL_COL_WIDTH = 180`, `TOTAL_SLOTS = 4` — constants in strip and content

**School strip–table column alignment:**
- Strip uses the same column widths as accordion content: 200px label spacer + 180px per school
- Cards are compact: `p-2` padding, `text-xs` name, `text-[9px]` badges/URN/metadata
- Age range + distance rendered as inline `text-[9px]` text (no StatCard) to save height

**Mobile (< 640px / P13.8):**
- School strip: 2×2 grid (`grid-cols-2 gap-2`) replaces wide horizontal strip
- Inside each accordion: `CompareMobileContent` renders vertical stacked cards (metric label header → school value cards). Desktop table hidden via `hidden sm:block`
- Metric label: teal left accent bar (`border-l-2 border-l-brand/60`) above school cards
- School value cards: `rounded-lg bg-surface/60`, school name left + value right, origin school tinted
- Muted cells: `text-disabled/50` (lighter than desktop), detail labels suppressed for density
- Touch targets: remove button `p-1.5`, ghost card `min-h-[60px]`, accordion triggers already `min-h-[48px]`

**Desktop (≥ 640px):**
- School strip: `snap-x snap-mandatory scroll-smooth`, `snap-start` per card, aligned with table columns
- Inside each accordion: `overflow-x-auto` table with sticky metric label column
- Unit labels: `text-[10px]` compact size
