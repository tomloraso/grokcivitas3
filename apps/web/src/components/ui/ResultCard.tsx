import { Link } from "react-router-dom";
import { ChevronRight } from "lucide-react";

import { cn } from "../../shared/utils/cn";
import { Card } from "./Card";

interface ResultCardProps {
  /** Unique identifier for hover-linking with map markers */
  id?: string;
  name: string;
  type: string;
  phase: string;
  postcode: string;
  distanceMiles?: number;
  href?: string;
  /** Navigation state passed to react-router Link */
  linkState?: Record<string, unknown>;
  /** Optional animation delay for staggered entry */
  style?: React.CSSProperties;
  className?: string;
  /** Whether this card is highlighted via map interaction */
  isActive?: boolean;
  /** Callback when the card gains/loses hover or keyboard focus */
  onHover?: (id: string | null) => void;
}

export function ResultCard({
  id,
  name,
  type,
  phase,
  postcode,
  distanceMiles,
  href,
  linkState,
  style,
  className,
  isActive,
  onHover,
}: ResultCardProps): JSX.Element {
  const hoverHandlers = id && onHover
    ? {
        onMouseEnter: () => onHover(id),
        onMouseLeave: () => onHover(null),
        onFocus: () => onHover(id),
        onBlur: () => onHover(null),
      }
    : {};
  const content = (
    <>
      <div className="grid grid-cols-[1fr_auto] items-start gap-3">
        <h2 className="min-w-0 text-lg font-semibold leading-snug text-primary">{name}</h2>
        <div className="flex shrink-0 items-center gap-2">
          {distanceMiles !== undefined ? (
            <span className="whitespace-nowrap rounded-full border border-brand/45 bg-brand/15 px-3 py-1 font-mono text-xs text-brand-hover">
              {distanceMiles.toFixed(2)} mi
            </span>
          ) : null}
          {href ? (
            <ChevronRight className="h-4 w-4 text-disabled transition-colors duration-fast group-hover:text-brand-hover" aria-hidden />
          ) : null}
        </div>
      </div>
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm">
        <span className="text-secondary">{type}</span>
        <span className="text-border-subtle/80" aria-hidden>&middot;</span>
        <span className="text-secondary">{phase}</span>
        <span className="text-border-subtle/80" aria-hidden>&middot;</span>
        <span className="font-mono text-secondary">{postcode}</span>
      </div>
    </>
  );

  const activeRing = isActive
    ? "border-brand/40 shadow-[0_0_20px_rgba(139,92,246,0.18)] scale-[1.01]"
    : "";

  if (href) {
    return (
      <Link
        to={href}
        state={linkState}
        className={cn("group block result-card-enter", className)}
        aria-label={`View profile for ${name}`}
        style={style}
        {...hoverHandlers}
      >
        <Card className={cn("space-y-3 transition-all duration-fast group-hover:scale-[1.01] group-hover:border-brand/30 group-hover:shadow-[0_0_20px_rgba(139,92,246,0.12)]", activeRing)}>
          {content}
        </Card>
      </Link>
    );
  }

  return (
    <Card className={cn("space-y-3 result-card-enter", activeRing, className)} style={style} {...hoverHandlers}>
      {content}
    </Card>
  );
}
