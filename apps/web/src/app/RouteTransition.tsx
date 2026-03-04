import { useLocation } from "react-router-dom";
import { useRef, type ReactNode } from "react";

import { cn } from "../shared/utils/cn";

interface RouteTransitionProps {
  children: ReactNode;
  className?: string;
}

/**
 * Wraps route content with a subtle fade-in + slide-up on navigation.
 * Uses a key derived from the pathname to re-trigger the CSS animation
 * on each route change. Fully disabled by `prefers-reduced-motion` via
 * the global CSS media query override.
 */
export function RouteTransition({ children, className }: RouteTransitionProps): JSX.Element {
  const { pathname } = useLocation();
  // Track the previous pathname to only animate on actual route changes
  const prevPathRef = useRef(pathname);
  const shouldAnimate = prevPathRef.current !== pathname;
  prevPathRef.current = pathname;

  return (
    <div key={pathname} className={cn(shouldAnimate && "route-enter", className)}>
      {children}
    </div>
  );
}
