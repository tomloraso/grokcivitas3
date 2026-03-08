import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { SignInFeature } from "./SignInFeature";
import { useAuth } from "./useAuth";
import { ThemeProvider } from "../../app/providers/ThemeProvider";

vi.mock("./useAuth", () => ({
  useAuth: vi.fn(),
}));

const useAuthMock = vi.mocked(useAuth);

describe("SignInFeature", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    useAuthMock.mockReturnValue({
      isLoading: false,
      session: {
        state: "anonymous",
        user: null,
        expiresAt: null,
        anonymousReason: "missing",
      },
      reloadSession: vi.fn().mockResolvedValue(undefined),
      startSignIn: vi.fn().mockResolvedValue(undefined),
      signOut: vi.fn().mockResolvedValue(undefined),
    });
  });

  it("submits the email address and return target through the auth feature", async () => {
    const user = userEvent.setup();
    const startSignIn = vi.fn().mockResolvedValue(undefined);
    useAuthMock.mockReturnValue({
      isLoading: false,
      session: {
        state: "anonymous",
        user: null,
        expiresAt: null,
        anonymousReason: "missing",
      },
      reloadSession: vi.fn().mockResolvedValue(undefined),
      startSignIn,
      signOut: vi.fn().mockResolvedValue(undefined),
    });

    render(
      <ThemeProvider>
        <MemoryRouter initialEntries={["/sign-in?returnTo=%2Fcompare"]}>
          <Routes>
            <Route path="/sign-in" element={<SignInFeature />} />
          </Routes>
        </MemoryRouter>
      </ThemeProvider>
    );

    await user.type(screen.getByLabelText(/Email address/i), "person@example.com");
    await user.click(screen.getByRole("button", { name: "Continue" }));

    await waitFor(() => {
      expect(startSignIn).toHaveBeenCalledWith("person@example.com", "/compare");
    });
  });

  it("renders an auth error banner from the callback redirect query string", () => {
    render(
      <ThemeProvider>
        <MemoryRouter initialEntries={["/sign-in?error=invalid_state"]}>
          <Routes>
            <Route path="/sign-in" element={<SignInFeature />} />
          </Routes>
        </MemoryRouter>
      </ThemeProvider>
    );

    expect(
      screen.getByText("Your sign-in link has expired or could not be verified.")
    ).toBeInTheDocument();
  });

  it("renders an explicit message when the provider does not verify the email address", () => {
    render(
      <ThemeProvider>
        <MemoryRouter initialEntries={["/sign-in?error=unverified_email"]}>
          <Routes>
            <Route path="/sign-in" element={<SignInFeature />} />
          </Routes>
        </MemoryRouter>
      </ThemeProvider>
    );

    expect(
      screen.getByText("Your identity provider did not confirm this email address.")
    ).toBeInTheDocument();
  });
});
