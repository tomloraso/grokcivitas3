/**
 * Centralized route path helpers.
 * Feature code uses these instead of hardcoding path strings.
 */
export const paths = {
  home: "/",
  signIn: (returnTo?: string | null) => {
    if (!returnTo) {
      return "/sign-in";
    }

    const params = new URLSearchParams({ returnTo });
    return `/sign-in?${params.toString()}` as const;
  },
  compare: (urns: string[] = []) =>
    urns.length > 0
      ? (`/compare?urns=${encodeURIComponent(urns.join(","))}` as const)
      : "/compare",
  schoolProfile: (urn: string) => `/schools/${urn}` as const
} as const;
