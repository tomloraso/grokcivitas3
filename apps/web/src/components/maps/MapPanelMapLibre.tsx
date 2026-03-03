import "maplibre-gl/dist/maplibre-gl.css";
import * as React from "react";
import { useEffect, useMemo, useState, useRef } from "react";
import Map, { Marker, Popup, NavigationControl, ViewStateChangeEvent, Source, Layer, MapRef } from "react-map-gl/maplibre";
import maplibregl from "maplibre-gl";
import { Protocol } from "pmtiles";
import circle from '@turf/circle';

import { MAP_BOUNDS } from "../../shared/maps/map-bounds";
import { getMapStyle } from "../../shared/maps/map-style";
import { MAP_BRAND, MAP_BG, MAP_TEXT_ON_BRAND, OFSTED_COLORS, markerColor } from "../../shared/maps/map-tokens";
import { useReducedMotion } from "../../shared/hooks/useReducedMotion";
import type { MapMarker } from "./MapPanel";

type ProtocolRegistryGlobal = typeof globalThis & {
  __civitasPmtilesRegistered?: boolean;
};

const protocolRegistry = globalThis as ProtocolRegistryGlobal;

// Register PMTiles protocol to handle pmtiles:// URLs once per runtime.
if (!protocolRegistry.__civitasPmtilesRegistered) {
  const protocol = new Protocol();
  maplibregl.addProtocol("pmtiles", protocol.tile);
  protocolRegistry.__civitasPmtilesRegistered = true;
}

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

const SEARCH_RESULTS_ZOOM = 12;

interface MapPanelMapLibreProps {
  center: { lat: number; lng: number };
  radiusMiles?: number;
  markers: MapMarker[];
  activeMarkerId?: string | null;
  onMarkerHover?: (id: string | null) => void;
}

export default function MapPanelMapLibre({
  center,
  radiusMiles,
  activeMarkerId,
  onMarkerHover,
  markers
}: MapPanelMapLibreProps): JSX.Element {
  const mapStyle = useMemo(() => getMapStyle(), []);
  const markerSize = useMarkerSize();
  const [popupInfo, setPopupInfo] = useState<MapMarker | null>(null);

  // Keep track of the view state
  const targetZoom = markers.length > 0 ? SEARCH_RESULTS_ZOOM : MAP_BOUNDS.DEFAULT_ZOOM;
  const mapRef = useRef<MapRef>(null);
  
  const [viewState, setViewState] = useState({
    longitude: center.lng,
    latitude: center.lat,
    zoom: targetZoom
  });

  const prefersReducedMotion = useReducedMotion();

  const isInitialMount = useRef(true);

  // Sync state if incoming props change significantly (e.g. new search)
  useEffect(() => {
    if (isInitialMount.current) {
      isInitialMount.current = false;
      return;
    }
    
    if (mapRef.current) {
      const map = mapRef.current.getMap();
      
      const targetState = {
        center: [center.lng, center.lat] as [number, number],
        zoom: targetZoom
      };

      if (prefersReducedMotion) {
        map.jumpTo(targetState);
      } else {
        map.flyTo({
          ...targetState,
          duration: 1200,
          essential: true
        });
      }
    }
  }, [center.lng, center.lat, targetZoom, prefersReducedMotion]);

  const onMove = React.useCallback((evt: ViewStateChangeEvent) => {
    setViewState(evt.viewState);
  }, []);

  // For keyboard a11y on markers
  const handleMarkerKeyDown = (e: React.KeyboardEvent, marker: MapMarker) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      setPopupInfo(marker);
    } else if (e.key === "Escape") {
      setPopupInfo(null);
    }
  };

  // Convert markers to GeoJSON for clustering
  const geojsonMarkers = useMemo(() => {
    return {
      type: "FeatureCollection" as const,
      features: markers.map(marker => ({
        type: "Feature" as const,
        geometry: {
          type: "Point" as const,
          coordinates: [marker.lng, marker.lat]
        },
        properties: {
          ...marker,
          isActive: marker.isHovered || activeMarkerId === marker.id
        }
      }))
    };
  }, [markers, activeMarkerId]);

  // Create radius circle polygon
  const radiusFeature = useMemo(() => {
    if (!radiusMiles) return null;
    return circle([center.lng, center.lat], radiusMiles, { units: 'miles' });
  }, [center.lng, center.lat, radiusMiles]);

  return (
    <div className="h-full w-full relative">
      <Map
        ref={mapRef}
        {...viewState}
        onMove={onMove}
        mapStyle={mapStyle}
        style={{ width: "100%", height: "100%" }}
        minZoom={MAP_BOUNDS.MIN_ZOOM}
        maxZoom={MAP_BOUNDS.MAX_ZOOM}
        maxBounds={MAP_BOUNDS.UK_BBOX}
        maplibreLogo={true}
        attributionControl={false}
      >
        {radiusFeature && (
          <Source type="geojson" data={radiusFeature}>
            <Layer
              id="search-radius-fill"
              type="fill"
              paint={{
                "fill-color": MAP_BRAND,
                "fill-opacity": 0.05
              }}
            />
            <Layer
              id="search-radius-line"
              type="line"
              paint={{
                "line-color": MAP_BRAND,
                "line-opacity": 0.2,
                "line-width": 1,
                "line-dasharray": [4, 4]
              }}
            />
          </Source>
        )}

        <NavigationControl position="bottom-right" showCompass={false} />

        {/* Source for clustered points */}
        <Source
          id="school-markers"
          type="geojson"
          data={geojsonMarkers}
          cluster={true}
          clusterMaxZoom={14}
          clusterRadius={50}
        >
          {/* Cluster circles */}
          <Layer
            id="clusters"
            type="circle"
            filter={["has", "point_count"]}
            paint={{
              "circle-color": MAP_BRAND,
              "circle-radius": [
                "step",
                ["get", "point_count"],
                15, // base radius
                10,
                20, // radius 20 if count >= 10
                50,
                25  // radius 25 if count >= 50
              ],
              "circle-stroke-width": 2,
              "circle-stroke-color": MAP_BG,
              "circle-opacity": 0.95
            }}
          />

          {/* Cluster count labels */}
          <Layer
            id="cluster-counts"
            type="symbol"
            filter={["has", "point_count"]}
            layout={{
              "text-field": "{point_count_abbreviated}",
              "text-font": ["Noto Sans Regular"],
              "text-size": 12,
              "text-allow-overlap": true
            }}
            paint={{
              "text-color": MAP_TEXT_ON_BRAND
            }}
          />
        </Source>

        {/* Individual unclustered markers */}
        {viewState.zoom > 14 ? markers.map((marker) => {
          const isActive = marker.isHovered || activeMarkerId === marker.id;
          const ariaLabel = marker.distanceMiles !== undefined
            ? `${marker.label}, ${marker.distanceMiles.toFixed(2)} miles from search center`
            : radiusMiles !== undefined
              ? `${marker.label}, within ${radiusMiles.toFixed(1)} mile search radius`
            : marker.label;

          return (
            <Marker
              key={marker.id}
              longitude={marker.lng}
              latitude={marker.lat}
              anchor="center"
              onClick={e => {
                e.originalEvent.stopPropagation();
                setPopupInfo(marker);
              }}
            >
              <div
                className="civitas-map-marker"
                tabIndex={0}
                role="button"
                aria-label={ariaLabel}
                onMouseEnter={() => onMarkerHover?.(marker.id)}
                onMouseLeave={() => onMarkerHover?.(null)}
                onKeyDown={(e) => handleMarkerKeyDown(e, marker)}
                style={{
                  width: `${markerSize}px`,
                  height: `${markerSize}px`,
                  borderRadius: "50%",
                  backgroundColor: markerColor(marker.ofstedRating, marker.phase),
                  border: `2px solid var(--ref-color-navy-950, ${MAP_BG})`,
                  boxShadow: isActive
                    ? "0 0 12px 5px var(--marker-glow-active)"
                    : "0 0 8px 3px var(--marker-glow)",
                  transform: isActive ? "scale(1.15)" : "scale(1)",
                  opacity: 0.95,
                  cursor: "pointer",
                  transition: "transform 120ms ease, box-shadow 120ms ease"
                }}
              />
            </Marker>
          );
        }) : null}

        {popupInfo && (
          <Popup
            longitude={popupInfo.lng}
            latitude={popupInfo.lat}
            anchor="bottom"
            offset={markerSize / 2 + 4}
            onClose={() => setPopupInfo(null)}
            closeOnClick={true}
            closeButton={false} // Will close on click outside
            className="civitas-map-popup"
          >
            <div className="space-y-2 text-sm p-3 min-w-[200px]">
              <div>
                <strong className="text-base text-primary block leading-tight">{popupInfo.label}</strong>
                {popupInfo.phase ? <span className="text-xs text-secondary mt-0.5 block">{popupInfo.phase}</span> : null}
              </div>
              
              {(popupInfo.distanceMiles !== undefined || popupInfo.ofstedRating) && (
                <div className="flex items-center justify-between gap-3 text-xs pt-1 border-t border-border-subtle mt-2">
                  <span className="text-disabled font-mono">{popupInfo.distanceMiles !== undefined ? `${popupInfo.distanceMiles.toFixed(2)} mi` : ''}</span>
                  {popupInfo.ofstedRating && (
                    <span className="font-semibold" style={{ color: popupInfo.ofstedRating && popupInfo.ofstedRating in OFSTED_COLORS ? OFSTED_COLORS[popupInfo.ofstedRating as keyof typeof OFSTED_COLORS] : 'inherit' }}>
                      {popupInfo.ofstedRating}
                    </span>
                  )}
                </div>
              )}
            </div>
          </Popup>
        )}
      </Map>
    </div>
  );
}
