import { useEffect, useState } from "react";

const MOBILE_BREAKPOINT = 768; // md breakpoint

/**
 * Returns true when the viewport width is below the md breakpoint (768px).
 * Falls back to false during SSR / initial render.
 */
export function useIsMobile(): boolean {
  const [isMobile, setIsMobile] = useState(() => {
    if (typeof window === "undefined") return false;
    return window.innerWidth < MOBILE_BREAKPOINT;
  });

  useEffect(() => {
    const mql = window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT - 1}px)`);
    const handler = (e: MediaQueryListEvent): void => {
      setIsMobile(e.matches);
    };

    setIsMobile(mql.matches);
    mql.addEventListener("change", handler);
    return () => mql.removeEventListener("change", handler);
  }, []);

  return isMobile;
}
