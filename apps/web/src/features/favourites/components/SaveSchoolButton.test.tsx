import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  removeAccountFavourite,
  resetApiRequestCache,
  saveAccountFavourite
} from "../../../api/client";
import { ToastProvider } from "../../../components/ui/Toast";
import { SaveSchoolButton } from "./SaveSchoolButton";
import type { SavedSchoolStateVM } from "../types";

vi.mock("../../../api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../../../api/client")>();
  return {
    ...actual,
    saveAccountFavourite: vi.fn(),
    removeAccountFavourite: vi.fn(),
    resetApiRequestCache: vi.fn()
  };
});

const saveAccountFavouriteMock = vi.mocked(saveAccountFavourite);
const removeAccountFavouriteMock = vi.mocked(removeAccountFavourite);
const resetApiRequestCacheMock = vi.mocked(resetApiRequestCache);

function renderButton({
  savedState,
  onSavedStateChange = vi.fn()
}: {
  savedState: SavedSchoolStateVM;
  onSavedStateChange?: (savedState: SavedSchoolStateVM) => void;
}) {
  const router = createMemoryRouter(
    [
      {
        path: "/schools/100001",
        element: (
          <ToastProvider>
            <SaveSchoolButton
              schoolUrn="100001"
              savedState={savedState}
              onSavedStateChange={onSavedStateChange}
            />
          </ToastProvider>
        )
      },
      {
        path: "/sign-in",
        element: <p>Sign in page</p>
      }
    ],
    {
      initialEntries: ["/schools/100001?view=results"]
    }
  );

  return {
    onSavedStateChange,
    router,
    ...render(<RouterProvider router={router} />)
  };
}

describe("SaveSchoolButton", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("routes anonymous users into sign-in with returnTo preserved", async () => {
    const user = userEvent.setup();

    renderButton({
      savedState: {
        status: "requires_auth",
        savedAt: null,
        capabilityKey: null,
        reasonCode: "anonymous_user"
      }
    });

    await user.click(screen.getByRole("button", { name: "Sign in to save" }));

    await waitFor(() => {
      expect(screen.getByText("Sign in page")).toBeInTheDocument();
    });
  });

  it("saves a school and reports the updated saved state", async () => {
    const user = userEvent.setup();
    const onSavedStateChange = vi.fn();
    saveAccountFavouriteMock.mockResolvedValue({
      status: "saved",
      saved_at: "2026-03-10T10:15:00Z",
      capability_key: null,
      reason_code: null
    });

    renderButton({
      savedState: {
        status: "not_saved",
        savedAt: null,
        capabilityKey: null,
        reasonCode: null
      },
      onSavedStateChange
    });

    await user.click(screen.getByRole("button", { name: "Save for later" }));

    await waitFor(() => {
      expect(saveAccountFavouriteMock).toHaveBeenCalledWith("100001");
    });
    expect(resetApiRequestCacheMock).toHaveBeenCalledTimes(1);
    expect(onSavedStateChange).toHaveBeenCalledWith({
      status: "saved",
      savedAt: "2026-03-10T10:15:00Z",
      capabilityKey: null,
      reasonCode: null
    });
  });

  it("removes a saved school and reports the cleared saved state", async () => {
    const user = userEvent.setup();
    const onSavedStateChange = vi.fn();
    removeAccountFavouriteMock.mockResolvedValue({
      status: "not_saved",
      saved_at: null,
      capability_key: null,
      reason_code: null
    });

    renderButton({
      savedState: {
        status: "saved",
        savedAt: "2026-03-10T10:15:00Z",
        capabilityKey: null,
        reasonCode: null
      },
      onSavedStateChange
    });

    await user.click(screen.getByRole("button", { name: "Saved" }));

    await waitFor(() => {
      expect(removeAccountFavouriteMock).toHaveBeenCalledWith("100001");
    });
    expect(resetApiRequestCacheMock).toHaveBeenCalledTimes(1);
    expect(onSavedStateChange).toHaveBeenCalledWith({
      status: "not_saved",
      savedAt: null,
      capabilityKey: null,
      reasonCode: null
    });
  });
});
