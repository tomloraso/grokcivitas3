import { useCallback, useEffect, useRef, useState } from "react";

/* ── Constants ─────────────────────────────────────────────── */

const WIDTH_STORAGE_KEY = "civitas:panel-width";
const DEFAULT_WIDTH = 380;
const MIN_WIDTH = 280;
const MAX_WIDTH = 480;
const PEEK_THRESHOLD = 40; // px drag past peek to snap expanded/collapsed

export type SheetMode = "peek" | "expanded";

export { MIN_WIDTH as PANEL_MIN_WIDTH, MAX_WIDTH as PANEL_MAX_WIDTH };

/* ── Types ─────────────────────────────────────────────────── */

interface PanelState {
  /** Desktop: panel width in px */
  panelWidth: number;
  /** Mobile: bottom-sheet mode */
  sheetMode: SheetMode;
}

interface UsePanelStateResult {
  /** Desktop: current panel width in px */
  panelWidth: number;
  /** Mobile: bottom-sheet mode */
  sheetMode: SheetMode;
  setSheetMode: (mode: SheetMode) => void;
  /** Drag handler props for desktop resize handle */
  resizeHandlers: {
    onPointerDown: (e: React.PointerEvent) => void;
  };
  /** Drag handler props for mobile sheet drag handle */
  sheetDragHandlers: {
    onPointerDown: (e: React.PointerEvent) => void;
  };
  /** Ref to attach to the mobile sheet element for drag calculation */
  sheetRef: React.RefObject<HTMLDivElement>;
  /** Whether the user is currently dragging the resize handle */
  isResizing: boolean;
}

/* ── Persistence helpers ──────────────────────────────────── */

function readWidth(): number {
  try {
    const raw = localStorage.getItem(WIDTH_STORAGE_KEY);
    if (raw === null) return DEFAULT_WIDTH;
    const parsed = Number(raw);
    if (Number.isFinite(parsed)) {
      return Math.max(MIN_WIDTH, Math.min(MAX_WIDTH, parsed));
    }
    return DEFAULT_WIDTH;
  } catch {
    return DEFAULT_WIDTH;
  }
}

function writeWidth(value: number): void {
  try {
    localStorage.setItem(WIDTH_STORAGE_KEY, String(Math.round(value)));
  } catch {
    // ignore storage errors
  }
}

/* ── Hook ─────────────────────────────────────────────────── */

export function usePanelState(): UsePanelStateResult {
  const [state, setState] = useState<PanelState>({
    panelWidth: readWidth(),
    sheetMode: "peek",
  });

  const sheetRef = useRef<HTMLDivElement>(null);
  const dragStartY = useRef(0);
  const isResizingRef = useRef(false);
  const [isResizing, setIsResizing] = useState(false);

  const setSheetMode = useCallback((mode: SheetMode) => {
    setState((prev) => ({ ...prev, sheetMode: mode }));
  }, []);

  /* ── Desktop resize drag ────────────────────────────────── */

  const onResizePointerDown = useCallback(
    (e: React.PointerEvent) => {
      e.preventDefault();
      const startX = e.clientX;
      const startWidth = state.panelWidth;
      const target = e.currentTarget as HTMLElement;
      target.setPointerCapture(e.pointerId);
      isResizingRef.current = true;
      setIsResizing(true);

      // Disable text selection during drag
      document.body.style.userSelect = "none";
      document.body.style.cursor = "col-resize";

      const onMove = (me: PointerEvent): void => {
        const dx = me.clientX - startX;
        const newWidth = Math.max(MIN_WIDTH, Math.min(MAX_WIDTH, startWidth + dx));
        setState((prev) => ({ ...prev, panelWidth: newWidth }));
      };

      const onUp = (): void => {
        target.removeEventListener("pointermove", onMove);
        target.removeEventListener("pointerup", onUp);
        isResizingRef.current = false;
        setIsResizing(false);
        document.body.style.userSelect = "";
        document.body.style.cursor = "";
        // Persist final width
        setState((prev) => {
          writeWidth(prev.panelWidth);
          return prev;
        });
      };

      target.addEventListener("pointermove", onMove);
      target.addEventListener("pointerup", onUp);
    },
    [state.panelWidth]
  );

  /* ── Mobile sheet drag ──────────────────────────────────── */

  const onSheetPointerDown = useCallback(
    (e: React.PointerEvent) => {
      dragStartY.current = e.clientY;
      const target = e.currentTarget as HTMLElement;
      target.setPointerCapture(e.pointerId);

      const onMove = (me: PointerEvent): void => {
        const dy = dragStartY.current - me.clientY;
        const sheet = sheetRef.current;
        if (sheet) {
          const clampedDy = Math.max(-200, Math.min(200, dy));
          sheet.style.transform = `translateY(${-clampedDy}px)`;
        }
      };

      const onUp = (ue: PointerEvent): void => {
        target.removeEventListener("pointermove", onMove);
        target.removeEventListener("pointerup", onUp);
        const dy = dragStartY.current - ue.clientY;
        const sheet = sheetRef.current;
        if (sheet) {
          sheet.style.transform = "";
        }
        if (dy > PEEK_THRESHOLD) {
          setSheetMode("expanded");
        } else if (dy < -PEEK_THRESHOLD) {
          setSheetMode("peek");
        }
      };

      target.addEventListener("pointermove", onMove);
      target.addEventListener("pointerup", onUp);
    },
    [setSheetMode]
  );

  // Sync with localStorage on mount (handles SSR / stale closures)
  useEffect(() => {
    setState((prev) => ({ ...prev, panelWidth: readWidth() }));
  }, []);

  return {
    panelWidth: state.panelWidth,
    sheetMode: state.sheetMode,
    setSheetMode,
    resizeHandlers: { onPointerDown: onResizePointerDown },
    sheetDragHandlers: { onPointerDown: onSheetPointerDown },
    sheetRef,
    isResizing,
  };
}
