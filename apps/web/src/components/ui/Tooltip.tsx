import * as TooltipPrimitive from "@radix-ui/react-tooltip";
import { forwardRef, type ComponentPropsWithoutRef, type ElementRef } from "react";

import { cn } from "../../shared/utils/cn";

/* ------------------------------------------------------------------ */
/* Provider - wrap the app or a subtree                                */
/* ------------------------------------------------------------------ */

export const TooltipProvider = TooltipPrimitive.Provider;

/* ------------------------------------------------------------------ */
/* Root + Trigger                                                      */
/* ------------------------------------------------------------------ */

export const Tooltip = TooltipPrimitive.Root;
export const TooltipTrigger = TooltipPrimitive.Trigger;

/* ------------------------------------------------------------------ */
/* Content                                                             */
/* ------------------------------------------------------------------ */

export const TooltipContent = forwardRef<
  ElementRef<typeof TooltipPrimitive.Content>,
  ComponentPropsWithoutRef<typeof TooltipPrimitive.Content>
>(({ className, sideOffset = 6, ...props }, ref) => (
  <TooltipPrimitive.Portal>
    <TooltipPrimitive.Content
      ref={ref}
      sideOffset={sideOffset}
      className={cn(
        "z-popover max-w-xs rounded-md border border-border-subtle bg-elevated px-3 py-2 text-xs leading-relaxed text-primary shadow-md",
        "data-[state=delayed-open]:animate-fade-in data-[state=closed]:animate-fade-out",
        className
      )}
      {...props}
    />
  </TooltipPrimitive.Portal>
));
TooltipContent.displayName = "TooltipContent";
