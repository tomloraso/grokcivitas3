import { forwardRef, type InputHTMLAttributes } from "react";

import { cn } from "../../shared/utils/cn";

export const TextInput = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  function TextInput({ className, type = "text", ...props }, ref): JSX.Element {
    return (
      <input
        ref={ref}
        type={type}
        className={cn(
          "h-11 w-full rounded-md border border-border bg-elevated px-3 text-sm text-primary shadow-inner placeholder:text-disabled",
          "transition-colors duration-base hover:border-brand/40 focus-visible:border-brand focus-visible:outline-none",
          className
        )}
        {...props}
      />
    );
  }
);
