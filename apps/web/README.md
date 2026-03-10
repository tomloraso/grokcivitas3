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
