import { useEffect, useState } from "react";

/**
 * Returns true when the primary pointer is coarse (touch device).
 * Reacts to changes (e.g. detaching a stylus or switching to tablet mode).
 * Falls back to false during SSR / initial render.
 */
export function useIsTouch(): boolean {
  const [isTouch, setIsTouch] = useState(() => {
    if (typeof window === "undefined") return false;
    return window.matchMedia("(pointer: coarse)").matches;
  });

  useEffect(() => {
    const mql = window.matchMedia("(pointer: coarse)");
    const handler = (e: MediaQueryListEvent): void => {
      setIsTouch(e.matches);
    };

    setIsTouch(mql.matches);
    mql.addEventListener("change", handler);
    return () => mql.removeEventListener("change", handler);
  }, []);

  return isTouch;
}
