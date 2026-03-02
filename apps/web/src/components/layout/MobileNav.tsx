import { Link } from "react-router-dom";
import { X } from "lucide-react";

import { Sheet } from "../ui/Sheet";
import { cn } from "../../shared/utils/cn";

interface NavLink {
  readonly label: string;
  readonly href: string;
}

interface MobileNavProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  links: readonly NavLink[];
  currentPath: string;
}

export function MobileNav({
  open,
  onOpenChange,
  links,
  currentPath
}: MobileNavProps): JSX.Element {
  return (
    <Sheet open={open} onOpenChange={onOpenChange} title="Navigation menu" side="right">
      <div className="flex h-14 items-center justify-between border-b border-border-subtle/60 px-4">
        <span className="text-sm font-semibold text-primary">Menu</span>
        <button
          type="button"
          className="inline-flex h-10 w-10 items-center justify-center rounded-md text-secondary transition-colors duration-fast hover:bg-elevated/60 hover:text-primary"
          onClick={() => onOpenChange(false)}
          aria-label="Close navigation menu"
        >
          <X className="h-5 w-5" aria-hidden />
        </button>
      </div>

      <nav aria-label="Mobile navigation" className="flex flex-col gap-1 p-4">
        {links.map((link) => {
          const isActive = currentPath === link.href;
          return (
            <Link
              key={link.href}
              to={link.href}
              onClick={() => onOpenChange(false)}
              className={cn(
                "rounded-md px-3 py-2.5 text-sm font-medium transition-colors duration-fast",
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
    </Sheet>
  );
}
