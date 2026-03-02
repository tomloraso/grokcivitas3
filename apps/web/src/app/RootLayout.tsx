import { Outlet } from "react-router-dom";

import { AppShell } from "../components/layout/AppShell";
import { SiteHeader } from "../components/layout/SiteHeader";
import { SiteFooter } from "../components/layout/SiteFooter";
import { SkipToContent } from "../components/layout/SkipToContent";

/**
 * Root layout shell wrapping all routes. Provides persistent site chrome:
 * skip-to-content, header, main content outlet, and footer.
 */
export function RootLayout(): JSX.Element {
  return (
    <AppShell>
      <SkipToContent />
      <SiteHeader />
      <main id="main-content">
        <Outlet />
      </main>
      <SiteFooter />
    </AppShell>
  );
}
