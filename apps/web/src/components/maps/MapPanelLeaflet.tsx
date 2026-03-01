import "leaflet/dist/leaflet.css";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { CircleMarker, MapContainer, Popup, TileLayer, ZoomControl } from "react-leaflet";
import type { CircleMarker as LeafletCircleMarker, LatLngExpression } from "leaflet";

import { resolveMapTileProviders } from "../../shared/maps/map-tiles";
import type { MapMarker } from "./MapPanel";

const MARKER_RADIUS_DESKTOP = 10;
const MARKER_RADIUS_TOUCH = 16;
const TOUCH_MEDIA_QUERY = "(pointer: coarse)";

function useMarkerRadius(): number {
  const [radius, setRadius] = useState(() =>
    typeof window !== "undefined" && window.matchMedia(TOUCH_MEDIA_QUERY).matches
      ? MARKER_RADIUS_TOUCH
      : MARKER_RADIUS_DESKTOP
  );

  useEffect(() => {
    const mql = window.matchMedia(TOUCH_MEDIA_QUERY);
    const handler = (event: MediaQueryListEvent) => {
      setRadius(event.matches ? MARKER_RADIUS_TOUCH : MARKER_RADIUS_DESKTOP);
    };
    mql.addEventListener("change", handler);
    return () => mql.removeEventListener("change", handler);
  }, []);

  return radius;
}

interface MapPanelLeafletProps {
  center: { lat: number; lng: number };
  markers: MapMarker[];
}

interface AccessibleCircleMarkerProps {
  marker: MapMarker;
  radius: number;
}

function AccessibleCircleMarker({ marker, radius }: AccessibleCircleMarkerProps): JSX.Element {
  const markerRef = useRef<LeafletCircleMarker | null>(null);

  useEffect(() => {
    const markerInstance = markerRef.current;
    if (!markerInstance) {
      return;
    }

    const ariaLabel =
      marker.distanceMiles !== undefined
        ? `${marker.label}, ${marker.distanceMiles.toFixed(2)} miles from search center`
        : marker.label;

    const handleFocus = () => markerInstance.openPopup();
    const handleBlur = () => markerInstance.closePopup();
    const handleKeydown = (event: Event) => {
      if (!(event instanceof KeyboardEvent)) {
        return;
      }

      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        markerInstance.openPopup();
      }

      if (event.key === "Escape") {
        markerInstance.closePopup();
      }
    };

    let boundElement: HTMLElement | SVGElement | null = null;
    const bindAccessibility = () => {
      const element = markerInstance.getElement();
      if (!element || boundElement === element) {
        return;
      }

      if (boundElement) {
        boundElement.removeEventListener("focus", handleFocus);
        boundElement.removeEventListener("blur", handleBlur);
        boundElement.removeEventListener("keydown", handleKeydown);
      }

      const interactiveElement = element as HTMLElement | SVGElement;
      boundElement = interactiveElement;
      interactiveElement.setAttribute("tabindex", "0");
      interactiveElement.setAttribute("role", "button");
      interactiveElement.setAttribute("aria-label", ariaLabel);
      interactiveElement.addEventListener("focus", handleFocus);
      interactiveElement.addEventListener("blur", handleBlur);
      interactiveElement.addEventListener("keydown", handleKeydown);
    };

    bindAccessibility();
    markerInstance.on("add", bindAccessibility);

    return () => {
      markerInstance.off("add", bindAccessibility);

      if (boundElement) {
        boundElement.removeEventListener("focus", handleFocus);
        boundElement.removeEventListener("blur", handleBlur);
        boundElement.removeEventListener("keydown", handleKeydown);
      }
    };
  }, [marker.distanceMiles, marker.label]);

  return (
    <CircleMarker
      ref={markerRef}
      center={[marker.lat, marker.lng]}
      radius={radius}
      pathOptions={{
        color: "var(--color-text-primary)",
        weight: 2,
        fillColor: "var(--color-action-primary)",
        fillOpacity: 0.95
      }}
    >
      <Popup>
        <div className="space-y-1">
          <strong>{marker.label}</strong>
          {marker.distanceMiles !== undefined ? (
            <div>{marker.distanceMiles.toFixed(2)} mi from search center</div>
          ) : null}
        </div>
      </Popup>
    </CircleMarker>
  );
}

export default function MapPanelLeaflet({
  center,
  markers
}: MapPanelLeafletProps): JSX.Element {
  const providers = resolveMapTileProviders();
  const [providerId, setProviderId] = useState(providers.primary.id);
  const markerRadius = useMarkerRadius();
  const mapCenter = useMemo<LatLngExpression>(() => [center.lat, center.lng], [center]);
  const provider = providerId === providers.fallback.id ? providers.fallback : providers.primary;

  const handleTileError = useCallback(() => {
    if (providerId !== providers.fallback.id) {
      setProviderId(providers.fallback.id);
    }
  }, [providerId, providers.fallback.id]);

  return (
    <MapContainer
      center={mapCenter}
      zoom={12}
      zoomControl={false}
      className="h-full w-full"
      scrollWheelZoom={false}
    >
      <TileLayer
        attribution={provider.attribution}
        url={provider.url}
        maxZoom={provider.maxZoom}
        eventHandlers={{ tileerror: handleTileError }}
      />
      <ZoomControl position="bottomright" />
      {markers.map((marker) => (
        <AccessibleCircleMarker key={marker.id} marker={marker} radius={markerRadius} />
      ))}
    </MapContainer>
  );
}
