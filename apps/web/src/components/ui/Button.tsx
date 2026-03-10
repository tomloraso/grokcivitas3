import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import type { ButtonHTMLAttributes } from "react";

import { cn } from "../../shared/utils/cn";

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-md font-semibold transition-all duration-200 ease-out hover:scale-[1.02] active:scale-[0.98] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-hover disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        primary:
          "bg-brand-solid text-primary shadow-sm hover:bg-brand hover:text-primary active:bg-brand-solid",
        secondary:
          "border border-border bg-elevated text-primary hover:border-brand/60 hover:bg-brand/15",
        ghost: "bg-transparent text-secondary hover:bg-elevated hover:text-primary",
        compare:
          "rounded-xl border border-brand/25 bg-[rgba(10,20,40,0.65)] text-primary/90 backdrop-blur-sm hover:border-brand/50 hover:bg-brand/10 hover:text-primary hover:shadow-[0_0_18px_rgba(0,212,200,0.25)]"
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
