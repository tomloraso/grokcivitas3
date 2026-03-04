import type { StyleSpecification } from "maplibre-gl";

import darkStyle from "./civitas-dark.json";
import lightStyle from "./civitas-light.json";

import type { ResolvedTheme } from "../theme/theme-mode";

export function getMapStyle(theme: ResolvedTheme = "dark"): StyleSpecification {
  const style = theme === "light" ? lightStyle : darkStyle;
  return style as unknown as StyleSpecification;
}
