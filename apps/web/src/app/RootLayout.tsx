import { Outlet, useLocation } from "react-router-dom";

import { AppShell } from "../components/layout/AppShell";
import { SiteHeader } from "../components/layout/SiteHeader";
import { SiteFooter } from "../components/layout/SiteFooter";
import { SkipToContent } from "../components/layout/SkipToContent";
import { ToastProvider } from "../components/ui/Toast";
import { TooltipProvider } from "../components/ui/Tooltip";
import { CompareSelectionProvider } from "../shared/context/CompareSelectionContext";
import { SearchContextProvider } from "../shared/context/SearchContext";
import { RouteTransition } from "./RouteTransition";
import { paths } from "../shared/routing/paths";

/**
 * Root layout shell wrapping all routes. Provides persistent site chrome:
 * skip-to-content, header, main content outlet, and footer.
 * Footer is hidden on the search/map page to maximize map real estate.
 */
export function RootLayout(): JSX.Element {
  const location = useLocation();
  const isMapPage = location.pathname === paths.home;

  return (
    <SearchContextProvider>
      <CompareSelectionProvider>
        <TooltipProvider delayDuration={300}>
          <ToastProvider>
            <AppShell>
              <SkipToContent />
              <SiteHeader />
              <main id="main-content">
                <RouteTransition>
                  <Outlet />
                </RouteTransition>
              </main>
              {!isMapPage && <SiteFooter />}
            </AppShell>
          </ToastProvider>
        </TooltipProvider>
      </CompareSelectionProvider>
    </SearchContextProvider>
  );
}
