import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  __resetApiRequestCacheForTests,
  getSession,
  resetApiRequestCache,
  signOut,
  startSignIn,
} from "../../api/client";
import { AuthProvider } from "./AuthProvider";
import { useAuth } from "./useAuth";

vi.mock("../../api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../../api/client")>();
    return {
      ...actual,
      getSession: vi.fn(),
      resetApiRequestCache: vi.fn(),
      signOut: vi.fn(),
      startSignIn: vi.fn(),
    };
  });

const getSessionMock = vi.mocked(getSession);
const resetApiRequestCacheMock = vi.mocked(resetApiRequestCache);
const signOutMock = vi.mocked(signOut);
const startSignInMock = vi.mocked(startSignIn);

function AuthProbe(): JSX.Element {
  const auth = useAuth();

  return (
    <div>
      <p data-testid="auth-state">{auth.session.state}</p>
      <p data-testid="auth-email">{auth.session.user?.email ?? "anonymous"}</p>
      <button type="button" onClick={() => void auth.startSignIn("person@example.com", "/compare")}>
        start sign in
      </button>
      <button type="button" onClick={() => void auth.reloadSession()}>
        reload session
      </button>
      <button type="button" onClick={() => void auth.signOut()}>
        sign out
      </button>
    </div>
  );
}

function renderAuth(children: ReactNode): ReturnType<typeof render> {
  return render(<AuthProvider>{children}</AuthProvider>);
}

describe("AuthProvider", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    __resetApiRequestCacheForTests();
    resetApiRequestCacheMock.mockReset();
    getSessionMock.mockResolvedValue({
      state: "anonymous",
      user: null,
      expires_at: null,
      anonymous_reason: "missing",
      account_access_state: "anonymous",
      capability_keys: [],
      access_epoch: "anonymous:none",
    });
    signOutMock.mockResolvedValue({
      state: "anonymous",
      user: null,
      expires_at: null,
      anonymous_reason: "signed_out",
      account_access_state: "anonymous",
      capability_keys: [],
      access_epoch: "anonymous:none",
    });
    startSignInMock.mockResolvedValue({
      redirect_url: "/api/v1/auth/callback?state=state-1&ticket=valid-ticket",
    });
    vi.stubGlobal("location", {
      ...window.location,
      assign: vi.fn(),
    });
  });

  it("loads current session on mount", async () => {
    getSessionMock.mockResolvedValueOnce({
      state: "authenticated",
      user: {
        id: "a32d5bf0-0ec5-4dc9-bd40-636264a6fb96",
        email: "person@example.com",
      },
      expires_at: "2026-03-21T10:00:00Z",
      anonymous_reason: null,
      account_access_state: "premium",
      capability_keys: ["premium_comparison"],
      access_epoch: "premium:premium_comparison",
    });

    renderAuth(<AuthProbe />);

    await waitFor(() => {
      expect(screen.getByTestId("auth-state")).toHaveTextContent("authenticated");
    });
    expect(screen.getByTestId("auth-email")).toHaveTextContent("person@example.com");
  });

  it("clears cached API responses when the boot session changes", async () => {
    getSessionMock.mockResolvedValueOnce({
      state: "authenticated",
      user: {
        id: "a32d5bf0-0ec5-4dc9-bd40-636264a6fb96",
        email: "person@example.com",
      },
      expires_at: "2026-03-21T10:00:00Z",
      anonymous_reason: null,
      account_access_state: "free",
      capability_keys: [],
      access_epoch: "free:none",
    });

    renderAuth(<AuthProbe />);

    await waitFor(() => {
      expect(screen.getByTestId("auth-state")).toHaveTextContent("authenticated");
    });
    expect(resetApiRequestCacheMock).toHaveBeenCalledTimes(1);
  });

  it("starts sign in through the backend route and redirects the browser", async () => {
    const user = userEvent.setup();
    renderAuth(<AuthProbe />);

    await user.click(screen.getByRole("button", { name: "start sign in" }));

    await waitFor(() => {
      expect(startSignInMock).toHaveBeenCalledWith({
        email: "person@example.com",
        returnTo: "/compare",
      });
    });
    expect(window.location.assign).toHaveBeenCalledWith(
      "/api/v1/auth/callback?state=state-1&ticket=valid-ticket"
    );
    expect(resetApiRequestCacheMock).toHaveBeenCalledTimes(1);
  });

  it("signs out and replaces session state", async () => {
    const user = userEvent.setup();
    getSessionMock.mockResolvedValueOnce({
      state: "authenticated",
      user: {
        id: "a32d5bf0-0ec5-4dc9-bd40-636264a6fb96",
        email: "person@example.com",
      },
      expires_at: "2026-03-21T10:00:00Z",
      anonymous_reason: null,
      account_access_state: "free",
      capability_keys: [],
      access_epoch: "free:none",
    });

    renderAuth(<AuthProbe />);
    await screen.findByText("person@example.com");

    await user.click(screen.getByRole("button", { name: "sign out" }));

    await waitFor(() => {
      expect(signOutMock).toHaveBeenCalledTimes(1);
      expect(screen.getByTestId("auth-state")).toHaveTextContent("anonymous");
    });
    expect(screen.getByTestId("auth-email")).toHaveTextContent("anonymous");
    expect(resetApiRequestCacheMock).toHaveBeenCalledTimes(2);
  });

  it("reloads session and clears cached API responses", async () => {
    const user = userEvent.setup();
    getSessionMock
      .mockResolvedValueOnce({
        state: "anonymous",
        user: null,
        expires_at: null,
        anonymous_reason: "missing",
        account_access_state: "anonymous",
        capability_keys: [],
        access_epoch: "anonymous:none",
      })
      .mockResolvedValueOnce({
        state: "authenticated",
        user: {
          id: "a32d5bf0-0ec5-4dc9-bd40-636264a6fb96",
          email: "person@example.com",
        },
        expires_at: "2026-03-21T10:00:00Z",
        anonymous_reason: null,
        account_access_state: "premium",
        capability_keys: ["premium_ai_analyst"],
        access_epoch: "premium:premium_ai_analyst",
      });

    renderAuth(<AuthProbe />);
    await waitFor(() => {
      expect(screen.getByTestId("auth-state")).toHaveTextContent("anonymous");
    });

    await user.click(screen.getByRole("button", { name: "reload session" }));

    await waitFor(() => {
      expect(screen.getByTestId("auth-state")).toHaveTextContent("authenticated");
    });
    expect(screen.getByTestId("auth-email")).toHaveTextContent("person@example.com");
    expect(resetApiRequestCacheMock).toHaveBeenCalledTimes(1);
  });

  it("clears cached responses when access epoch changes without an auth-state change", async () => {
    const user = userEvent.setup();
    getSessionMock
      .mockResolvedValueOnce({
        state: "authenticated",
        user: {
          id: "a32d5bf0-0ec5-4dc9-bd40-636264a6fb96",
          email: "person@example.com",
        },
        expires_at: "2026-03-21T10:00:00Z",
        anonymous_reason: null,
        account_access_state: "free",
        capability_keys: [],
        access_epoch: "free:none",
      })
      .mockResolvedValueOnce({
        state: "authenticated",
        user: {
          id: "a32d5bf0-0ec5-4dc9-bd40-636264a6fb96",
          email: "person@example.com",
        },
        expires_at: "2026-03-21T10:00:00Z",
        anonymous_reason: null,
        account_access_state: "premium",
        capability_keys: ["premium_comparison"],
        access_epoch: "premium:premium_comparison",
      });

    renderAuth(<AuthProbe />);
    await screen.findByText("person@example.com");

    await user.click(screen.getByRole("button", { name: "reload session" }));

    await waitFor(() => {
      expect(resetApiRequestCacheMock).toHaveBeenCalledTimes(2);
    });
  });
});
