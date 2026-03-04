import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  type ThemeMode,
  readPersistedMode,
  persistMode,
  resolveTheme,
  applyThemeToDOM,
  nextMode,
} from "../../shared/theme/theme-mode";

import { ThemeContext, type ThemeContextValue } from "./ThemeContext";

/* ------------------------------------------------------------------ */
/* Provider                                                             */
/* ------------------------------------------------------------------ */

function getSystemPrefersDark(): boolean {
  if (typeof window === "undefined") return true;
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

export function ThemeProvider({ children }: { children: React.ReactNode }): JSX.Element {
  const [mode, setModeState] = useState<ThemeMode>(readPersistedMode);
  const [systemDark, setSystemDark] = useState(getSystemPrefersDark);

  const theme = useMemo(() => resolveTheme(mode, systemDark), [mode, systemDark]);

  // Keep DOM attribute in sync.
  useEffect(() => {
    applyThemeToDOM(theme);
  }, [theme]);

  // Listen for OS-level preference changes.
  useEffect(() => {
    const mql = window.matchMedia("(prefers-color-scheme: dark)");
    const handler = (e: MediaQueryListEvent) => setSystemDark(e.matches);
    mql.addEventListener("change", handler);
    return () => mql.removeEventListener("change", handler);
  }, []);

  const setMode = useCallback((next: ThemeMode) => {
    setModeState(next);
    persistMode(next);
  }, []);

  const cycleMode = useCallback(() => {
    setModeState((prev) => {
      const next = nextMode(prev);
      persistMode(next);
      return next;
    });
  }, []);

  const value = useMemo<ThemeContextValue>(
    () => ({ mode, theme, setMode, cycleMode }),
    [mode, theme, setMode, cycleMode],
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}
