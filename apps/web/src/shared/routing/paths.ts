/**
 * Centralized route path helpers.
 * Feature code uses these instead of hardcoding path strings.
 */
export const paths = {
  home: "/",
  compare: (urns: string[] = []) =>
    urns.length > 0
      ? (`/compare?urns=${encodeURIComponent(urns.join(","))}` as const)
      : "/compare",
  schoolProfile: (urn: string) => `/schools/${urn}` as const
} as const;
