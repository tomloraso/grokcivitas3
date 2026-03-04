import * as DialogPrimitive from "@radix-ui/react-dialog";
import * as VisuallyHidden from "@radix-ui/react-visually-hidden";
import type { ReactNode } from "react";

import { cn } from "../../shared/utils/cn";

interface SheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  children: ReactNode;
  side?: "left" | "right";
}

export function Sheet({
  open,
  onOpenChange,
  title,
  children,
  side = "right"
}: SheetProps): JSX.Element {
  return (
    <DialogPrimitive.Root open={open} onOpenChange={onOpenChange}>
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay className="fixed inset-0 z-modal bg-black/60 backdrop-blur-sm data-[state=closed]:animate-fade-out data-[state=open]:animate-fade-in" />
        <DialogPrimitive.Content
          className={cn(
            "fixed top-0 z-modal flex h-full w-[280px] flex-col border-border-subtle bg-canvas shadow-lg",
            "data-[state=closed]:duration-slow data-[state=open]:duration-slow",
            side === "right"
              ? "right-0 border-l data-[state=closed]:animate-slide-out-right data-[state=open]:animate-slide-in-right"
              : "left-0 border-r data-[state=closed]:animate-slide-out-left data-[state=open]:animate-slide-in-left"
          )}
        >
          <VisuallyHidden.Root>
            <DialogPrimitive.Title>{title}</DialogPrimitive.Title>
            <DialogPrimitive.Description>
              Use this panel to navigate the main sections of the website.
            </DialogPrimitive.Description>
          </VisuallyHidden.Root>
          {children}
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  );
}
