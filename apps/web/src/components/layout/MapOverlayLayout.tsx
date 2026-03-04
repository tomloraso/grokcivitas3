import type { ReactNode } from "react";

import { cn } from "../../shared/utils/cn";
import { useIsMobile } from "../../shared/hooks/useIsMobile";
import { usePanelState, PANEL_MIN_WIDTH, PANEL_MAX_WIDTH } from "../../shared/hooks/usePanelState";
import { useScrollShadow } from "../../shared/hooks/useScrollShadow";

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
 *
 * Desktop: resizable side panel (drag right edge, 280–480 px, persisted).
 * Mobile: bottom-sheet overlay with peek/expanded states and drag handle.
 */
export function MapOverlayLayout({
  map,
  children,
  className,
}: MapOverlayLayoutProps): JSX.Element {
  const isMobile = useIsMobile();
  const { panelWidth, sheetMode, setSheetMode, resizeHandlers, sheetDragHandlers, sheetRef, isResizing } =
    usePanelState();
  const { scrollRef, topSentinelRef, bottomSentinelRef, showTopShadow, showBottomShadow } =
    useScrollShadow();

  return (
    <div
      data-layout="map-overlay"
      className={cn("relative h-[calc(100vh-3.5rem)] overflow-hidden", className)}
    >
      {/* Full-bleed map background */}
      <section aria-label="Map view" className="absolute inset-0 z-0">
        {map}
      </section>

      {/* --- Mobile bottom-sheet --- */}
      {isMobile ? (
        <div
          ref={sheetRef}
          role="region"
          aria-label="Results panel"
          className={cn(
            "absolute inset-x-0 bottom-0 z-base flex flex-col rounded-t-xl panel-surface-neutral shadow-lg bottom-sheet",
            sheetMode === "expanded" ? "h-[80vh]" : "h-[var(--sheet-peek-height,220px)]"
          )}
        >
          {/* Drag handle — acts as expand/collapse affordance */}
          <button
            type="button"
            aria-label={sheetMode === "expanded" ? "Collapse results panel" : "Expand results panel"}
            onClick={() => setSheetMode(sheetMode === "expanded" ? "peek" : "expanded")}
            className="flex shrink-0 cursor-grab items-center justify-center py-3 active:cursor-grabbing"
            {...sheetDragHandlers}
          >
            <div className="drag-handle" />
          </button>

          {/* Scrollable content */}
          <div className="relative min-h-0 flex-1">
            <div
              className="scroll-shadow-top"
              data-visible={String(showTopShadow)}
              aria-hidden
            />
            <div
              ref={scrollRef}
              className="h-full overflow-y-auto scrollbar-hide"
            >
              <div ref={topSentinelRef} data-sentinel="top" className="h-px" />
              {children}
              <div ref={bottomSentinelRef} data-sentinel="bottom" className="h-px" />
            </div>
            <div
              className="scroll-shadow-bottom"
              data-visible={String(showBottomShadow)}
              aria-hidden
            />
          </div>

          {/* Screen-reader live region for state changes */}
          <div className="sr-only" aria-live="polite">
            {sheetMode === "expanded" ? "Results panel expanded" : "Results panel collapsed"}
          </div>
        </div>
      ) : (
        /* --- Desktop resizable side panel --- */
        <div className="pointer-events-none absolute inset-0 z-base p-4 sm:p-6">
          <div
            role="region"
            aria-label="Results panel"
            style={{ width: `${panelWidth}px` }}
            className={cn(
              "pointer-events-auto relative flex h-full flex-col rounded-xl panel-surface-neutral shadow-lg",
              isResizing ? "select-none" : "panel-resizable"
            )}
          >
            {/* Scrollable content */}
            <div className="relative min-h-0 flex-1">
              <div
                className="scroll-shadow-top rounded-t-xl"
                data-visible={String(showTopShadow)}
                aria-hidden
              />
              <div
                ref={scrollRef}
                className="h-full overflow-y-auto rounded-xl scrollbar-hide"
              >
                <div ref={topSentinelRef} data-sentinel="top" className="h-px" />
                {children}
                <div ref={bottomSentinelRef} data-sentinel="bottom" className="h-px" />
              </div>
              <div
                className="scroll-shadow-bottom rounded-b-xl"
                data-visible={String(showBottomShadow)}
                aria-hidden
              />
            </div>

            {/* Resize drag handle (right edge) */}
            <div
              role="separator"
              aria-orientation="vertical"
              aria-label={`Resize panel, ${Math.round(panelWidth)} pixels wide`}
              aria-valuemin={PANEL_MIN_WIDTH}
              aria-valuemax={PANEL_MAX_WIDTH}
              aria-valuenow={Math.round(panelWidth)}
              tabIndex={0}
              className="panel-resize-handle"
              {...resizeHandlers}
            />
          </div>
        </div>
      )}
    </div>
  );
}

