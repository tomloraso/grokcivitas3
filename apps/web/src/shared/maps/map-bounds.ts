import type { LngLatBoundsLike } from "maplibre-gl";

export const MAP_BOUNDS = {
  // Approximate full UK bounds
  UK_BBOX: [
    [-8.2, 49.5], // SW [lng, lat]
    [2.0, 61.0] // NE [lng, lat]
  ] as LngLatBoundsLike,

  // Default landing state (London roughly centered if no other data)
  DEFAULT_CENTER: [-0.1276, 51.5072] as [number, number],
  DEFAULT_ZOOM: 5.5,

  // Constraints
  MIN_ZOOM: 5,
  MAX_ZOOM: 17
};
