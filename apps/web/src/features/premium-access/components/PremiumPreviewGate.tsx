import { LockKeyhole, Sparkles } from "lucide-react";
import type { ReactNode } from "react";
import { Link, useLocation } from "react-router-dom";

import { Button } from "../../../components/ui/Button";
import { cn } from "../../../shared/utils/cn";
import { buildAccessActionHref, getPremiumPaywallCopy } from "../copy";
import type { SectionAccessVM } from "../types";

interface PremiumPreviewGateProps {
  access: SectionAccessVM;
  teaser: ReactNode;
  unavailable: ReactNode;
  children: ReactNode;
  className?: string;
}

export function PremiumPreviewGate({
  access,
  teaser,
  unavailable,
  children,
  className,
}: PremiumPreviewGateProps): JSX.Element {
  const location = useLocation();
  const returnTo = `${location.pathname}${location.search}`;

  if (access.state === "unavailable") {
    return <>{unavailable}</>;
  }

  if (access.state === "available") {
    return (
      <div
        className={cn(
          "rounded-md border border-brand/30 bg-brand/5 p-4 shadow-[0_0_0_1px_rgba(117,86,255,0.08)] sm:p-5",
          className
        )}
      >
        {children}
      </div>
    );
  }

  const copy = getPremiumPaywallCopy({
    capabilityKey: access.capabilityKey,
    schoolName: access.schoolName,
    requiresAuth: access.requiresAuth,
  });
  const actionHref = buildAccessActionHref({ access, returnTo });

  return (
    <div className={cn("space-y-4", className)}>
      <div className="relative overflow-hidden rounded-md border border-brand/20 bg-surface/70">
        <div className="max-h-48 overflow-hidden p-4 sm:p-5">{teaser}</div>
        <div className="pointer-events-none absolute inset-x-0 bottom-0 h-20 bg-gradient-to-t from-canvas via-canvas/95 to-transparent" />
      </div>

      <div className="rounded-md border border-brand/30 bg-brand/5 p-4 sm:p-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="space-y-2">
            <p className="inline-flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.12em] text-brand">
              <Sparkles className="h-3.5 w-3.5" aria-hidden />
              Premium preview
            </p>
            <div className="space-y-1">
              <h3 className="text-base font-semibold text-primary">{copy.title}</h3>
              <p className="text-sm text-secondary">{copy.description}</p>
            </div>
          </div>

          <Button asChild variant="primary">
            <Link to={actionHref}>
              <LockKeyhole className="mr-1.5 h-4 w-4" aria-hidden />
              {copy.buttonLabel}
            </Link>
          </Button>
        </div>
      </div>
    </div>
  );
}
