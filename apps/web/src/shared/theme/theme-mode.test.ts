import { describe, expect, it, beforeEach } from "vitest";

import {
  parseThemeMode,
  resolveTheme,
  readPersistedMode,
  persistMode,
  nextMode,
  STORAGE_KEY,
  DEFAULT_MODE,
} from "./theme-mode";

describe("parseThemeMode", () => {
  it.each(["dark", "light", "system"] as const)(
    "accepts valid mode '%s'",
    (mode) => {
      expect(parseThemeMode(mode)).toBe(mode);
    },
  );

  it("falls back to DEFAULT_MODE for unknown strings", () => {
    expect(parseThemeMode("turbo")).toBe(DEFAULT_MODE);
  });

  it("falls back for null / undefined / number", () => {
    expect(parseThemeMode(null)).toBe(DEFAULT_MODE);
    expect(parseThemeMode(undefined)).toBe(DEFAULT_MODE);
    expect(parseThemeMode(42)).toBe(DEFAULT_MODE);
  });
});

describe("resolveTheme", () => {
  it("returns 'dark' when mode is 'dark', regardless of system preference", () => {
    expect(resolveTheme("dark", false)).toBe("dark");
    expect(resolveTheme("dark", true)).toBe("dark");
  });

  it("returns 'light' when mode is 'light', regardless of system preference", () => {
    expect(resolveTheme("light", false)).toBe("light");
    expect(resolveTheme("light", true)).toBe("light");
  });

  it("delegates to system preference when mode is 'system'", () => {
    expect(resolveTheme("system", true)).toBe("dark");
    expect(resolveTheme("system", false)).toBe("light");
  });
});

describe("persistence", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("readPersistedMode returns DEFAULT_MODE when storage is empty", () => {
    expect(readPersistedMode()).toBe(DEFAULT_MODE);
  });

  it("round-trips a persisted mode", () => {
    persistMode("light");
    expect(readPersistedMode()).toBe("light");
  });

  it("uses the correct storage key", () => {
    persistMode("dark");
    expect(localStorage.getItem(STORAGE_KEY)).toBe("dark");
  });
});

describe("nextMode", () => {
  it("cycles system → light → dark → system", () => {
    expect(nextMode("system")).toBe("light");
    expect(nextMode("light")).toBe("dark");
    expect(nextMode("dark")).toBe("system");
  });
});
