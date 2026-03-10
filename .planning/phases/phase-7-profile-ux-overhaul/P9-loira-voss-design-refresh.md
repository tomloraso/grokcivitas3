# P9 — Loira Voss Design Refresh (2026-03-09)

## Status: Complete — superseded by P10 for StatCard standardisation

## Iteration log

### Iteration 10 (2026-03-09) — shadcn StatCard standardisation (P10)
See `P10-statcard-shadcn-standardisation.md` for full detail. Summary:
- **`components/ui/stat-card.tsx`** (new) — canonical shadcn-style primitive with `cva` variants (`default`, `hero`, `mini`), `size` prop (`sm`/`md`/`lg`), built-in overflow protection (`min-w-0 leading-tight` labels, `tabular-nums break-all` values, `overflow-hidden` wrapper), and `tooltip`/`description` info button.
- **`components/data/StatCard.tsx`** — converted to a re-export shim. Existing section components continue to work without modification.
- **`NeighbourhoodSection.tsx`** — migrated from raw `div` inline stats to `<StatCard variant="mini" size="sm">`, resolving the double-padding root cause for all nested stats.
- **`apps/web/README.md`** — full StatCard design system rule section added (P10).
- **Root `README.md`** — frontend component inventory table added.

### Iteration 9 (2026-03-09) — Neighbourhood mini-stat unified sizing
- **`NeighbourhoodSection.tsx`** — All four mini-stat cards standardised to `valueClassName="text-lg sm:text-xl"`: Incidents (`text-xl sm:text-2xl` → `text-lg sm:text-xl`), Per 1,000 (same), Average Price (`text-2xl sm:text-3xl` → `text-lg sm:text-xl`), Annual Change (no override → `text-lg sm:text-xl`).

### Iteration 8 (2026-03-09) — Area Crime mini-stat final sizing
- **`NeighbourhoodSection.tsx`** — Incidents and Per 1,000 `valueClassName` reduced from `text-2xl sm:text-3xl` → `text-xl sm:text-2xl`. Values now sit comfortably with generous padding inside the narrow 2-col Crime grid.

### Iteration 7 (2026-03-09) — Area Crime mini-stat sizing
- **`NeighbourhoodSection.tsx`** — Incidents and Per 1,000 `StatCard`s get `valueClassName="text-2xl sm:text-3xl"` to prevent oversized numbers cramping the narrow 2-col Crime grid.

### Iteration 6 (2026-03-09) — neighbourhood desktop polish
- **`StatCard.tsx`** — added `valueClassName?: string` prop; applied via `cn()` on the value `<span>` to allow per-card font-size overrides without breaking the default variant system.
- **`NeighbourhoodSection.tsx`** — Average Price `StatCard` gets `valueClassName="text-2xl sm:text-3xl"` (fixes `£306k` clip inside narrow 2-col grid); neighbourhood grid gets `xl:items-stretch` for perfect 3-card bottom alignment.

### Iteration 5 (2026-03-09) — sparkline overflow fix
- **`Sparkline.tsx`** — all three SVG render paths changed from `width={px}` to `width="100%"` + `preserveAspectRatio="none"` + `className="block"`. The `width` prop is now viewBox coordinate space only.
- **`NeighbourhoodSection.tsx`** — both `<Sparkline>` call sites (Crime + House Prices): removed `width={220}`, added `className="w-full"`, added `overflow-hidden` to each container div.

### Iteration 4 (2026-03-09) — benchmark bars on mobile
- **`StatCard.tsx`** — removed the `hidden sm:block` / `sm:hidden` split in `BenchmarkBlock`. Replaced with a single unified `BarRow` path visible at all breakpoints. Bar height is `h-2` (8px) on mobile, `h-[5px]` on `sm+`. `TextRow` component deleted. No changes to colours, widths, delta formatting, or desktop layout.

### Iteration 3 (2026-03-09) — mobile density
See Phase 7 README tracking log.

### Iteration 2 (2026-03-09) — post-review fixes
- **Removed `UKMapWatermark`** from `ProfileHeader.tsx` — the simplified SVG path rendered as an unrecognisable flame/wave shape rather than a UK silhouette. Hero is now illustration-free; this is now a design rule (see `apps/web/README.md`).
- **`SiteFooter.tsx`** — both `CIVITAS` occurrences replaced with `[BRAND]` (logo link + copyright line).
- **`SchoolProfileFeature.tsx`** — 30-line styling comment block added at file top; TOC sticky position corrected to `top-[3.75rem]` + `self-start`; mobile CTA hardened with `min-h-[52px]` and `env(safe-area-inset-bottom)` iOS safe-area padding.
- **`apps/web/README.md`** — `## School Profile UI` section added.
- **Phase 7 `README.md`** — deliverable table updated, tracking log extended, "What Is Not Changing" corrected to reflect brand/font migration.

### Iteration 1 (2026-03-09) — initial implementation
See original scope below.

## Scope

A second full design pass over the school profile page, extending the Phase 7 work. Delivered as a designer prompt from Loira Voss.

## Changes

### Global design-token changes (affect whole app via CSS variables)

| Token | Before | After |
|---|---|---|
| `--ref-color-brand-500` | `#A855F7` (purple) | `#00D4C8` (teal) |
| `--ref-color-brand-400` | `#C084FC` | `#33DDD8` |
| `--ref-color-brand-600` | `#8B2FC9` | `#00A89D` |
| `--ref-color-navy-900` | `#0c1222` | `#0A1428` |
| `--ref-color-navy-950` | `#060a13` | `#02060F` |
| `--ref-color-navy-800` | `#141d30` | `#0F172A` |
| `--color-trend-up` (dark) | `--ref-color-info-500` (blue) | `#00D4C8` (teal) |
| `--color-trend-down` (dark) | `--ref-color-info-500` (blue) | `#FF4D6D` (red) |
| `--font-family-display` | `Space Grotesk` | `Inter` |
| `--font-family-body` | `Public Sans` | `Inter` |

### Font

Add `@fontsource/inter` to apps/web. Import weights 400, 500, 600 in theme.css.

### Component changes

- **SiteHeader**: "CIVITAS" → "[BRAND]" (display text + aria-label)
- **Card**: `rounded-lg` → `rounded-xl`, add `hover:-translate-y-0.5 hover:shadow-lg transition-all duration-200`
- **ProfileHeader**: Add subtle UK map outline SVG watermark (10% opacity) behind the hero section

### School profile layout (SchoolProfileFeature)

- **Desktop (lg+)**: Two-column layout — 280px sticky Table of Contents sidebar + main content area (max-w-5xl)
- **Mobile**: Sections 3–8 (Ofsted through Neighbourhood) rendered as collapsible accordions. Ofsted Profile and Results & Progress default open. All others default closed.
- **Mobile sticky CTA bar**: Fixed bottom bar with "Add to compare" / "Remove from compare" button, teal background, full width. Hidden on lg+.
- **Section IDs**: Each section wrapped in a `<div id="...">` for TOC jump-link targets.

### New component

`apps/web/src/features/school-profile/components/ProfileSectionAccordion.tsx` — lightweight React-state accordion for mobile section collapsing. No new package dependency (uses `useState` + CSS transitions).

## What is NOT changing

- All API contracts and data connections — zero backend changes
- TypeScript interfaces — unchanged
- Compare flow, auth, map page — unaffected
- Light theme — kept as-is; teal brand works in both themes
- Accessibility — ARIA labels updated to match [BRAND], accordion uses `aria-expanded`

## Files touched

- `.planning/phases/phase-7-profile-ux-overhaul/P9-loira-voss-design-refresh.md` (this file)
- `apps/web/package.json` + `package-lock.json` (@fontsource/inter added)
- `apps/web/src/styles/tokens.css`
- `apps/web/src/styles/theme.css`
- `apps/web/src/components/layout/SiteHeader.tsx`
- `apps/web/src/components/ui/Card.tsx`
- `apps/web/src/features/school-profile/components/ProfileHeader.tsx`
- `apps/web/src/features/school-profile/components/ProfileSectionAccordion.tsx` (new)
- `apps/web/src/features/school-profile/SchoolProfileFeature.tsx`
