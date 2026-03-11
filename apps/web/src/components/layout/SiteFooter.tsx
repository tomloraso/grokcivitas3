import { Link } from "react-router-dom";
import { siteConfig } from "../../shared/config/site";
import { paths } from "../../shared/routing/paths";

const FOOTER_LINKS = [
  { label: "About", to: paths.about },
  { label: "Data Sources", to: paths.dataSources },
  { label: "Contact", to: paths.contact },
  { label: "Privacy", to: paths.privacy },
  { label: "Terms", to: paths.terms },
  { label: "Accessibility", to: paths.accessibility }
] as const;

export function SiteFooter(): JSX.Element {
  return (
    <footer
      className="border-t border-border-subtle/60 bg-canvas/60"
      role="contentinfo"
    >
      <div className="mx-auto flex max-w-[1200px] flex-col items-center gap-4 px-4 py-8 sm:flex-row sm:justify-between sm:px-6 lg:px-8">
        <Link
          to={paths.home}
          className="text-xs font-display font-semibold tracking-[0.18em] text-secondary transition-opacity duration-fast hover:opacity-80"
        >
          {siteConfig.shortName}
        </Link>

        <nav
          aria-label="Footer"
          className="flex flex-wrap items-center justify-center gap-4 sm:justify-start"
        >
          {FOOTER_LINKS.map((link) => (
            <Link
              key={link.label}
              to={link.to}
              className="text-xs text-disabled transition-colors duration-fast hover:text-secondary"
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <p className="text-xs text-disabled">
          &copy; {new Date().getFullYear()} {siteConfig.productName}. All data sourced from UK government.
        </p>

        <p className="text-[10px] text-disabled/60">
          Map powered by{" "}
          <a href="https://maplibre.org" target="_blank" rel="noopener noreferrer" className="underline hover:text-secondary transition-colors duration-fast">MapLibre</a>
          {" &middot; "}
          <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer" className="underline hover:text-secondary transition-colors duration-fast">&copy; OpenStreetMap</a>
        </p>
      </div>
    </footer>
  );
}
