import type { ReactNode } from "react";

import { cn } from "../../shared/utils/cn";

interface FieldProps {
  label: string;
  htmlFor?: string;
  helperText?: string;
  errorText?: string;
  required?: boolean;
  children: ReactNode;
  className?: string;
}

export function Field({
  label,
  htmlFor,
  helperText,
  errorText,
  required = false,
  children,
  className
}: FieldProps): JSX.Element {
  const helperId = htmlFor ? `${htmlFor}-helper` : undefined;
  const errorId = htmlFor ? `${htmlFor}-error` : undefined;
  return (
    <div className={cn("space-y-2", className)}>
      <label
        htmlFor={htmlFor}
        className="block text-xs font-semibold uppercase tracking-[0.08em] text-secondary"
      >
        {label}
        {required ? <span className="ml-1 text-brand">*</span> : null}
      </label>
      {children}
      {helperText ? (
        <p id={helperId} className="text-xs text-secondary">
          {helperText}
        </p>
      ) : null}
      {errorText ? (
        <p id={errorId} className="text-xs font-medium text-danger">
          {errorText}
        </p>
      ) : null}
    </div>
  );
}
