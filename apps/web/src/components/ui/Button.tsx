import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import type { ButtonHTMLAttributes } from "react";

import { cn } from "../../shared/utils/cn";

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-md font-semibold transition-colors duration-base focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-hover disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        primary:
          "bg-brand-solid text-primary shadow-sm hover:bg-brand hover:text-primary active:bg-brand-solid",
        secondary:
          "border border-border bg-elevated text-primary hover:border-brand/60 hover:bg-brand/15",
        ghost: "bg-transparent text-secondary hover:bg-elevated hover:text-primary",
        compare: "btn-compare focus-visible:ring-0"
      },
      size: {
        default: "h-11 min-w-20 px-4 text-sm",
        sm: "h-9 min-w-16 px-3 text-xs",
        none: ""
      }
    },
    defaultVariants: {
      variant: "primary",
      size: "default"
    }
  }
);

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

export function Button({
  className,
  variant,
  size,
  asChild = false,
  ...props
}: ButtonProps): JSX.Element {
  const Component = asChild ? Slot : "button";
  return <Component className={cn(buttonVariants({ variant, size }), className)} {...props} />;
}
