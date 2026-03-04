import { useCallback, useEffect, useRef, useState } from "react";

interface ScrollShadowState {
  showTop: boolean;
  showBottom: boolean;
}

interface UseScrollShadowResult {
  scrollRef: React.RefObject<HTMLDivElement>;
  topSentinelRef: React.RefCallback<HTMLDivElement>;
  bottomSentinelRef: React.RefCallback<HTMLDivElement>;
  showTopShadow: boolean;
  showBottomShadow: boolean;
}

/**
 * Observes sentinel elements at the top/bottom of a scrollable container
 * to toggle scroll-shadow visibility using IntersectionObserver.
 */
export function useScrollShadow(): UseScrollShadowResult {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [state, setState] = useState<ScrollShadowState>({
    showTop: false,
    showBottom: false,
  });

  const observerRef = useRef<IntersectionObserver | null>(null);
  const topNodeRef = useRef<HTMLDivElement | null>(null);
  const bottomNodeRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const root = scrollRef.current;
    if (!root) return;

    const observer = new IntersectionObserver(
      (entries) => {
        setState((prev) => {
          let next = prev;
          for (const entry of entries) {
            const id = (entry.target as HTMLElement).dataset.sentinel;
            if (id === "top") {
              const showTop = !entry.isIntersecting;
              if (showTop !== prev.showTop) {
                next = { ...next, showTop };
              }
            } else if (id === "bottom") {
              const showBottom = !entry.isIntersecting;
              if (showBottom !== prev.showBottom) {
                next = { ...next, showBottom };
              }
            }
          }
          return next;
        });
      },
      { root, threshold: 0 }
    );

    observerRef.current = observer;

    if (topNodeRef.current) observer.observe(topNodeRef.current);
    if (bottomNodeRef.current) observer.observe(bottomNodeRef.current);

    return () => {
      observer.disconnect();
    };
  }, []);

  const topSentinelRef = useCallback((node: HTMLDivElement | null) => {
    if (topNodeRef.current && observerRef.current) {
      observerRef.current.unobserve(topNodeRef.current);
    }
    topNodeRef.current = node;
    if (node && observerRef.current) {
      observerRef.current.observe(node);
    }
  }, []);

  const bottomSentinelRef = useCallback((node: HTMLDivElement | null) => {
    if (bottomNodeRef.current && observerRef.current) {
      observerRef.current.unobserve(bottomNodeRef.current);
    }
    bottomNodeRef.current = node;
    if (node && observerRef.current) {
      observerRef.current.observe(node);
    }
  }, []);

  return {
    scrollRef,
    topSentinelRef,
    bottomSentinelRef,
    showTopShadow: state.showTop,
    showBottomShadow: state.showBottom,
  };
}
