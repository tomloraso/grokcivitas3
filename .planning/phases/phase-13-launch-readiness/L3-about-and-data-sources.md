# L3 - About And Data Sources

## Document Control

- Status: Implemented
- Last updated: 2026-03-11
- Depends on:
  - `L1-content-page-foundation.md` (ContentPageLayout, PageMeta, prose styles, route paths)
  - `.planning/project-brief.md` (editorial stance and product positioning)

## Objective

Create the three user-facing content pages that establish trust and transparency: an About page explaining what Civitas is, a Data Sources page listing every data source and how it is used, and a Contact page for feedback and enquiries. These are the core credibility pages that any parent or researcher will look for before trusting the product.

## Scope

### In scope

- **About Civitas** page — product purpose, editorial stance, who it is for.
- **Data Sources and Methodology** page — every data source listed with its publisher, update cadence, and how Civitas uses it.
- **Contact and Feedback** page — how to reach the team, report data issues, or request features.
- Route registration, footer link activation, and PageMeta wiring for all three pages.

### Out of scope

- Legal pages (Privacy, Terms, Accessibility) — delivered in L4.
- CMS or dynamic content loading — page copy lives in component files.
- Backend API changes — none required.

## Decisions

1. **No CMS.** Content pages are React components with inline copy. The content is stable enough that a CMS adds unnecessary complexity. If content updates become frequent, MDX or a headless CMS can be evaluated later.
2. **Data Sources page references canonical source URLs.** Each data source entry links to the publisher's page so users can verify provenance independently.
3. **Contact page uses a mailto link**, not a contact form. A form requires backend work and spam protection; a simple email link is sufficient for launch. A form can be added in a later phase if volume warrants it.
4. **Editorial stance language follows the project brief.** Civitas presents facts without editorial commentary. The About page makes this explicit.
5. **Contact and operator details are configuration-backed.** Launch content can ship before the final brand/domain decision, but support emails and operator identity still need real production values before launch.

## Content Outline

### About Civitas

**Route:** `/about`

1. **What Civitas is.** A free, independent research tool for exploring English school data. Built for parents, researchers, and anyone interested in understanding schools in their area.
2. **What Civitas is not.** Civitas does not rank schools, make recommendations, or offer editorial opinions. All data is sourced from official public datasets and presented as-is with contextual benchmarks.
3. **How it works.** Data is collected from government and public sources, normalised into a consistent format, and presented through search, profiles, and comparison tools. Trends show change over time. Benchmarks compare a school against national or phase-level medians.
4. **Who built it.** Brief description of the team or individual behind Civitas. Keep factual and concise.
5. **Open data commitment.** All underlying data is publicly available. Civitas adds presentation, aggregation, and contextual comparison — not proprietary data.

### Data Sources And Methodology

**Route:** `/data-sources`

1. **Introduction.** Explain that all Civitas data comes from official public sources. List the update cadence (pipelines run on a defined schedule; data freshness is visible per source).

2. **Source table.** For each source:

| Source | Publisher | What Civitas uses it for | Update cadence |
|---|---|---|---|
| Get Information About Schools (GIAS) | DfE | School identity, location, type, phase, status, age range, contact details | Daily download |
| School Census / Characteristics | DfE Statistics | Pupil demographics — FSM, EAL, SEN, ethnicity, numbers on roll | Annual release |
| Ofsted Management Information | Ofsted | Latest inspection rating and date | Monthly release |
| Ofsted Inspection Reports Timeline | Ofsted | Full inspection history per school | Monthly release |
| Indices of Multiple Deprivation (IMD) | ONS | Area deprivation context by LSOA | Periodic release |
| Police UK Street-Level Crime | Police UK | Local crime context by location | Monthly release |
| Key Stage Results (Performance) | DfE Statistics | KS2/KS4 attainment and progress measures | Annual release |
| School Workforce Census | DfE Statistics | Teacher count, pupil-teacher ratio, teacher turnover | Annual release |
| Attendance Statistics | DfE Statistics | Overall, persistent, and severe absence rates | Termly/annual release |
| Behaviour and Exclusions | DfE Statistics | Suspensions and permanent exclusions | Annual release |
| UK House Price Index | ONS / Land Registry | Median house prices for area context | Monthly release |

3. **Methodology notes.**
   - Benchmarks are calculated as national or phase-level medians from the full dataset. They are not editorial judgements.
   - Trends require at least two data points. Where a school has fewer, the trend chart is suppressed and a completeness notice is shown.
   - Data completeness signals are displayed per metric. If a source has not published data for a given year, Civitas shows a "not reported" indicator rather than hiding the metric.

4. **Data freshness.** Explain that each pipeline tracks when data was last ingested and that the profile page shows per-section freshness where available.

### Contact And Feedback

**Route:** `/contact`

1. **General enquiries.** Email address for questions about Civitas.
2. **Data corrections.** If a user believes data shown is incorrect, direct them to check the original source first (linked from Data Sources page), then report discrepancies via email.
3. **Feature requests and feedback.** Encourage users to share what they would find useful.
4. **Response time.** Set expectations — "We read every message. Response times vary."

## Frontend Design

Each page uses `ContentPageLayout` from L1:

```text
<ContentPageLayout
  title="About Civitas"
  metaDescription="Civitas is a free research tool for exploring English school data. Built on official public datasets, presented without editorial commentary."
>
  {/* page content */}
</ContentPageLayout>
```

The Data Sources page includes a styled `<table>` or definition list. Use the existing table styles from the compare page if appropriate, or define a simple prose-compatible table style in `prose.css`.

### PageMeta values

| Route | Title | Description |
|---|---|---|
| `/about` | About Civitas | Civitas is a free, independent research tool for exploring English school data — demographics, trends, Ofsted, and area context. |
| `/data-sources` | Data Sources and Methodology | Every data source Civitas uses, where it comes from, and how it is processed. |
| `/contact` | Contact and Feedback | Get in touch with the Civitas team — questions, data corrections, or feature requests. |

## File-Oriented Implementation Plan

1. `apps/web/src/pages/AboutPage.tsx` (new)
   - About Civitas content in `ContentPageLayout`.

2. `apps/web/src/pages/DataSourcesPage.tsx` (new)
   - Source table and methodology notes in `ContentPageLayout`.

3. `apps/web/src/pages/ContactPage.tsx` (new)
   - Contact information and feedback guidance in `ContentPageLayout`.

4. `apps/web/src/app/routes.tsx`
   - Register `/about`, `/data-sources`, `/contact` routes importing the new page components.

5. `apps/web/src/components/layout/SiteFooter.tsx`
   - Confirm About and Contact footer links now point to real paths (initial wiring done in L1; verify after page creation).

6. `apps/web/src/pages/about-page.test.tsx` (new)
   - Renders heading and key content sections.
   - PageMeta sets correct title and description.

7. `apps/web/src/pages/data-sources-page.test.tsx` (new)
   - Renders source table with expected source names.
   - PageMeta sets correct title and description.

8. `apps/web/src/pages/contact-page.test.tsx` (new)
   - Renders email link.
   - PageMeta sets correct title and description.

## Testing And Quality Gates

### Required tests

- Each page renders its heading and primary content.
- Each page sets the correct document `<title>` via `PageMeta`.
- Data Sources table includes all sources from the source table above.
- Contact page renders a working `mailto:` link.
- Pages render correctly in both dark and light themes.

### Quality gate

- `make lint` passes.
- `make test` passes.
- `cd apps/web && npm run build` passes.
- No layout regression at 375px mobile width.

## Acceptance Criteria

- `/about`, `/data-sources`, and `/contact` routes render full content.
- Footer links for About and Contact navigate to the correct pages.
- Data Sources page lists every source from the source table with links to the original publisher.
- All three pages use `ContentPageLayout` and have correct PageMeta (title, description, and canonical path from L2 where applicable).
- Content is readable and well-formatted in both themes.

## Rollback

Per-file: `git checkout -- <file>`
