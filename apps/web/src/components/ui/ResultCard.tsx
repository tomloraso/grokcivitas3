import { Link } from "react-router-dom";
import { ChevronRight } from "lucide-react";

import { Card } from "./Card";

interface ResultCardProps {
  name: string;
  type: string;
  phase: string;
  postcode: string;
  distanceMiles?: number;
  href?: string;
}

export function ResultCard({
  name,
  type,
  phase,
  postcode,
  distanceMiles,
  href
}: ResultCardProps): JSX.Element {
  const content = (
    <>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <h2 className="text-lg leading-tight text-primary">{name}</h2>
        <div className="flex items-center gap-2">
          {distanceMiles !== undefined ? (
            <span className="rounded-full border border-brand/45 bg-brand/15 px-3 py-1 font-mono text-xs text-brand-hover">
              {distanceMiles.toFixed(2)} mi
            </span>
          ) : null}
          {href ? (
            <ChevronRight className="h-4 w-4 text-disabled transition-colors duration-fast group-hover:text-brand-hover" aria-hidden />
          ) : null}
        </div>
      </div>
      <dl className="grid grid-cols-1 gap-2 text-sm text-secondary sm:grid-cols-3">
        <div>
          <dt className="text-xs uppercase tracking-[0.08em] text-disabled">Type</dt>
          <dd className="mt-1 text-primary">{type}</dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-[0.08em] text-disabled">Phase</dt>
          <dd className="mt-1 text-primary">{phase}</dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-[0.08em] text-disabled">Postcode</dt>
          <dd className="mt-1 font-mono text-primary">{postcode}</dd>
        </div>
      </dl>
    </>
  );

  if (href) {
    return (
      <Link to={href} className="group block transition-transform duration-fast hover:scale-[1.01]" aria-label={`View profile for ${name}`}>
        <Card className="space-y-3 transition-colors duration-fast group-hover:border-brand/30">
          {content}
        </Card>
      </Link>
    );
  }

  return <Card className="space-y-3">{content}</Card>;
}
