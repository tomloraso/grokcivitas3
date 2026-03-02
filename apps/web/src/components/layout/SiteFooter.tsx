import { Link } from "react-router-dom";
import { paths } from "../../shared/routing/paths";

const FOOTER_LINKS = [
  { label: "About", href: "#" },
  { label: "Contact", href: "#" },
  { label: "Privacy", href: "#" }
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
          className="text-sm font-display font-bold tracking-tight text-secondary transition-colors duration-fast hover:text-primary"
        >
          Civitas
        </Link>

        <nav aria-label="Footer" className="flex items-center gap-5">
          {FOOTER_LINKS.map((link) => (
            <a
              key={link.label}
              href={link.href}
              className="text-xs text-disabled transition-colors duration-fast hover:text-secondary"
            >
              {link.label}
            </a>
          ))}
        </nav>

        <p className="text-xs text-disabled">
          &copy; {new Date().getFullYear()} Civitas. All data sourced from UK government.
        </p>
      </div>
    </footer>
  );
}
