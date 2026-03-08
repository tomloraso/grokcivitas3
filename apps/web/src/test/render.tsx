import { render, type RenderOptions, type RenderResult } from "@testing-library/react";
import type { ReactElement, ReactNode } from "react";
import { MemoryRouter } from "react-router-dom";
import { ThemeProvider } from "../app/providers/ThemeProvider";
import { AuthProvider } from "../features/auth/AuthProvider";
import { ANONYMOUS_SESSION } from "../features/auth/types";

interface ProviderOptions extends Omit<RenderOptions, "wrapper"> {
  /** Initial route entries for MemoryRouter. Defaults to ["/"] */
  initialEntries?: string[];
}

export function renderWithProviders(
  ui: ReactElement,
  options?: ProviderOptions
): RenderResult {
  const { initialEntries = ["/"], ...renderOptions } = options ?? {};

  function Wrapper({ children }: { children: ReactNode }) {
    return (
      <ThemeProvider>
        <AuthProvider autoLoad={false} initialSession={ANONYMOUS_SESSION}>
          <MemoryRouter initialEntries={initialEntries}>{children}</MemoryRouter>
        </AuthProvider>
      </ThemeProvider>
    );
  }

  return render(ui, { wrapper: Wrapper, ...renderOptions });
}
