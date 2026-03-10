import {
  DEFAULT_SEARCH_SORT_MODE,
  normalizeSearchPhaseFilters,
  type SearchPhaseFilter,
  type SearchSortMode,
  type SearchViewMode,
} from "../search/searchState";

/**
 * Centralized route path helpers.
 * Feature code uses these instead of hardcoding path strings.
 */
export const paths = {
  home: "/",
  account: "/account",
  accountFavourites: "/account/favourites",
  homeSearch: ({
    view = "map",
    resultsPhases = [],
    resultsSort = DEFAULT_SEARCH_SORT_MODE,
  }: {
    view?: SearchViewMode;
    resultsPhases?: readonly SearchPhaseFilter[];
    resultsSort?: SearchSortMode;
  } = {}) => {
    if (view === "map") {
      return "/";
    }

    const normalizedSort = resultsSort === "ofsted" ? "ofsted" : DEFAULT_SEARCH_SORT_MODE;
    const params = new URLSearchParams({ view: "results", sort: normalizedSort });
    for (const phase of normalizeSearchPhaseFilters(resultsPhases)) {
      params.append("phase", phase);
    }
    return `/?${params.toString()}` as const;
  },
  signIn: (returnTo?: string | null) => {
    if (!returnTo) {
      return "/sign-in";
    }

    const params = new URLSearchParams({ returnTo });
    return `/sign-in?${params.toString()}` as const;
  },
  upgrade: ({
    capability,
    product,
    returnTo,
  }: {
    capability?: string;
    product?: string;
    returnTo?: string | null;
  } = {}) => {
    const params = new URLSearchParams();
    if (capability) {
      params.set("capability", capability);
    }
    if (product) {
      params.set("product", product);
    }
    if (returnTo) {
      params.set("returnTo", returnTo);
    }
    const query = params.toString();
    return query ? (`/account/upgrade?${query}` as const) : "/account/upgrade";
  },
  compare: (urns: string[] = []) =>
    urns.length > 0
      ? (`/compare?urns=${encodeURIComponent(urns.join(","))}` as const)
      : "/compare",
  schoolProfile: (urn: string) => `/schools/${urn}` as const
} as const;
