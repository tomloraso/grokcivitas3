import { useParams, Link } from "react-router-dom";

import { PageContainer } from "../../components/layout/PageContainer";
import { Breadcrumbs } from "../../components/layout/Breadcrumbs";
import { paths } from "../../shared/routing/paths";

/**
 * Minimal placeholder for the school profile route.
 * Phase 1G replaces this with the full profile page.
 */
export function SchoolProfilePlaceholder(): JSX.Element {
  const { urn } = useParams<{ urn: string }>();

  return (
    <PageContainer>
      <Breadcrumbs
        segments={[{ label: `School ${urn ?? ""}` }]}
      />
      <div className="panel-surface rounded-xl p-6 sm:p-8">
        <p className="font-mono text-xs uppercase tracking-[0.14em] text-secondary">
          School Profile
        </p>
        <h1 className="mt-2 text-2xl leading-tight sm:text-3xl">
          URN: {urn}
        </h1>
        <p className="mt-4 text-sm text-secondary">
          Full school profile coming in Phase 1G. This route confirms navigation from search results is wired.
        </p>
        <Link
          to={paths.home}
          className="mt-6 inline-block text-sm font-medium text-brand transition-colors duration-fast hover:text-brand-hover"
        >
          &larr; Back to search
        </Link>
      </div>
    </PageContainer>
  );
}
