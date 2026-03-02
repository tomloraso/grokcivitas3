import { render, type RenderOptions, type RenderResult } from "@testing-library/react";
import type { ReactElement } from "react";
import { MemoryRouter } from "react-router-dom";

interface ProviderOptions extends Omit<RenderOptions, "wrapper"> {
  /** Initial route entries for MemoryRouter. Defaults to ["/"] */
  initialEntries?: string[];
}

export function renderWithProviders(
  ui: ReactElement,
  options?: ProviderOptions
): RenderResult {
  const { initialEntries = ["/"], ...renderOptions } = options ?? {};

  function Wrapper({ children }: { children: React.ReactNode }) {
    return <MemoryRouter initialEntries={initialEntries}>{children}</MemoryRouter>;
  }

  return render(ui, { wrapper: Wrapper, ...renderOptions });
}
