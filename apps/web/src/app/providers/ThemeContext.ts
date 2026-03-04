import { createContext } from "react";
import type { ThemeMode, ResolvedTheme } from "../../shared/theme/theme-mode";

export interface ThemeContextValue {
  /** User-persisted preference: "dark" | "light" | "system". */
  mode: ThemeMode;
  /** Runtime-resolved theme applied to the DOM: "dark" | "light". */
  theme: ResolvedTheme;
  /** Set an explicit mode and persist it. */
  setMode: (mode: ThemeMode) => void;
  /** Cycle through system → light → dark → system. */
  cycleMode: () => void;
}

export const ThemeContext = createContext<ThemeContextValue | null>(null);
