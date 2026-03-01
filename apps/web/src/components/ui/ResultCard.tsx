import { Card } from "./Card";

interface ResultCardProps {
  name: string;
  type: string;
  phase: string;
  postcode: string;
  distanceMiles?: number;
}

export function ResultCard({
  name,
  type,
  phase,
  postcode,
  distanceMiles
}: ResultCardProps): JSX.Element {
  return (
    <Card className="space-y-3">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <h2 className="text-lg leading-tight text-primary">{name}</h2>
        {distanceMiles !== undefined ? (
          <span className="rounded-full border border-brand/45 bg-brand/15 px-3 py-1 font-mono text-xs text-brand-hover">
            {distanceMiles.toFixed(2)} mi
          </span>
        ) : null}
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
    </Card>
  );
}
