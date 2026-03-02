import type { ReactNode } from "react";

import { cn } from "../../shared/utils/cn";

interface MapOverlayLayoutProps {
  /** The map component rendered as the full-viewport background */
  map: ReactNode;
  /** Overlay panel content (search form, results, etc.) */
  children: ReactNode;
  className?: string;
}

/**
 * Layout variant where the map stretches to full viewport and
 * UI panels float as glassmorphism overlays. Sets `data-layout="map-overlay"`
 * so CSS can conditionally suppress ambient glows.
 */
export function MapOverlayLayout({
  map,
  children,
  className
}: MapOverlayLayoutProps): JSX.Element {
  return (
    <div
      data-layout="map-overlay"
      className={cn("relative h-[calc(100vh-3.5rem)] overflow-hidden", className)}
    >
      {/* Full-bleed map background */}
      <section aria-label="Map view" className="absolute inset-0 z-0">
        {map}
      </section>

      {/* Overlay panel slot */}
      <div className="pointer-events-none absolute inset-0 z-base p-4 sm:p-6">
        <div className="pointer-events-auto h-full w-[min(420px,100%)] overflow-y-auto rounded-xl panel-surface-neutral shadow-lg scrollbar-hide">
          {children}
        </div>
      </div>
    </div>
  );
}
