# P1 - Design Tokens: Benchmark Colour System

## Status

Not started

## Goal

Establish the three benchmark colour tokens — school, local, national — as CSS custom properties and Tailwind utility classes before any component references them. This is a zero-visual-change step.

## Files

- `apps/web/src/styles/tokens.css`
- `apps/web/tailwind.config.ts`

## Tokens Required

### Dark theme (`[data-theme="dark"]`)

```css
--color-benchmark-school:   var(--ref-color-brand-500);   /* #A855F7 purple  */
--color-benchmark-local:    var(--ref-color-accent-400);  /* #22d3ee cyan    */
--color-benchmark-national: var(--ref-color-success-500); /* #22c55e green   */
```

### Light theme (`[data-theme="light"]`)

```css
--color-benchmark-school:   var(--ref-color-brand-600);   /* #8B2FC9 purple  */
--color-benchmark-local:    var(--ref-color-accent-500);  /* #06b6d4 cyan    */
--color-benchmark-national: var(--ref-color-success-500); /* #22c55e green   */
```

### Tailwind aliases (tailwind.config.ts)

```ts
"benchmark-school":   "var(--color-benchmark-school)",
"benchmark-local":    "var(--color-benchmark-local)",
"benchmark-national": "var(--color-benchmark-national)",
```

## Acceptance Criteria

- [ ] Three tokens defined in both `[data-theme="dark"]` and `[data-theme="light"]` blocks.
- [ ] Three Tailwind color aliases added, usable as `bg-benchmark-school`, `text-benchmark-local`, etc.
- [ ] No visual change to any existing component.
- [ ] Lint passes.

## Rollback

```
git checkout -- apps/web/src/styles/tokens.css apps/web/tailwind.config.ts
```
