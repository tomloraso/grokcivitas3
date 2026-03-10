# Design System & UX Guide

This document codifies every site-wide visual and interaction standard. All agents building pages, features, or data visualisations must follow these rules.

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

**Critical rule: trend indicators are always teal, never red/green.** Direction triangles (▲/▼) use `text-brand` regardless of whether the direction is conventionally "good" or "bad". The platform presents facts, not judgements.

---

## Typography

- **Font family:** Inter (all weights) via `@fontsource/inter`, fallback `system-ui, sans-serif`
- **Display headings:** `font-display font-semibold tracking-tight`
- **Metric numbers:** `font-bold text-3xl sm:text-4xl` (hero: `text-4xl sm:text-5xl`)
- **Body / labels:** `text-sm leading-relaxed`
- **Title Case rule:** All section headings and StatCard labels use Title Case (e.g. "Free School Meals", not "FREE SCHOOL MEALS"). Never use `text-transform: uppercase`.

---

## Button System (`src/components/ui/Button.tsx`)

shadcn/ui `cva`-based button with unified micro-animation on every variant.

**Base animation:** `transition-all duration-200 ease-out hover:scale-[1.02] active:scale-[0.98]`

| Variant | Use case | Visual |
|---------|----------|--------|
| `primary` | Main CTAs: "Add to compare", "Open compare", "Browse schools" | Solid teal fill (`bg-brand-solid`) |
| `secondary` | Secondary actions: "Remove", "Save for later", "Share", "Back to search" | Outline with subtle border (`border-border bg-elevated`) |
| `ghost` | Tertiary / destructive: "Clear all" | Transparent, text-only hover |
| `compare` | Reserved — glass-card look for specialised compare contexts | Backdrop-blur glass with teal border accents |

**Sizes:** `default` (h-11 px-4 text-sm), `sm` (h-9 px-3 text-xs), `none` (no sizing).

**Rules:**
- Always use the shadcn `Button` — no raw `<button>` for action buttons.
- Never add inline `hover:scale` or `transition-all` overrides; the cva base handles all animation.
- Mobile sticky bars use `min-h-[52px]` touch targets.

---

## Card Primitive (`src/components/ui/Card.tsx`)

`panel-surface rounded-xl` + `hover:-translate-y-0.5 hover:shadow-lg transition-all duration-200`

`panel-surface` is a CSS utility in `theme.css`: glass gradient background, 1px border at `--color-border-default`, `backdrop-filter: blur(18px)`.

---

## StatCard Primitive (`src/components/ui/stat-card.tsx`)

The single source of truth for all numeric stat display. Uses `cva` for variant and size control.

### Variants

| Variant | When to use | Chrome |
|---|---|---|
| `default` | Standalone metric in a `MetricGrid` | `Card` wrapper, `p-4 sm:p-5`, hover lift |
| `hero` | Most important metric in a section | `Card` + teal glow border |
| `mini` | Embedded inside an existing section card | Plain `div`, zero padding, zero border |

**Rule: never use `variant="default"` or `variant="hero"` inside another `Card`. Always use `variant="mini"` for nested stats.**

### Size prop

| Size | `default`/`hero` value | `mini` value |
|---|---|---|
| `sm` | `text-2xl sm:text-3xl` | `text-xl` |
| `md` _(default)_ | `text-3xl sm:text-4xl` | `text-2xl` |
| `lg` | `text-4xl sm:text-5xl` | `text-2xl sm:text-3xl` |

### Benchmark delta neutrality

Regional and national delta values always render in neutral gray (`#94A3B8`) — never conditionally coloured by sign.

### Title min-height

Label container has `min-h-[40px]` so values align across grid rows regardless of title wrap.

---

## Trend Indicators (`src/components/data/TrendIndicator.tsx`)

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

## Layout Patterns

### Mobile-First (375px baseline)

Every page and component starts at 375px. Key breakpoints:
- `sm` (640px): Switch from stacked to horizontal layouts
- `lg` (1024px): Add sidebar/multi-column layouts
- `xl` (1280px): Max content width

### School Profile Layout

**Mobile (`< 1024px`):**
- Single column, full-width cards, 24px internal padding
- Sections collapse into accordions; Ofsted and Results & Progress default open
- Sticky action bar at bottom: `min-h-[52px]`, `env(safe-area-inset-bottom)` padding

**Desktop (`≥ 1024px`):**
- Two-column grid: 280px sticky TOC sidebar + flexible main content
- TOC: `position: sticky; top: 3.75rem`
- Max width: 1280px centred via `PageContainer`

### Compare Page Layout

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

---

## Premium Access Gates

- Locked sections show a slim `Panel` banner with `Sparkles` icon, title, description, CTA
- SaveSchoolButton: Heart icon, tooltip on hover, status-aware label ("Save for later" / "Saved" / "Sign in to save" / "Unlock save")
- Unauthenticated users redirected to sign-in; locked users redirected to upgrade

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
