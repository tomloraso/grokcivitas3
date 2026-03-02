/**
 * Centralized route path helpers.
 * Feature code uses these instead of hardcoding path strings.
 */
export const paths = {
  home: "/",
  schoolProfile: (urn: string) => `/schools/${urn}` as const
} as const;
