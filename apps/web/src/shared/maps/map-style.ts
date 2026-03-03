import type { StyleSpecification } from "maplibre-gl";

import darkStyle from "./civitas-dark.json";

export function getMapStyle(): StyleSpecification {
  // We use Carto's open source as our data source, but style it locally with our brand tokens
  return darkStyle as unknown as StyleSpecification;
}
