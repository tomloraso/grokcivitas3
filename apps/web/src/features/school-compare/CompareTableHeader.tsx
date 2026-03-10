import { Link } from "react-router-dom";

import type { CompareSchoolColumnVM } from "./types";

interface CompareTableHeaderProps {
  schools: CompareSchoolColumnVM[];
  labelWidth: number;
  columnWidth: number;
}

export function CompareTableHeader({
  schools,
  labelWidth,
  columnWidth,
}: CompareTableHeaderProps): JSX.Element {
  return (
    <thead>
      <tr>
        <th
          scope="col"
          className="sticky left-0 top-0 z-30 bg-canvas/95 px-4 py-3 text-left align-bottom backdrop-blur"
          style={{ minWidth: labelWidth, width: labelWidth }}
        >
          <span className="text-xs font-semibold tracking-[0.04em] text-disabled">
            Metric
          </span>
        </th>

        {schools.map((school) => (
          <th
            key={school.urn}
            scope="col"
            className="sticky top-0 z-20 bg-canvas/95 px-4 py-3 text-left align-bottom backdrop-blur"
            style={{ minWidth: columnWidth }}
          >
            <Link
              to={school.profileHref}
              state={school.profileState}
              className="block transition-colors hover:text-brand-hover"
            >
              <p className="text-sm font-semibold leading-snug text-primary">
                {school.name}
              </p>
              <p className="mt-0.5 font-mono text-[10px] text-disabled">
                URN {school.urn}
              </p>
            </Link>
          </th>
        ))}
      </tr>
    </thead>
  );
}
