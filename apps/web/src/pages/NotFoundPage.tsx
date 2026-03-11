import { Link } from "react-router-dom";
import { SearchX } from "lucide-react";

import { PageMeta } from "../components/layout/PageMeta";
import { Button } from "../components/ui/Button";
import { paths } from "../shared/routing/paths";

export function NotFoundPage(): JSX.Element {
  return (
    <div className="mx-auto flex min-h-[60vh] max-w-md flex-col items-center justify-center px-4 text-center">
      <PageMeta
        title="Page not found"
        description="The page you requested could not be found."
        noIndex
      />
      <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-full border border-border-subtle bg-elevated/40">
        <SearchX className="h-8 w-8 text-secondary" aria-hidden />
      </div>

      <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">Page not found</h1>
      <p className="mt-3 text-secondary">
        The page you&rsquo;re looking for doesn&rsquo;t exist or has been moved.
      </p>

      <Link to={paths.home} className="mt-8">
        <Button variant="primary">Back to search</Button>
      </Link>
    </div>
  );
}
