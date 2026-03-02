import { Link } from "react-router-dom";
import { ChevronRight, Home } from "lucide-react";

export interface BreadcrumbSegment {
  label: string;
  href?: string;
}

interface BreadcrumbsProps {
  segments: BreadcrumbSegment[];
}

export function Breadcrumbs({ segments }: BreadcrumbsProps): JSX.Element {
  return (
    <nav aria-label="Breadcrumb" className="mb-4">
      <ol className="flex flex-wrap items-center gap-1.5 text-sm">
        <li className="flex items-center gap-1.5">
          <Link
            to="/"
            className="inline-flex items-center gap-1 text-disabled transition-colors duration-fast hover:text-secondary"
            aria-label="Home"
          >
            <Home className="h-3.5 w-3.5" aria-hidden />
            <span className="sr-only">Home</span>
          </Link>
        </li>

        {segments.map((segment, index) => {
          const isLast = index === segments.length - 1;
          return (
            <li key={segment.label} className="flex items-center gap-1.5">
              <ChevronRight className="h-3.5 w-3.5 text-disabled/60" aria-hidden />
              {isLast || !segment.href ? (
                <span className="font-medium text-primary" aria-current="page">
                  {segment.label}
                </span>
              ) : (
                <Link
                  to={segment.href}
                  className="text-disabled transition-colors duration-fast hover:text-secondary"
                >
                  {segment.label}
                </Link>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
