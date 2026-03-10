import { Link, useLocation } from "react-router-dom";

import { Button } from "../../components/ui/Button";
import { cn } from "../../shared/utils/cn";
import { useCompareSelection } from "../../shared/context/CompareSelectionContext";
import { useSearchContext } from "../../shared/context/SearchContext";
import { readCompareUrlState } from "../../shared/routing/compareUrns";
import { paths } from "../../shared/routing/paths";
import type { ThemeMode } from "../../shared/theme/theme-mode";
import { ThemeModeToggle } from "./ThemeModeToggle";

interface SiteHeaderProps {
  accountEmail?: string | null;
  isAuthenticated?: boolean;
  onSignOut?: () => void;
  themeMode?: ThemeMode;
  onCycleTheme?: () => void;
}

export function SiteHeader({
  accountEmail = null,
  isAuthenticated = false,
  onSignOut,
  themeMode = "system",
  onCycleTheme = () => undefined,
}: SiteHeaderProps): JSX.Element {
  const location = useLocation();
  const isMapPage = location.pathname === paths.home;
  const isComparePage = location.pathname === paths.compare();
  const { search } = useSearchContext();
  const { items } = useCompareSelection();
  const compareRouteState = readCompareUrlState(new URLSearchParams(location.search));
  const selectionUrns = items.map((item) => item.urn);
  const compareUrns =
    isComparePage && compareRouteState.hasExplicitUrns
      ? compareRouteState.urns
      : selectionUrns;
  const compareCount = compareUrns.length;
  const compareHref = paths.compare(compareUrns);
  const compareLabel = `Compare ${compareCount}/4`;
  const returnTo = `${location.pathname}${location.search}`;
  const signInHref = paths.signIn(returnTo);

  return (
    <header
      className={cn(
        "sticky top-0 z-nav backdrop-blur-xl transition-colors duration-base",
        isMapPage
          ? "border-b border-transparent bg-transparent"
          : "border-b border-border-subtle/60 bg-canvas/80"
      )}
      role="banner"
    >
      <div className="mx-auto flex h-14 max-w-[1200px] items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link
          to={paths.home}
          className="text-sm font-display font-semibold tracking-[0.18em] text-primary transition-opacity duration-fast hover:opacity-80"
          aria-label="[BRAND] - return to home"
        >
          [BRAND]
        </Link>

        <div className="flex items-center gap-3">
          {isMapPage && search ? (
            <div
              className="hidden items-center gap-1.5 rounded-full border border-border-subtle/40 bg-surface/60 px-3 py-1 text-xs text-secondary backdrop-blur sm:flex"
              aria-label={`Searching ${search.postcode} within ${search.radius} miles`}
            >
              <span className="font-mono font-medium text-primary">{search.postcode}</span>
              <span className="text-disabled" aria-hidden>·</span>
              <span>{search.radius} mi</span>
              <span className="text-disabled" aria-hidden>·</span>
              <span>{search.count} {search.count === 1 ? "result" : "results"}</span>
            </div>
          ) : null}

          {compareCount >= 2 ? (
            <Button asChild variant="secondary" size="sm">
              <Link to={compareHref} aria-label={`${compareLabel} selected`}>
                {compareLabel}
              </Link>
            </Button>
          ) : (
            <Button
              type="button"
              variant="secondary"
              size="sm"
              disabled
              aria-label={`${compareLabel} selected`}
            >
              {compareLabel}
            </Button>
          )}

          {isAuthenticated ? (
            <>
              {accountEmail ? (
                <div className="hidden items-center rounded-full border border-border-subtle/40 bg-surface/70 px-3 py-1 text-xs text-secondary sm:flex">
                  <span className="max-w-[180px] truncate font-medium text-primary">
                    {accountEmail}
                  </span>
                </div>
              ) : null}
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={onSignOut}
              >
                Sign out
              </Button>
            </>
          ) : (
            <Button asChild variant="ghost" size="sm">
              <Link to={signInHref}>Sign in</Link>
            </Button>
          )}

          <ThemeModeToggle mode={themeMode} onCycle={onCycleTheme} />
        </div>
      </div>
    </header>
  );
}
