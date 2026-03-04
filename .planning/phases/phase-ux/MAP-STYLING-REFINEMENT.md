# Map Styling Refinement Guide

> Production-grade aesthetic direction for the Civitas MapLibre dark basemap.
> Companion to UX-1 (map migration) and UX-2 (interaction depth).

## Document Control

- Status: Complete
- Last updated: 2026-03-03
- Depends on:
  - `.planning/phases/phase-ux/UX-1-maplibre-migration-uk-bounds-landing-state.md`
  - `.planning/phases/phase-ux/UX-2-map-interaction-depth.md`
  - `apps/web/src/styles/tokens.css`

---

## 1. Basemap Palette Refinement

### Design Philosophy

The current style uses `#0b1221` for background and `#141e30` for water — both within the navy family but slightly too blue-saturated, creating a faint "glow" effect on retina screens. The refinement shifts toward **desaturated charcoal-navy** — still firmly dark, but calmer. The key insight: reduce blue channel saturation by ~15% across all base fills so the map reads as a sophisticated neutral canvas rather than a blue-tinted screen.

### Refined Palette

| Feature | Current | Refined | Delta | Rationale |
|---|---|---|---|---|
| **Background (land)** | `#0b1221` | `#080d19` | Darker, less blue | Deeper recession. Screen won't feel "lit" at night. |
| **Water fill** | `#141e30` | `#0c1424` | Tighter gap to land | Water distinguishable by geometry alone, not colour pop. |
| **Water (line features)** | `rgb(27,27,29)` | `#101828` | Navy-aligned | Canals/rivers read as subtle navy lines, not grey. |
| **Landuse residential** | `#101726` @ 0.4 | `#0e1420` @ 0.25 | Lower opacity | Residential zones as whisper-level tonal shift. |
| **Landuse park** | `#101726` | `#0c1222` @ 0.6 | Per UX-1 spec | Parks exist but do not compete. |
| **Landcover wood** | `rgb(32,32,32)` | `#0e1420` @ 0.5 | Navy-aligned | Eliminate grey/neutral woodland. Integrate into navy. |
| **Ice shelf / glacier** | `rgb(12,12,12)` | `#0a0f1a` | Navy-tinted | Even polar features belong to the navy world. |
| **Building fill** | `rgb(10,10,10)` | `#0e1420` | Navy-800 | Flat navy polygons, not pure black. |
| **Building outline** | `rgb(27,27,29)` | **none** | Removed | Per UX-1 anti-pattern: "No outlines. Buildings are mass, not wireframe." |

### Depth Without Noise Techniques

1. **Tonal stepping, not colour variation.** Every feature lives in the HSL range `H: 218–225°, S: 25–40%, L: 3–12%`. Depth comes from lightness steps alone.
2. **Opacity as the primary depth tool.** Rather than picking distinct hex values, use the same base navy at different opacities. This guarantees palette cohesion.
3. **No raster natural-earth shading at z0–6.** The `ne2_shaded` raster source introduces photographic texture that breaks the flat aesthetic. Remove it or set layer opacity to 0.
4. **Water gets anti-alias disabled.** Crisp polygon edges read as coastline without needing a stroke. Already correctly set.

---

## 2. Label Styling

### The Problem

Every label layer currently uses the same `rgb(101,101,101)` colour and `rgba(0,0,0,0.7)` halo. This creates a flat, undifferentiated text layer — no hierarchy, no editorial rhythm.

### Refined Hierarchy

| Label Class | Text Colour | Opacity | Size | Halo | Letter Spacing | Weight |
|---|---|---|---|---|---|---|
| **Country (major)** | `#94a3b8` (grey-400) | 0.75 | z0: 10 → z4: 14 | `#080d19` @ 0.9, width 1.6 | `0.12em` | Regular |
| **Country (minor)** | `#94a3b8` | 0.65 | z0: 9 → z6: 12 | `#080d19` @ 0.9, width 1.4 | `0.10em` | Regular |
| **State / region** | `#64748b` (grey-500) | 0.55 | 10 | `#080d19` @ 0.85, width 1.2 | `0.10em` | Regular |
| **City (large, rank≤3)** | `#94a3b8` | 0.70 | 13 | `#080d19` @ 0.9, width 1.4 | `0.08em` | Regular |
| **City (other)** | `#7b8ba3` | 0.60 | 10 | `#080d19` @ 0.85, width 1.2 | `0.08em` | Regular |
| **Town** | `#64748b` | 0.50 | 10 | `#080d19` @ 0.8, width 1.0 | `0.06em` | Regular |
| **Village / suburb** | `#506078` | 0.40 | 9 | `#080d19` @ 0.8, width 1.0 | `0.06em` | Regular |
| **Hamlet / neighbourhood** | `#506078` | 0.35 | 9 | `#080d19` @ 0.75, width 0.8 | `0.04em` | Regular |
| **Water name** | `#3a4f6e` | 0.45 | 11, italic feel via spacing | `#080d19` @ 0.6, width 0.8 | `0.14em` | Regular |
| **Road name (other)** | `#506078` | 0.45 | 9 | `#080d19` @ 0.9, width 1.0 | `0.06em` | Regular |
| **Road name (motorway)** | `#64748b` | 0.40 | 9 | `#080d19` @ 0.8, width 0.8 | `0.04em` | Regular |

### Key Label Rules

1. **Navy-matched halos only.** Every halo uses `#080d19` (background colour) at high opacity. Never black (`#000`), never grey. This makes text "cut through" the map without a visible halo ring.
2. **No `text-halo-blur`.** Blur creates a glow effect that reads as unintentional. Crisp `0` blur, wider width.
3. **Progressive dimming.** Lower-importance labels get lower opacity AND a desaturated colour shift. The eye naturally gravitates to the brighter country labels.
4. **All uppercase.** Consistent with the app's mono-label treatment per UX-1 spec.
5. **`text-letter-spacing`** creates the editorial feel. Country names at `0.12em` read as headlines.
6. **Aggressive collision avoidance.** Use `text-allow-overlap: false` and `text-optional: true` to auto-hide lower priority labels when space is tight.

---

## 3. Data Layer Styling

### Marker Colour Recommendation

Your current implementation uses `#8b5cf6` (brand-500 violet) — **which is excellent.** The UX-1 spec designates this as "the only saturated element on the entire map" and this is the correct choice for your humanitarian data context. Violet-purple communicates:

- Seriousness without aggression (unlike red/orange)
- Distinction from every basemap feature (no purple exists in the navy palette)
- Accessibility — high WCAG contrast against dark backgrounds

**Do not switch to orange.** Orange is commonly associated with warning states in your token system (`--ref-color-warning-500: #f59e0b`), and on a dark map it can read as "alert" or "danger" rather than "data point". The violet brand colour is the right call.

### Unclustered Point Markers (Layer-Based Alternative)

For render performance at scale, consider a purely layer-based `circle` type for unclustered points instead of DOM markers:

```json
{
  "id": "school-points",
  "type": "circle",
  "source": "school-markers",
  "filter": ["!", ["has", "point_count"]],
  "paint": {
    "circle-radius": [
      "interpolate", ["linear"], ["zoom"],
      8, 4,
      12, 6,
      15, 8
    ],
    "circle-color": "#8b5cf6",
    "circle-opacity": 0.9,
    "circle-stroke-width": 1.5,
    "circle-stroke-color": "#080d19",
    "circle-blur": 0.15
  }
}
```

### Hover / Active State Treatments

Use MapLibre feature-state for interactive styling without re-rendering:

```json
{
  "circle-radius": [
    "case",
    ["boolean", ["feature-state", "active"], false], 10,
    ["boolean", ["feature-state", "hover"], false], 9,
    7
  ],
  "circle-color": [
    "case",
    ["boolean", ["feature-state", "active"], false], "#a78bfa",
    "#8b5cf6"
  ],
  "circle-stroke-width": [
    "case",
    ["boolean", ["feature-state", "active"], false], 2.5,
    ["boolean", ["feature-state", "hover"], false], 2,
    1.5
  ],
  "circle-stroke-color": [
    "case",
    ["boolean", ["feature-state", "active"], false], "rgba(167, 139, 250, 0.4)",
    "#080d19"
  ]
}
```

### Cluster Styling

```json
{
  "id": "clusters",
  "type": "circle",
  "filter": ["has", "point_count"],
  "paint": {
    "circle-color": [
      "step", ["get", "point_count"],
      "#7c3aed",
      10, "#6d28d9",
      50, "#5b21b6"
    ],
    "circle-radius": [
      "step", ["get", "point_count"],
      14,
      10, 18,
      50, 24
    ],
    "circle-stroke-width": 2,
    "circle-stroke-color": "#080d19",
    "circle-opacity": 0.92
  }
}
```

Clusters use progressively deeper violet as density increases. This communicates "weight" without introducing new hues.

### Handling Overlapping Circles

1. **Slight opacity reduction** (0.85–0.9) allows overlapping circles to show density through additive blending on the GPU.
2. **`circle-sort-key`** ordered by a data property (e.g. rating priority) ensures important markers render on top.
3. **Clustering is the primary mechanism** — at low zoom overlaps are handled by clusters; at high zoom (z14+) physical separation mostly eliminates the problem.

### Radius Overlay Refinement

```json
{
  "id": "search-radius-fill",
  "type": "fill",
  "paint": {
    "fill-color": "#8b5cf6",
    "fill-opacity": 0.04
  }
},
{
  "id": "search-radius-line",
  "type": "line",
  "paint": {
    "line-color": "#8b5cf6",
    "line-opacity": 0.15,
    "line-width": 1,
    "line-dasharray": [6, 4]
  }
}
```

Subtler than current (opacity 0.05/0.2). The radius should be a whisper, not a boundary.

---

## 4. Visual Hierarchy Strategy

### The Three-Layer Model

```
Layer 0 — Canvas (land, water)     → L: 3–5%   | Nearly invisible
Layer 1 — Structure (roads, admin) → L: 8–14%  | Ghost lines emerge
Layer 2 — Data (markers, radius)   → S: 70%+   | The only saturated elements
```

The basemap serves as a **precision substrate** — it provides geographic context through subtle structural cues (road network, coastline shape, boundary positions) without ever competing for visual attention. Data markers are the *only* elements that break out of the monochrome navy field.

### Subtle Glow Technique (MapLibre-Compatible)

MapLibre doesn't support CSS `box-shadow` on layer features, but you can achieve a glow effect using stacked circle layers:

```json
[
  {
    "id": "school-points-glow",
    "type": "circle",
    "source": "school-markers",
    "filter": ["!", ["has", "point_count"]],
    "paint": {
      "circle-radius": [
        "interpolate", ["linear"], ["zoom"],
        8, 12, 12, 18, 15, 22
      ],
      "circle-color": "#8b5cf6",
      "circle-opacity": 0.08,
      "circle-blur": 1
    }
  },
  {
    "id": "school-points",
    "type": "circle",
    "source": "school-markers",
    "filter": ["!", ["has", "point_count"]],
    "paint": {
      "circle-radius": [
        "interpolate", ["linear"], ["zoom"],
        8, 4, 12, 6, 15, 8
      ],
      "circle-color": "#8b5cf6",
      "circle-opacity": 0.9,
      "circle-stroke-width": 1.5,
      "circle-stroke-color": "#080d19"
    }
  }
]
```

The first layer is a large, fully blurred, low-opacity circle that creates an ambient "light emission" effect. The second layer is the crisp data point.

### Boundary Line Refinement

Boundaries should be nearly invisible — context, not content:

```json
{
  "line-color": "#1c2840",
  "line-opacity": 0.25,
  "line-width": ["interpolate", ["exponential", 1.1], ["zoom"], 3, 0.5, 12, 1.5],
  "line-dasharray": [3, 2],
  "line-blur": 0.5
}
```

### Road Hierarchy Depth

```
Motorway  → #1c2840 @ 0.7 opacity, width 1–4px by zoom
A-road    → #141d30 @ 0.55 opacity, width 0.5–2px by zoom
Minor     → #101828 @ 0.35 opacity, width 0.5–1.5px by zoom
Path      → #101828 @ 0.25 opacity, dashed
```

These are deliberately thin and low-contrast. Roads create a "mesh" texture that provides orientation without drawing the eye.

---

## 5. Road Casing — Remove

The current style includes `highway_major_casing` and `highway_motorway_casing` layers — these create the double-stroke road effect explicitly prohibited by the UX-1 spec. Set their visibility to `"none"` or remove them.

---

## 6. Implementation Audit — Current vs. Refined

| Issue | Severity | Fix |
|---|---|---|
| Background too blue (`#0b1221` vs `#080d19`) | Low | Update paint |
| Water too bright (`#141e30` vs `#0c1424`) | Low | Update paint |
| Road casings present (anti-pattern) | Medium | Set visibility none |
| Building has outline-color (anti-pattern) | Medium | Remove outline |
| All labels same colour (`rgb(101,101,101)`) | High | Apply hierarchy |
| Label halos use black not navy | Medium | Use `#080d19` halos |
| Label `text-halo-blur: 1` on many layers | Medium | Set to 0 |
| Water name labels nearly invisible (`hsla(0,0%,0%,0.7)`) | Medium | Fix colour |
| Wood/landcover uses grey, not navy | Low | Align to navy |
| Motorway inner too bright (`#475569`) | Medium | Tone down to `#1c2840` at 0.7 |
| Highway minor at 0.9 opacity (too prominent) | Medium | Reduce to 0.35 |
| No letter-spacing on labels | Low | Add per hierarchy |
| `ne2_shaded` raster may break flat aesthetic | Low | Consider removing |

---

## 7. Complete MapLibre Paint/Layout Snippets

These are production-ready snippets aligned with the MapLibre Style Specification.

### Background
```json
{ "background-color": "#080d19" }
```

### Water Fill
```json
{ "fill-antialias": false, "fill-color": "#0c1424" }
```

### Building (z15+)
```json
{
  "fill-antialias": true,
  "fill-color": "#0e1420"
}
```
No `fill-outline-color`. Buildings are mass.

### Motorway (single line, no casing)
```json
{
  "line-color": "#1c2840",
  "line-opacity": 0.7,
  "line-width": ["interpolate", ["exponential", 1.4], ["zoom"], 5, 0.5, 8, 1, 14, 3, 20, 12]
}
```

### Country Label (major)
```json
{
  "layout": {
    "text-font": ["Noto Sans Regular"],
    "text-size": ["interpolate", ["exponential", 1.4], ["zoom"], 0, 10, 3, 12, 4, 14],
    "text-transform": "uppercase",
    "text-letter-spacing": 0.12,
    "text-allow-overlap": false
  },
  "paint": {
    "text-color": "rgba(148, 163, 184, 0.75)",
    "text-halo-color": "rgba(8, 13, 25, 0.9)",
    "text-halo-width": 1.6,
    "text-halo-blur": 0
  }
}
```

### City Label (large)
```json
{
  "layout": {
    "text-font": ["Noto Sans Regular"],
    "text-size": 13,
    "text-transform": "uppercase",
    "text-letter-spacing": 0.08,
    "text-allow-overlap": false,
    "text-optional": true
  },
  "paint": {
    "text-color": "rgba(148, 163, 184, 0.70)",
    "text-halo-color": "rgba(8, 13, 25, 0.9)",
    "text-halo-width": 1.4,
    "text-halo-blur": 0
  }
}
```

### Town / Village Label
```json
{
  "layout": {
    "text-font": ["Noto Sans Regular"],
    "text-size": 10,
    "text-transform": "uppercase",
    "text-letter-spacing": 0.06,
    "text-allow-overlap": false,
    "text-optional": true
  },
  "paint": {
    "text-color": "rgba(80, 96, 120, 0.45)",
    "text-halo-color": "rgba(8, 13, 25, 0.8)",
    "text-halo-width": 1.0,
    "text-halo-blur": 0
  }
}
```

### Boundary (country, z5+)
```json
{
  "line-color": "#1c2840",
  "line-opacity": 0.25,
  "line-width": ["interpolate", ["exponential", 1.1], ["zoom"], 3, 0.5, 12, 1.5],
  "line-blur": 0.5
}
```

### Boundary (state/admin4)
```json
{
  "line-color": "#1c2840",
  "line-opacity": 0.18,
  "line-dasharray": [3, 2],
  "line-width": ["interpolate", ["exponential", 1.1], ["zoom"], 3, 0.3, 12, 1],
  "line-blur": 0.4
}
```

---

## 8. Ofsted Rating Colour Encoding on Markers

When markers encode Ofsted ratings, use muted variants of semantic colours that harmonize with the violet brand:

| Rating | Hex | Note |
|---|---|---|
| Outstanding | `#10b981` (emerald-500) | Green — positive semantic |
| Good | `#3b82f6` (blue-500) | Blue — stable semantic |
| Requires Improvement | `#f59e0b` (amber-500) | Amber — caution semantic |
| Inadequate | `#ef4444` (red-500) | Red — critical semantic |
| No rating / fallback | `#8b5cf6` (brand-500) | Violet — default brand |

All rating markers should still use the same stroke (`#080d19`) and glow pattern to maintain visual cohesion.

---

## Summary

The refinement moves the map from "a dark basemap with markers" to "a designed editorial canvas where data speaks." Every change serves one principle: **suppress the substrate, elevate the data.**
