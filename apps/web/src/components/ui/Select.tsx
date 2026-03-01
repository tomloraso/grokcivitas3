import * as SelectPrimitive from "@radix-ui/react-select";

import { cn } from "../../shared/utils/cn";

export interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

interface SelectProps {
  id?: string;
  value: string;
  onValueChange: (value: string) => void;
  options: SelectOption[];
  placeholder?: string;
  disabled?: boolean;
  name?: string;
  ariaLabel: string;
}

export function Select({
  id,
  value,
  onValueChange,
  options,
  placeholder,
  disabled = false,
  name,
  ariaLabel
}: SelectProps): JSX.Element {
  return (
    <SelectPrimitive.Root
      value={value}
      onValueChange={onValueChange}
      disabled={disabled}
      name={name}
    >
      <SelectPrimitive.Trigger
        id={id}
        aria-label={ariaLabel}
        className={cn(
          "flex h-11 w-full items-center justify-between rounded-md border border-border bg-elevated px-3 text-sm text-primary shadow-inner transition-colors duration-base",
          "hover:border-brand/40 focus:outline-none focus-visible:border-brand"
        )}
      >
        <SelectPrimitive.Value placeholder={placeholder ?? "Select an option"} />
        <SelectPrimitive.Icon className="text-secondary" aria-hidden>
          v
        </SelectPrimitive.Icon>
      </SelectPrimitive.Trigger>
      <SelectPrimitive.Portal>
        <SelectPrimitive.Content
          className="z-popover max-h-72 min-w-[var(--radix-select-trigger-width)] overflow-hidden rounded-md border border-border bg-surface shadow-md"
          position="popper"
          sideOffset={6}
        >
          <SelectPrimitive.Viewport className="p-1">
            {options.map((option) => (
              <SelectPrimitive.Item
                key={option.value}
                value={option.value}
                disabled={option.disabled}
                className={cn(
                  "relative flex cursor-default select-none items-center rounded-sm px-3 py-2 text-sm text-secondary outline-none transition-colors duration-fast",
                  "focus:bg-brand/20 focus:text-primary data-[state=checked]:text-primary data-[disabled]:cursor-not-allowed data-[disabled]:opacity-45"
                )}
              >
                <SelectPrimitive.ItemText>{option.label}</SelectPrimitive.ItemText>
              </SelectPrimitive.Item>
            ))}
          </SelectPrimitive.Viewport>
        </SelectPrimitive.Content>
      </SelectPrimitive.Portal>
    </SelectPrimitive.Root>
  );
}
