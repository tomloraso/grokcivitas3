/**
 * Map color tokens for MapLibre GL paint properties.
 *
 * MapLibre layers render via WebGL and cannot read CSS custom properties.
 * This module mirrors the CSS design tokens from `tokens.css` as plain
 * JS constants so map Layer paint values stay in sync with the system.
 *
 * IMPORTANT: If you change a value here, update the matching CSS custom
 * property in `src/styles/tokens.css` (and vice-versa).
 */

/* ------------------------------------------------------------------ */
/* Reference palette (mirrors --ref-color-* in tokens.css)             */
/* ------------------------------------------------------------------ */

const ref = {
  navy950: "#060a13",
  navy900: "#0c1222",
  brand500: "#A855F7",
  phaseSecondary: "#E879F9",
  success500: "#22c55e",
  info500: "#3b82f6",
  warning500: "#f59e0b",
  danger500: "#ef4444",
} as const;

/* ------------------------------------------------------------------ */
/* Semantic map tokens                                                  */
/* ------------------------------------------------------------------ */

/** Brand accent used for search radius, clusters, default markers. */
export const MAP_BRAND = ref.brand500;

/** Stroke / border colour matching the land background. */
export const MAP_BG = ref.navy950;

/** White — used for cluster count text on brand-filled circles. */
export const MAP_TEXT_ON_BRAND = "#ffffff";

/* ------------------------------------------------------------------ */
/* Ofsted rating palette                                               */
/* ------------------------------------------------------------------ */

export const OFSTED_COLORS = {
  Outstanding: ref.success500,
  Good: ref.info500,
  "Requires Improvement": ref.warning500,
  Inadequate: ref.danger500,
} as const;

/* ------------------------------------------------------------------ */
/* School phase palette                                                */
/* ------------------------------------------------------------------ */

export const PHASE_COLORS = {
  Primary: ref.brand500,
  Secondary: ref.phaseSecondary,
} as const;

/* ------------------------------------------------------------------ */
/* Convenience: resolve a marker colour from rating → phase → fallback */
/* ------------------------------------------------------------------ */

export function markerColor(
  ofstedRating: string | undefined | null,
  phase: string | undefined | null,
): string {
  if (ofstedRating && ofstedRating in OFSTED_COLORS) {
    return OFSTED_COLORS[ofstedRating as keyof typeof OFSTED_COLORS];
  }
  if (phase && phase in PHASE_COLORS) {
    return PHASE_COLORS[phase as keyof typeof PHASE_COLORS];
  }
  return MAP_BRAND;
}
