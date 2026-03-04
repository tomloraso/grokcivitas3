import { describe, expect, it } from "vitest";

import { getMapStyle } from "./map-style";

describe("getMapStyle", () => {
  it("returns dark style by default", () => {
    const style = getMapStyle();
    expect(style.name).toBe("Civitas Dark");
  });

  it("returns dark style when theme is 'dark'", () => {
    const style = getMapStyle("dark");
    expect(style.name).toBe("Civitas Dark");
  });

  it("returns light style when theme is 'light'", () => {
    const style = getMapStyle("light");
    expect(style.name).toBe("Civitas Light");
  });

  it("contains expected source configuration", () => {
    const dark = getMapStyle("dark");
    const light = getMapStyle("light");

    expect(dark.sources).toHaveProperty("openmaptiles");
    expect(light.sources).toHaveProperty("openmaptiles");
  });
});
