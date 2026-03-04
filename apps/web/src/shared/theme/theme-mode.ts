/**
 * Theme mode constants, parsing, and precedence helpers.
 *
 * Three persisted values: "dark", "light", "system".
 * Resolved runtime theme is always "dark" or "light".
 */

export const THEME_MODES = ["dark", "light", "system"] as const;
export type ThemeMode = (typeof THEME_MODES)[number];
export type ResolvedTheme = "dark" | "light";

export const STORAGE_KEY = "civitas.theme.mode";
export const DEFAULT_MODE: ThemeMode = "system";
export const FALLBACK_THEME: ResolvedTheme = "dark";

/* ------------------------------------------------------------------ */
/* Parsing                                                              */
/* ------------------------------------------------------------------ */

/** Parse an unknown value into a valid ThemeMode, falling back to DEFAULT_MODE. */
export function parseThemeMode(value: unknown): ThemeMode {
  if (typeof value === "string" && THEME_MODES.includes(value as ThemeMode)) {
    return value as ThemeMode;
  }
  return DEFAULT_MODE;
}

/* ------------------------------------------------------------------ */
/* Resolution                                                           */
/* ------------------------------------------------------------------ */

/** Resolve persisted mode + system preference → "dark" | "light". */
export function resolveTheme(
  mode: ThemeMode,
  systemPrefersDark: boolean,
): ResolvedTheme {
  if (mode === "dark") return "dark";
  if (mode === "light") return "light";
  // mode === "system"
  return systemPrefersDark ? "dark" : "light";
}

/* ------------------------------------------------------------------ */
/* Persistence                                                          */
/* ------------------------------------------------------------------ */

export function readPersistedMode(): ThemeMode {
  try {
    return parseThemeMode(localStorage.getItem(STORAGE_KEY));
  } catch {
    return DEFAULT_MODE;
  }
}

export function persistMode(mode: ThemeMode): void {
  try {
    localStorage.setItem(STORAGE_KEY, mode);
  } catch {
    // Storage unavailable — silently ignore.
  }
}

/* ------------------------------------------------------------------ */
/* DOM helpers                                                          */
/* ------------------------------------------------------------------ */

/** Apply resolved theme to <html> element for CSS token switching. */
export function applyThemeToDOM(theme: ResolvedTheme): void {
  const root = document.documentElement;
  root.setAttribute("data-theme", theme);
  root.style.colorScheme = theme;
}

/* ------------------------------------------------------------------ */
/* Cycling                                                              */
/* ------------------------------------------------------------------ */

const MODE_CYCLE: ThemeMode[] = ["system", "light", "dark"];

/** Cycle to the next mode in the order: system → light → dark → system. */
export function nextMode(current: ThemeMode): ThemeMode {
  const idx = MODE_CYCLE.indexOf(current);
  return MODE_CYCLE[(idx + 1) % MODE_CYCLE.length];
}
