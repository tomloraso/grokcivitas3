import { Link, useLocation } from "react-router-dom";
import { Crown, LockKeyhole } from "lucide-react";

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
  accountAccessState?: "anonymous" | "free" | "pending" | "premium";
  hasCompareAccess?: boolean;
  onSignOut?: () => void;
  themeMode?: ThemeMode;
  onCycleTheme?: () => void;
}

export function SiteHeader({
  accountEmail = null,
  isAuthenticated = false,
  accountAccessState = "anonymous",
  hasCompareAccess = false,
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
  const compareLabel = `Compare ${compareCount}/4`;
  const returnTo = `${location.pathname}${location.search}`;
  const signInHref = paths.signIn(returnTo);
  const compareActionHref = isAuthenticated
    ? hasCompareAccess
      ? paths.compare(compareUrns)
      : paths.upgrade({
          capability: "premium_comparison",
          returnTo: paths.compare(compareUrns),
        })
    : paths.signIn(
        paths.upgrade({
          capability: "premium_comparison",
          returnTo: paths.compare(compareUrns),
        })
      );

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
              <Link to={compareActionHref} aria-label={`${compareLabel} selected`}>
                {!hasCompareAccess ? (
                  <LockKeyhole className="mr-1.5 h-3.5 w-3.5" aria-hidden />
                ) : null}
                {hasCompareAccess ? compareLabel : "Unlock compare"}
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
                <Link
                  to={paths.account}
                  className="hidden items-center gap-2 rounded-full border border-border-subtle/40 bg-surface/70 px-3 py-1 text-xs text-secondary transition-colors hover:border-brand/40 hover:text-primary sm:flex"
                >
                  <span className="max-w-[180px] truncate font-medium text-primary">
                    {accountEmail}
                  </span>
                  {accountAccessState === "premium" ? (
                    <span className="inline-flex items-center gap-1 rounded-full border border-brand/30 bg-brand/10 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.08em] text-brand">
                      <Crown className="h-3 w-3" aria-hidden />
                      Premium
                    </span>
                  ) : null}
                </Link>
              ) : null}
              <Button asChild variant="ghost" size="sm">
                <Link to={paths.account}>Account</Link>
              </Button>
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
      {compareCount >= 2 && !hasCompareAccess ? (
        <div className="border-t border-border-subtle/60 bg-brand/5 px-4 py-2 sm:px-6 lg:px-8">
          <div className="mx-auto flex max-w-[1200px] items-center gap-2 text-xs text-secondary">
            <LockKeyhole className="h-3.5 w-3.5 text-brand" aria-hidden />
            <span>Compare is included with Premium.</span>
          </div>
        </div>
      ) : null}
    </header>
  );
}
