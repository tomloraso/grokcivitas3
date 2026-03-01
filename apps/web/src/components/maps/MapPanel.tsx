import { lazy, Suspense } from "react";

import { LoadingSkeleton } from "../ui/LoadingSkeleton";
import { Panel } from "../ui/Card";
import { cn } from "../../shared/utils/cn";

const MapPanelLeaflet = lazy(async () => import("./MapPanelLeaflet"));

export interface MapMarker {
  id: string;
  lat: number;
  lng: number;
  label: string;
  distanceMiles?: number;
}

interface MapPanelProps {
  center: { lat: number; lng: number } | null;
  markers: MapMarker[];
  title?: string;
  className?: string;
}

export function MapPanel({
  center,
  markers,
  title = "Map view",
  className
}: MapPanelProps): JSX.Element {
  return (
    <Panel className={cn("overflow-hidden p-0", className)}>
      <div className="flex items-center justify-between border-b border-border-subtle px-4 py-3 sm:px-5">
        <h3 className="text-sm font-semibold uppercase tracking-[0.08em] text-secondary">{title}</h3>
        <p className="font-mono text-xs text-disabled">{markers.length} markers</p>
      </div>
      <div className="relative h-[320px] sm:h-[400px]">
        {center ? (
          <Suspense fallback={<LoadingSkeleton lines={5} className="m-4 h-[calc(100%-2rem)]" />}>
            <MapPanelLeaflet center={center} markers={markers} />
          </Suspense>
        ) : (
          <div className="grid h-full place-items-center bg-surface/80 p-6 text-center">
            <p className="max-w-sm text-sm text-secondary">
              Search results will appear here once a postcode is resolved.
            </p>
          </div>
        )}
      </div>
    </Panel>
  );
}
