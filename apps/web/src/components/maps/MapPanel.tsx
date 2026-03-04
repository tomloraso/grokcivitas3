import { lazy, Suspense } from "react";

import { LoadingSkeleton } from "../ui/LoadingSkeleton";
import { Panel } from "../ui/Card";
import { cn } from "../../shared/utils/cn";
import { MAP_BOUNDS } from "../../shared/maps/map-bounds";

const MapPanelMapLibre = lazy(async () => import("./MapPanelMapLibre"));

export interface MapMarker {
  id: string;
  lat: number;
  lng: number;
  label: string;
  distanceMiles?: number;
  
  // Data-driven map marker stylings
  phase?: string;
  ofstedRating?: string;
  
  // Interaction link
  isHovered?: boolean;
}

interface MapPanelProps {
  center: { lat: number; lng: number } | null;
  radiusMiles?: number;
  markers: MapMarker[];
  title?: string;
  className?: string;
  activeMarkerId?: string | null;
  onMarkerHover?: (id: string | null) => void;
}

export function MapPanel({
  center,
  radiusMiles,
  markers,
  title = "Map view",
  className,
  activeMarkerId,
  onMarkerHover
}: MapPanelProps): JSX.Element {
  const mapCenter = center || {
    lat: MAP_BOUNDS.DEFAULT_CENTER[1],
    lng: MAP_BOUNDS.DEFAULT_CENTER[0]
  };

  return (
    <Panel className={cn("overflow-hidden p-0", className)}>
      <div className="flex items-center justify-between border-b border-border-subtle px-4 py-3 sm:px-5">
        <h3 className="text-sm font-semibold uppercase tracking-[0.08em] text-secondary">{title}</h3>
        <p className="font-mono text-xs text-disabled">{markers.length} markers</p>
      </div>
      <div className="relative h-[320px] sm:h-[400px]">
        <Suspense fallback={<LoadingSkeleton lines={5} className="m-4 h-[calc(100%-2rem)]" />}>
          <MapPanelMapLibre 
            center={mapCenter} 
            radiusMiles={radiusMiles}
            markers={markers} 
            activeMarkerId={activeMarkerId}
            onMarkerHover={onMarkerHover}
          />
        </Suspense>
      </div>
    </Panel>
  );
}
