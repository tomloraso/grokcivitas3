import type { ReactNode } from "react";
import { ChevronLeft, ChevronRight, ChevronUp, ChevronDown } from "lucide-react";

import { cn } from "../../shared/utils/cn";
import { useIsMobile } from "../../shared/hooks/useIsMobile";
import { usePanelState } from "../../shared/hooks/usePanelState";
import { useScrollShadow } from "../../shared/hooks/useScrollShadow";

interface MapOverlayLayoutProps {
  /** The map component rendered as the full-viewport background */
  map: ReactNode;
  /** Overlay panel content (search form, results, etc.) */
  children: ReactNode;
  /** Optional persistent summary shown when panel is collapsed */
  summary?: ReactNode;
  className?: string;
}

/**
 * Layout variant where the map stretches to full viewport and
 * UI panels float as glassmorphism overlays. Sets `data-layout="map-overlay"`
 * so CSS can conditionally suppress ambient glows.
 *
 * Desktop: collapsible side panel with scroll shadows.
 * Mobile: bottom-sheet overlay with peek/expanded states and drag handle.
 */
export function MapOverlayLayout({
  map,
  children,
  summary,
  className,
}: MapOverlayLayoutProps): JSX.Element {
  const isMobile = useIsMobile();
  const { collapsed, sheetMode, toggleCollapsed, setSheetMode, dragHandlers, sheetRef } =
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
          {/* Drag handle */}
          <div
            className="flex shrink-0 items-center justify-center py-2"
            {...dragHandlers}
          >
            <div className="drag-handle" />
          </div>

          {/* Accessible expand/collapse button */}
          <button
            type="button"
            aria-label={sheetMode === "expanded" ? "Collapse results panel" : "Expand results panel"}
            onClick={() => setSheetMode(sheetMode === "expanded" ? "peek" : "expanded")}
            className="mx-auto -mt-1 mb-1 flex items-center gap-1 rounded-full px-3 py-0.5 text-xs text-secondary transition-colors duration-fast hover:text-primary"
          >
            {sheetMode === "expanded" ? (
              <>
                <ChevronDown className="h-3.5 w-3.5" aria-hidden />
                <span>Collapse</span>
              </>
            ) : (
              <>
                <ChevronUp className="h-3.5 w-3.5" aria-hidden />
                <span>Expand</span>
              </>
            )}
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
        /* --- Desktop side panel --- */
        <div className="pointer-events-none absolute inset-0 z-base p-4 sm:p-6">
          <div
            role="region"
            aria-label="Results panel"
            className={cn(
              "pointer-events-auto flex h-full flex-col rounded-xl panel-surface-neutral shadow-lg panel-collapsible",
              collapsed ? "w-14" : "w-[min(420px,100%)]"
            )}
          >
            {/* Collapse toggle rail */}
            <button
              type="button"
              aria-label={collapsed ? "Expand results panel" : "Collapse results panel"}
              onClick={toggleCollapsed}
              className="flex shrink-0 items-center gap-2 rounded-t-xl border-b border-border-subtle/50 px-3 py-2 text-xs text-secondary transition-colors duration-fast hover:bg-white/5 hover:text-primary"
            >
              {collapsed ? (
                <ChevronRight className="h-4 w-4" aria-hidden />
              ) : (
                <ChevronLeft className="h-4 w-4" aria-hidden />
              )}
              {!collapsed && <span className="font-mono uppercase tracking-[0.08em]">Collapse</span>}
            </button>

            {/* Collapsed rail: show summary only */}
            {collapsed ? (
              <div className="flex flex-1 flex-col items-center gap-3 overflow-hidden py-4 text-xs text-secondary">
                {summary}
              </div>
            ) : (
              /* Expanded panel: scrollable content with scroll shadows */
              <div className="relative min-h-0 flex-1">
                <div
                  className="scroll-shadow-top rounded-none"
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
                  className="scroll-shadow-bottom rounded-none"
                  data-visible={String(showBottomShadow)}
                  aria-hidden
                />
              </div>
            )}

            {/* Screen-reader live region for state changes */}
            <div className="sr-only" aria-live="polite">
              {collapsed ? "Results panel collapsed" : "Results panel expanded"}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

