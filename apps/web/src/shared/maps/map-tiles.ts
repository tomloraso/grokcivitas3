export interface MapTileProvider {
  id: string;
  urlTemplate: string;
  attribution: string;
}

interface MapTileProviderResolution {
  primary: MapTileProvider;
  fallback: MapTileProvider;
}

const PROVIDERS: Record<string, MapTileProvider> = {
  "cartodb-dark-matter": {
    id: "cartodb-dark-matter",
    urlTemplate: "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
    attribution: "&copy; OpenStreetMap contributors &copy; CARTO"
  },
  "cartodb-dark-nolabels": {
    id: "cartodb-dark-nolabels",
    urlTemplate: "https://{s}.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}{r}.png",
    attribution: "&copy; OpenStreetMap contributors &copy; CARTO"
  }
};

const DEFAULT_PRIMARY_ID = "cartodb-dark-matter";
const DEFAULT_FALLBACK_ID = "cartodb-dark-nolabels";

export function resolveMapTileProviders(
  preferredProviderId?: string | null
): MapTileProviderResolution {
  const preferred = preferredProviderId
    ? PROVIDERS[preferredProviderId]
    : undefined;
  const primary =
    preferred ?? PROVIDERS[DEFAULT_PRIMARY_ID];
  const fallback =
    primary.id === DEFAULT_FALLBACK_ID
      ? PROVIDERS[DEFAULT_PRIMARY_ID]
      : PROVIDERS[DEFAULT_FALLBACK_ID];

  return { primary, fallback };
}
