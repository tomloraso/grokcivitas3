import { useEffect, useState } from "react";

const QUERY = "(prefers-reduced-motion: reduce)";

function getInitialState(): boolean {
  if (typeof window === "undefined") return false;
  return window.matchMedia(QUERY).matches;
}

/**
 * Reactive hook that tracks the user's `prefers-reduced-motion` media query.
 * Returns `true` when the user prefers reduced motion.
 *
 * Updates live if the preference changes at runtime (e.g. system settings toggle).
 */
export function useReducedMotion(): boolean {
  const [reduced, setReduced] = useState(getInitialState);

  useEffect(() => {
    const mql = window.matchMedia(QUERY);
    const handler = (e: MediaQueryListEvent) => setReduced(e.matches);
    mql.addEventListener("change", handler);
    return () => mql.removeEventListener("change", handler);
  }, []);

  return reduced;
}
