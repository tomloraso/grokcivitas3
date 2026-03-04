import { cva, type VariantProps } from "class-variance-authority";
import type { HTMLAttributes } from "react";

import { cn } from "../../shared/utils/cn";

const badgeVariants = cva(
  "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold tracking-wide transition-colors duration-fast",
  {
    variants: {
      variant: {
        default:
          "border border-brand/30 bg-brand/15 text-brand-hover",
        success:
          "border border-success/30 bg-success/15 text-success",
        warning:
          "border border-warning/30 bg-warning/15 text-warning",
        danger:
          "border border-danger/30 bg-danger/15 text-danger",
        info:
          "border border-info/30 bg-info/15 text-info",
        outline:
          "border border-border bg-transparent text-secondary"
      }
    },
    defaultVariants: {
      variant: "default"
    }
  }
);

export interface BadgeProps
  extends HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps): JSX.Element {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />;
}
