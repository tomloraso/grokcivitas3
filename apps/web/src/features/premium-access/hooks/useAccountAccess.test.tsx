import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  __resetApiRequestCacheForTests,
  getAccountAccess,
  getSession,
  resetApiRequestCache,
  signOut,
  startSignIn,
} from "../../../api/client";
import { AuthProvider } from "../../auth/AuthProvider";
import { useAuth } from "../../auth/useAuth";
import { useAccountAccess } from "./useAccountAccess";

vi.mock("../../../api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../../../api/client")>();
  return {
    ...actual,
    getAccountAccess: vi.fn(),
    getSession: vi.fn(),
    resetApiRequestCache: vi.fn(),
    signOut: vi.fn(),
    startSignIn: vi.fn(),
  };
});

const getAccountAccessMock = vi.mocked(getAccountAccess);
const getSessionMock = vi.mocked(getSession);
const resetApiRequestCacheMock = vi.mocked(resetApiRequestCache);
const signOutMock = vi.mocked(signOut);
const startSignInMock = vi.mocked(startSignIn);

function renderAuth(children: ReactNode): ReturnType<typeof render> {
  return render(<AuthProvider>{children}</AuthProvider>);
}

function AccessProbe(): JSX.Element {
  const auth = useAuth();
  const accountAccess = useAccountAccess();

  return (
    <div>
      <p data-testid="session-email">{auth.session.user?.email ?? "anonymous"}</p>
      <p data-testid="access-state">{accountAccess.status}</p>
      <p data-testid="entitlement-id">
        {accountAccess.access?.entitlements[0]?.id ?? "none"}
      </p>
      <button type="button" onClick={() => void auth.reloadSession()}>
        reload session
      </button>
    </div>
  );
}

describe("useAccountAccess", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    __resetApiRequestCacheForTests();
    resetApiRequestCacheMock.mockReset();
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
  });

  it("reloads account access when the authenticated user changes but the access epoch stays the same", async () => {
    const user = userEvent.setup();

    getSessionMock
      .mockResolvedValueOnce({
        state: "authenticated",
        user: {
          id: "11111111-1111-1111-1111-111111111111",
          email: "first@example.com",
        },
        expires_at: "2026-03-21T10:00:00Z",
        anonymous_reason: null,
        account_access_state: "premium",
        capability_keys: ["premium_comparison"],
        access_epoch: "premium:premium_comparison",
      })
      .mockResolvedValueOnce({
        state: "authenticated",
        user: {
          id: "22222222-2222-2222-2222-222222222222",
          email: "second@example.com",
        },
        expires_at: "2026-03-21T11:00:00Z",
        anonymous_reason: null,
        account_access_state: "premium",
        capability_keys: ["premium_comparison"],
        access_epoch: "premium:premium_comparison",
      });

    getAccountAccessMock
      .mockResolvedValueOnce({
        account_access_state: "premium",
        capability_keys: ["premium_comparison"],
        access_epoch: "premium:premium_comparison",
        entitlements: [
          {
            id: "entitlement-first",
            product_code: "premium_launch",
            product_display_name: "Premium",
            capability_keys: ["premium_comparison"],
            status: "active",
            starts_at: "2026-03-09T08:00:00Z",
            ends_at: null,
            revoked_at: null,
            revoked_reason_code: null,
          },
        ],
      })
      .mockResolvedValueOnce({
        account_access_state: "premium",
        capability_keys: ["premium_comparison"],
        access_epoch: "premium:premium_comparison",
        entitlements: [
          {
            id: "entitlement-second",
            product_code: "premium_launch",
            product_display_name: "Premium",
            capability_keys: ["premium_comparison"],
            status: "active",
            starts_at: "2026-03-10T08:00:00Z",
            ends_at: null,
            revoked_at: null,
            revoked_reason_code: null,
          },
        ],
      });

    renderAuth(<AccessProbe />);

    await waitFor(() => {
      expect(screen.getByTestId("session-email")).toHaveTextContent(
        "first@example.com"
      );
    });
    await waitFor(() => {
      expect(screen.getByTestId("entitlement-id")).toHaveTextContent(
        "entitlement-first"
      );
    });

    await user.click(screen.getByRole("button", { name: "reload session" }));

    await waitFor(() => {
      expect(screen.getByTestId("session-email")).toHaveTextContent(
        "second@example.com"
      );
    });
    await waitFor(() => {
      expect(screen.getByTestId("entitlement-id")).toHaveTextContent(
        "entitlement-second"
      );
    });
    expect(getAccountAccessMock).toHaveBeenCalledTimes(2);
  });
});
