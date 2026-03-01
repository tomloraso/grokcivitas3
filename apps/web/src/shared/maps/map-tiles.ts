export interface MapTileProvider {
  id: string;
  label: string;
  url: string;
  attribution: string;
  maxZoom?: number;
}

const cartoDarkMatter: MapTileProvider = {
  id: "cartodb-dark-matter",
  label: "CartoDB Dark Matter",
  url: "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
  attribution: "&copy; OpenStreetMap contributors &copy; CARTO",
  maxZoom: 20
};

const cartoDarkNoLabels: MapTileProvider = {
  id: "cartodb-dark-nolabels",
  label: "CartoDB Dark Matter (No labels)",
  url: "https://{s}.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}{r}.png",
  attribution: "&copy; OpenStreetMap contributors &copy; CARTO",
  maxZoom: 20
};

function buildStadiaProvider(apiKey: string | undefined): MapTileProvider | null {
  if (!apiKey) {
    return null;
  }

  return {
    id: "stadia-dark",
    label: "Stadia Alidade Smooth Dark",
    url: `https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}{r}.png?api_key=${apiKey}`,
    attribution: "&copy; Stadia Maps &copy; OpenMapTiles &copy; OpenStreetMap contributors",
    maxZoom: 20
  };
}

const staticProviders: Record<string, MapTileProvider> = {
  [cartoDarkMatter.id]: cartoDarkMatter,
  [cartoDarkNoLabels.id]: cartoDarkNoLabels
};

interface TileProviderSelection {
  primary: MapTileProvider;
  fallback: MapTileProvider;
}

export function resolveMapTileProviders(providerFromEnv?: string): TileProviderSelection {
  const requestedProviderId = (providerFromEnv ?? import.meta.env.VITE_MAP_TILE_PROVIDER ?? "").trim();
  const requested = staticProviders[requestedProviderId];
  const stadia = buildStadiaProvider(import.meta.env.VITE_STADIA_MAPS_API_KEY);

  const primary = requested ?? cartoDarkMatter;
  const fallback = stadia ?? cartoDarkNoLabels;

  if (primary.id === fallback.id) {
    return {
      primary,
      fallback: primary.id === cartoDarkMatter.id ? cartoDarkNoLabels : cartoDarkMatter
    };
  }

  return { primary, fallback };
}
