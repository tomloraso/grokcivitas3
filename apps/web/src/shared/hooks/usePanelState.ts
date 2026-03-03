import { useCallback, useEffect, useRef, useState } from "react";

const STORAGE_KEY = "civitas:panel-collapsed";
const PEEK_THRESHOLD = 40; // px drag past peek to snap expanded/collapsed

export type SheetMode = "peek" | "expanded";

interface PanelState {
  /** Desktop: panel collapsed to rail */
  collapsed: boolean;
  /** Mobile: bottom-sheet mode */
  sheetMode: SheetMode;
}

interface UsePanelStateResult {
  collapsed: boolean;
  sheetMode: SheetMode;
  toggleCollapsed: () => void;
  setSheetMode: (mode: SheetMode) => void;
  /** Drag handler props for mobile sheet drag handle */
  dragHandlers: {
    onPointerDown: (e: React.PointerEvent) => void;
  };
  /** Ref to attach to the mobile sheet element for drag calculation */
  sheetRef: React.RefObject<HTMLDivElement>;
}

function readCollapsed(): boolean {
  try {
    return localStorage.getItem(STORAGE_KEY) === "true";
  } catch {
    return false;
  }
}

function writeCollapsed(value: boolean): void {
  try {
    localStorage.setItem(STORAGE_KEY, String(value));
  } catch {
    // ignore storage errors
  }
}

export function usePanelState(): UsePanelStateResult {
  const [state, setState] = useState<PanelState>({
    collapsed: readCollapsed(),
    sheetMode: "peek",
  });

  const sheetRef = useRef<HTMLDivElement>(null);
  const dragStartY = useRef(0);

  const toggleCollapsed = useCallback(() => {
    setState((prev) => {
      const next = !prev.collapsed;
      writeCollapsed(next);
      return { ...prev, collapsed: next };
    });
  }, []);

  const setSheetMode = useCallback((mode: SheetMode) => {
    setState((prev) => ({ ...prev, sheetMode: mode }));
  }, []);

  // Drag-to-expand/collapse for mobile sheet
  const onPointerDown = useCallback(
    (e: React.PointerEvent) => {
      dragStartY.current = e.clientY;
      const target = e.currentTarget as HTMLElement;
      target.setPointerCapture(e.pointerId);

      const onMove = (me: PointerEvent): void => {
        const dy = dragStartY.current - me.clientY;
        // Visual feedback could be added here; we keep it simple for now
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
    setState((prev) => ({ ...prev, collapsed: readCollapsed() }));
  }, []);

  return {
    collapsed: state.collapsed,
    sheetMode: state.sheetMode,
    toggleCollapsed,
    setSheetMode,
    dragHandlers: { onPointerDown },
    sheetRef,
  };
}
