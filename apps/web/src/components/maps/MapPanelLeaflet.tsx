import "leaflet/dist/leaflet.css";

import L from "leaflet";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { MapContainer, Marker, Popup, TileLayer, useMap, ZoomControl } from "react-leaflet";
import type { LatLngBoundsExpression, LatLngExpression, Marker as LeafletMarker } from "leaflet";

/** Constrain panning to the British Isles region */
const UK_MAX_BOUNDS: LatLngBoundsExpression = [
  [49.5, -8.2],
  [61.0, 2.0]
];
const UK_MIN_ZOOM = 5;

import { resolveMapTileProviders } from "../../shared/maps/map-tiles";
import type { MapMarker } from "./MapPanel";

const MARKER_SIZE_DESKTOP = 20;
const MARKER_SIZE_TOUCH = 32;
const TOUCH_MEDIA_QUERY = "(pointer: coarse)";

function useMarkerSize(): number {
  const [size, setSize] = useState(() =>
    typeof window !== "undefined" && window.matchMedia(TOUCH_MEDIA_QUERY).matches
      ? MARKER_SIZE_TOUCH
      : MARKER_SIZE_DESKTOP
  );

  useEffect(() => {
    const mql = window.matchMedia(TOUCH_MEDIA_QUERY);
    const handler = (event: MediaQueryListEvent) => {
      setSize(event.matches ? MARKER_SIZE_TOUCH : MARKER_SIZE_DESKTOP);
    };
    mql.addEventListener("change", handler);
    return () => mql.removeEventListener("change", handler);
  }, []);

  return size;
}

/** Build a DivIcon that renders as a styled circle dot. */
function createDotIcon(size: number): L.DivIcon {
  return L.divIcon({
    className: "",
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    popupAnchor: [0, -(size / 2)],
    html: `<span style="
      display:block;
      width:${size}px;
      height:${size}px;
      border-radius:50%;
      background:var(--color-action-primary);
      border:2px solid var(--color-text-primary);
      opacity:0.95;
    "></span>`
  });
}

/** Default zoom when no markers are present (national UK view) */
const UK_DEFAULT_ZOOM = 6;
/** Zoom level when displaying search results */
const SEARCH_RESULTS_ZOOM = 12;

/** Syncs the map view when center/zoom props change after initial mount. */
function MapViewUpdater({ center, zoom }: { center: LatLngExpression; zoom: number }): null {
  const map = useMap();
  const isInitialMount = useRef(true);

  useEffect(() => {
    if (isInitialMount.current) {
      isInitialMount.current = false;
      return;
    }
    map.flyTo(center, zoom, { duration: 1.2 });
  }, [map, center, zoom]);

  return null;
}

interface MapPanelLeafletProps {
  center: { lat: number; lng: number };
  markers: MapMarker[];
}

interface AccessibleDotMarkerProps {
  marker: MapMarker;
  icon: L.DivIcon;
}

function AccessibleDotMarker({ marker, icon }: AccessibleDotMarkerProps): JSX.Element {
  const markerRef = useRef<LeafletMarker | null>(null);

  useEffect(() => {
    const markerInstance = markerRef.current;
    if (!markerInstance) {
      return;
    }

    const ariaLabel =
      marker.distanceMiles !== undefined
        ? `${marker.label}, ${marker.distanceMiles.toFixed(2)} miles from search center`
        : marker.label;

    const el = markerInstance.getElement();
    if (el) {
      el.setAttribute("tabindex", "0");
      el.setAttribute("role", "button");
      el.setAttribute("aria-label", ariaLabel);
    }
  }, [marker.distanceMiles, marker.label]);

  return (
    <Marker
      ref={markerRef}
      position={[marker.lat, marker.lng]}
      icon={icon}
      eventHandlers={{
        keydown: (e) => {
          const key = (e.originalEvent as KeyboardEvent).key;
          if (key === "Enter" || key === " ") {
            e.originalEvent.preventDefault();
            markerRef.current?.openPopup();
          }
          if (key === "Escape") {
            markerRef.current?.closePopup();
          }
        }
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
    </Marker>
  );
}

export default function MapPanelLeaflet({
  center,
  markers
}: MapPanelLeafletProps): JSX.Element {
  const providers = resolveMapTileProviders();
  const [providerId, setProviderId] = useState(providers.primary.id);
  const markerSize = useMarkerSize();
  const dotIcon = useMemo(() => createDotIcon(markerSize), [markerSize]);
  const mapCenter = useMemo<LatLngExpression>(() => [center.lat, center.lng], [center]);
  const zoom = markers.length > 0 ? SEARCH_RESULTS_ZOOM : UK_DEFAULT_ZOOM;
  const provider = providerId === providers.fallback.id ? providers.fallback : providers.primary;

  const handleTileError = useCallback(() => {
    if (providerId !== providers.fallback.id) {
      setProviderId(providers.fallback.id);
    }
  }, [providerId, providers.fallback.id]);

  return (
    <MapContainer
      center={mapCenter}
      zoom={zoom}
      zoomControl={false}
      className="h-full w-full"
      scrollWheelZoom={true}
      maxBounds={UK_MAX_BOUNDS}
      maxBoundsViscosity={1.0}
      minZoom={UK_MIN_ZOOM}
    >
      <TileLayer
        attribution={provider.attribution}
        url={provider.url}
        maxZoom={provider.maxZoom}
        eventHandlers={{ tileerror: handleTileError }}
      />
      <ZoomControl position="bottomright" />
      <MapViewUpdater center={mapCenter} zoom={zoom} />
      {markers.map((marker) => (
        <AccessibleDotMarker key={marker.id} marker={marker} icon={dotIcon} />
      ))}
    </MapContainer>
  );
}
