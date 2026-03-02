import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { Menu } from "lucide-react";

import { cn } from "../../shared/utils/cn";
import { paths } from "../../shared/routing/paths";
import { MobileNav } from "./MobileNav";

const NAV_LINKS = [{ label: "Search", href: paths.home }] as const;

export function SiteHeader(): JSX.Element {
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();
  const isMapPage = location.pathname === paths.home;

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
          className="group flex items-center gap-2 text-lg font-display font-bold tracking-tight text-primary transition-colors duration-fast hover:text-brand-hover"
          aria-label="Civitas - return to home"
        >
          <span className="inline-flex h-7 w-7 items-center justify-center rounded-md bg-brand-solid text-xs font-bold text-white shadow-inner transition-transform duration-fast group-hover:scale-105">
            C
          </span>
          <span>Civitas</span>
        </Link>

        <nav aria-label="Primary" className="hidden items-center gap-1 md:flex">
          {NAV_LINKS.map((link) => {
            const isActive = location.pathname === link.href;
            return (
              <Link
                key={link.href}
                to={link.href}
                className={cn(
                  "rounded-md px-3 py-1.5 text-sm font-medium transition-colors duration-fast",
                  isActive
                    ? "bg-brand/15 text-brand-hover"
                    : "text-secondary hover:bg-elevated/60 hover:text-primary"
                )}
                aria-current={isActive ? "page" : undefined}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>

        <button
          type="button"
          className="inline-flex h-10 w-10 items-center justify-center rounded-md text-secondary transition-colors duration-fast hover:bg-elevated/60 hover:text-primary md:hidden"
          onClick={() => setMobileOpen(true)}
          aria-label="Open navigation menu"
        >
          <Menu className="h-5 w-5" aria-hidden />
        </button>
      </div>

      <MobileNav
        open={mobileOpen}
        onOpenChange={setMobileOpen}
        links={NAV_LINKS}
        currentPath={location.pathname}
      />
    </header>
  );
}
