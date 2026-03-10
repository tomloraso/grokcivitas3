import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  getAccountFavourites,
  removeAccountFavourite,
  resetApiRequestCache
} from "../../api/client";
import { ToastProvider } from "../../components/ui/Toast";
import { AuthProvider } from "../auth/AuthProvider";
import type { AuthSession } from "../auth/types";
import { FavouritesLibraryFeature } from "./FavouritesLibraryFeature";

vi.mock("../../api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../../api/client")>();
  return {
    ...actual,
    getAccountFavourites: vi.fn(),
    removeAccountFavourite: vi.fn(),
    resetApiRequestCache: vi.fn()
  };
});

const getAccountFavouritesMock = vi.mocked(getAccountFavourites);
const removeAccountFavouriteMock = vi.mocked(removeAccountFavourite);
const resetApiRequestCacheMock = vi.mocked(resetApiRequestCache);

const AUTHENTICATED_SESSION: AuthSession = {
  state: "authenticated",
  user: {
    id: "11111111-1111-1111-1111-111111111111",
    email: "saved@example.com"
  },
  expiresAt: "2026-03-21T10:00:00Z",
  anonymousReason: null,
  accountAccessState: "free",
  capabilityKeys: [],
  accessEpoch: "free:none"
};

function renderFeature() {
  const router = createMemoryRouter(
    [
      {
        path: "/account/favourites",
        element: <FavouritesLibraryFeature />
      }
    ],
    {
      initialEntries: ["/account/favourites"]
    }
  );

  return render(
    <AuthProvider autoLoad={false} initialSession={AUTHENTICATED_SESSION}>
      <ToastProvider>
        <RouterProvider router={router} />
      </ToastProvider>
    </AuthProvider>
  );
}

describe("FavouritesLibraryFeature", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    getAccountFavouritesMock.mockResolvedValue({
      access: {
        state: "available",
        capability_key: null,
        reason_code: "free_baseline",
        product_codes: [],
        requires_auth: false,
        requires_purchase: false,
        school_name: null
      },
      count: 1,
      schools: [
        {
          urn: "100001",
          name: "Camden Bridge Primary School",
          type: "Community school",
          phase: "Primary",
          postcode: "NW1 8NH",
          pupil_count: 420,
          latest_ofsted: {
            label: "Good",
            sort_rank: 2,
            availability: "published"
          },
          academic_metric: {
            metric_key: "ks2_combined_expected_pct",
            label: "KS2 expected standard",
            display_value: "67%",
            sort_value: 67,
            availability: "published"
          },
          saved_at: "2026-03-10T09:15:00Z"
        }
      ]
    });
    removeAccountFavouriteMock.mockResolvedValue({
      status: "not_saved",
      saved_at: null,
      capability_key: null,
      reason_code: null
    });
  });

  it("loads saved schools and removes a school from the library after unsave", async () => {
    const user = userEvent.setup();
    renderFeature();

    expect(
      await screen.findByRole("heading", { name: "Saved schools" })
    ).toBeInTheDocument();
    expect(screen.getByText("Camden Bridge Primary School")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Saved" }));

    await waitFor(() => {
      expect(removeAccountFavouriteMock).toHaveBeenCalledWith("100001");
    });
    expect(resetApiRequestCacheMock).toHaveBeenCalledTimes(1);

    await waitFor(() => {
      expect(screen.queryByText("Camden Bridge Primary School")).not.toBeInTheDocument();
    });
  });
});
