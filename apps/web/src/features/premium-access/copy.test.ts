import { describe, expect, it } from "vitest";

import {
  getCapabilityDisplayLabel,
  getPremiumPaywallCopy,
} from "./copy";

describe("premium-access copy helpers", () => {
  it("maps internal capability keys to user-facing labels", () => {
    expect(getCapabilityDisplayLabel("premium_ai_analyst")).toBe(
      "AI analyst view"
    );
    expect(getCapabilityDisplayLabel("premium_comparison")).toBe(
      "School comparison"
    );
    expect(getCapabilityDisplayLabel("premium_neighbourhood")).toBe(
      "Neighbourhood context"
    );
    expect(getCapabilityDisplayLabel("custom_capability")).toBe(
      "custom_capability"
    );
  });

  it("keeps compare paywall copy action-oriented", () => {
    expect(
      getPremiumPaywallCopy({
        capabilityKey: "premium_comparison",
        schoolName: null,
        requiresAuth: false,
      })
    ).toMatchObject({
      title: "Compare schools side by side with Premium",
      buttonLabel: "View Premium plans",
    });
  });
});
